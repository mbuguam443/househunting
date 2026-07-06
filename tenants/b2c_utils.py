import base64
import os
from urllib.parse import urlparse
import requests
from django.conf import settings
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from .models import B2CTransaction


_SANDBOX_CERT_PATH = os.path.join(os.path.dirname(__file__), 'sandbox_cert.cer')


def _is_production():
    return settings.MPESA_ENV == 'production'


def _get_access_token(landlord=None):
    url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    if _is_production():
        url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    key = landlord.profile.mpesa_consumer_key if (landlord and landlord.profile.mpesa_consumer_key) else getattr(settings, 'MPESA_CONSUMER_KEY', '')
    secret = landlord.profile.mpesa_consumer_secret if (landlord and landlord.profile.mpesa_consumer_secret) else getattr(settings, 'MPESA_CONSUMER_SECRET', '')
    resp = requests.get(url, auth=(key, secret), timeout=15)
    resp.raise_for_status()
    return resp.json()['access_token']


def _format_phone(phone):
    phone = phone.strip().replace(' ', '').replace('-', '').replace('+', '')
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    if not phone.startswith('254'):
        phone = '254' + phone
    return phone


def _get_security_credential(initiator_name, initiator_pw, token=None):
    """Generate SecurityCredential by RSA-encrypting initiator password with Safaricom public key."""
    try:
        return _fetch_and_encrypt(initiator_name, initiator_pw, token)
    except Exception as e:
        if not _is_production():
            return _encrypt_with_bundled_cert(initiator_pw)
        raise ValueError(f'Failed to generate security credential: {e}')


def _fetch_and_encrypt(initiator_name, initiator_pw, token=None):
    """Fetch public key from Safaricom API and encrypt password."""
    url = 'https://sandbox.safaricom.co.ke/mpesa/b2c/v1/b2c-publickey'
    if _is_production():
        url = 'https://api.safaricom.co.ke/mpesa/b2c/v1/b2c-publickey'

    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    resp = requests.post(url, params={'publicKey': initiator_name}, headers=headers, timeout=15)
    if resp.status_code != 200:
        raise ValueError(f'Public key endpoint returned HTTP {resp.status_code}')
    data = resp.json()

    cert_pem = data.get('publicKey') or data.get('certificate', '')
    if not cert_pem:
        if 'output_Certificate' in data:
            cert_pem = data['output_Certificate']
        else:
            raise ValueError(f'No public key in response: {data}')

    return _encrypt_with_pem(cert_pem, initiator_pw)


def _encrypt_with_bundled_cert(initiator_pw):
    """Use bundled sandbox certificate to encrypt the initiator password."""
    if not os.path.exists(_SANDBOX_CERT_PATH):
        raise ValueError('Sandbox certificate not found at ' + _SANDBOX_CERT_PATH)
    with open(_SANDBOX_CERT_PATH) as f:
        cert_pem = f.read()
    return _encrypt_with_pem(cert_pem, initiator_pw)


def _encrypt_with_pem(cert_pem, initiator_pw):
    """Encrypt initiator password using a PEM-encoded certificate or public key."""
    if 'CERTIFICATE' in cert_pem:
        cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
        public_key = cert.public_key()
    else:
        public_key = serialization.load_pem_public_key(cert_pem.encode(), default_backend())

    encrypted = public_key.encrypt(
        initiator_pw.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return base64.b64encode(encrypted).decode()


def initiate_b2c(landlord, amount, recipient_phone, recipient_name=''):
    """Initiate a B2C payment from landlord's paybill to recipient."""
    shortcode = landlord.profile.b2c_shortcode or landlord.profile.c2b_shortcode
    if not shortcode:
        raise ValueError('Landlord has no B2C or C2B shortcode configured.')
    initiator = landlord.profile.b2c_initiator_name
    initiator_pw = landlord.profile.b2c_initiator_password
    if not initiator or not initiator_pw:
        raise ValueError('B2C initiator credentials not configured.')

    token = _get_access_token(landlord)
    phone = _format_phone(recipient_phone)

    security_credential = _get_security_credential(initiator, initiator_pw, token)

    url = 'https://sandbox.safaricom.co.ke/mpesa/b2c/v1/paymentrequest'
    if _is_production():
        url = 'https://api.safaricom.co.ke/mpesa/b2c/v1/paymentrequest'

    payload = {
        'InitiatorName': initiator,
        'SecurityCredential': security_credential,
        'CommandID': 'BusinessPayment',
        'Amount': int(amount),
        'PartyA': shortcode,
        'PartyB': int(phone),
        'Remarks': f'Commission payment from {landlord.username}',
        'QueueTimeOutURL': _get_timeout_url(landlord),
        'ResultURL': _get_result_url(landlord),
        'Occasion': 'PataNyumba Commission',
    }

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    tx = B2CTransaction.objects.create(
        landlord=landlord,
        amount=amount,
        recipient_phone=phone,
        recipient_name=recipient_name,
        status='pending',
    )

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        data = resp.json()
        tx.raw_response = data
        tx.response_description = data.get('ResponseDescription', '')
        tx.conversation_id = data.get('ConversationID', '')
        tx.originator_conversation_id = data.get('OriginatorConversationID', '')
        tx.transaction_id = data.get('TransactionID', '')

        if data.get('ResponseCode') == '0':
            tx.status = 'completed'
            tx.save()
            return tx, None
        else:
            tx.status = 'failed'
            tx.save()
            return tx, data.get('ResponseDescription', 'B2C request failed')
    except requests.RequestException as e:
        tx.status = 'failed'
        tx.response_description = str(e)
        tx.save()
        return tx, str(e)
    except Exception as e:
        tx.status = 'failed'
        tx.response_description = str(e)
        tx.save()
        return tx, str(e)


def _get_timeout_url(landlord=None):
    base = _get_callback_base(landlord)
    return base + '/dashboard/tenants/b2c/timeout/'


def _get_result_url(landlord=None):
    base = _get_callback_base(landlord)
    return base + '/dashboard/tenants/b2c/result/'


def _get_callback_base(landlord=None):
    if landlord and landlord.profile.b2c_callback_base_url:
        return landlord.profile.b2c_callback_base_url.rstrip('/')
    from accounts.models import PlatformConfig
    cfg = PlatformConfig.objects.filter(pk=1).first()
    if cfg and cfg.c2b_confirmation_url:
        base = cfg.c2b_confirmation_url.rstrip('/')
        parsed = urlparse(base)
        return f'{parsed.scheme}://{parsed.netloc}'
    if getattr(settings, 'MPESA_CALLBACK_URL', ''):
        base = getattr(settings, 'MPESA_CALLBACK_URL', '').rstrip('/')
        parsed = urlparse(base)
        return f'{parsed.scheme}://{parsed.netloc}'
    return ''
