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
    cert_pem = """-----BEGIN CERTIFICATE-----
MIIGgDCCBWigAwIBAgIKMvrulAAAAARG5DANBgkqhkiG9w0BAQsFADBbMRMwEQYK
CZImiZPyLGQBGRYDbmV0MRkwFwYKCZImiZPyLGQBGRYJc2FmYXJpY29tMSkwJwYD
VQQDEyBTYWZhcmljb20gSW50ZXJuYWwgSXNzdWluZyBDQSAwMjAeFw0xNDExMTIw
NzEyNDVaFw0xNjExMTEwNzEyNDVaMHsxCzAJBgNVBAYTAktFMRAwDgYDVQQIEwdO
YWlyb2JpMRAwDgYDVQQHEwdOYWlyb2JpMRAwDgYDVQQKEwdOYWlyb2JpMRMwEQYD
VQQLEwpUZWNobm9sb2d5MSEwHwYDVQQDExhhcGljcnlwdC5zYWZhcmljb20uY28u
a2UwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCotwV1VxXsd0Q6i2w0
ugw+EPvgJfV6PNyB826Ik3L2lPJLFuzNEEJbGaiTdSe6Xitf/PJUP/q8Nv2dupHL
BkiBHjpQ6f61He8Zdc9fqKDGBLoNhNpBXxbznzI4Yu6hjBGLnF5Al9zMAxTij6wL
GUFswKpizifNbzV+LyIXY4RR2t8lxtqaFKeSx2B8P+eiZbL0wRIDPVC5+s4GdpFf
Y3QIqyLxI2bOyCGl8/XlUuIhVXxhc8Uq132xjfsWljbw4oaMobnB2KN79vMUvyoR
w8OGpga5VoaSFfVuQjSIf5RwW1hitm/8XJvmNEdeY0uKriYwbR8wfwQ3E0AIW1Fl
MMghAgMBAAGjggMkMIIDIDAdBgNVHQ4EFgQUwUfE+NgGndWDN3DyVp+CAiF1Zkgw
HwYDVR0jBBgwFoAU6zLUT35gmjqYIGO6DV6+6HlO1SQwggE7BgNVHR8EggEyMIIB
LjCCASqgggEmoIIBIoaB1mxkYXA6Ly8vQ049U2FmYXJpY29tJTIwSW50ZXJuYWwl
MjBJc3N1aW5nJTIwQ0ElMjAwMixDTj1hcnVzLENOPUNQLENOPVB1YmxpYyUyMEtl
eSUyMFNlcnZpY2VzLENOPVNlcnZpY2VzLENOPUNvbmZpZ3VyYXRpb24sREM9c2Fm
YXJpY29tLERDPW5ldD9jZXJ0aWZpY2F0ZVJldm9jYXRpb25MaXN0P2Jhc2U/b2Jq
ZWN0Q2xhc3M9Y1JMRGlzdHJpYnV0aW9uUG9pbnSGNWh0dHA6Ly9hcnVzLnNhZmFy
aWNvbS5uZXQvQ2VydEVucm9sbC9TYWZhcmljb21Jc3N1aW5nMDEuY3JshjRodHRw
Oi8vYXJ1cy5zYWZhcmljb20ubmV0L0NlcnRFbnJvbGwvU2FmYXJpY29tSXNzdWlu
ZzAyLmNybDCCAcQGA1UdEgSCAbswggG3oAsGCSsGAQQBgjc9AaEGBW6hAwIBgakC
AwYBA6QaBAQ0MDAwMDCkOQQ3NjI1MDCkOQQ3OTkxM6kJBgNghv8AAQABoIHCBgMq
CQAAMYIBMjCCAS4CAQEwUTBbMRMwEQYKCZImiZPyLGQBGRYDbmV0MRkwFwYKCZIm
iZPyLGQBGRYJc2FmYXJpY29tMSkwJwYDVQQDEyBTYWZhcmljb20gSW50ZXJuYWwg
SXNzdWluZyBDQSAwMgIKMvrulAAAAARG5DANBgkqhkiG9w0BAQsFAASCAQAU0qM7
A8S5MgjFWwqJJsCBB2tqGGbFrV4WBSV6WltPqP9+ZSl7OqY5DwLTw3CQRT2s7zwh
K6AXFG6qY4G0Emk42Y8R64FH+X0r5FoKUj6FVJY3zNdfksSXyN7LmGufLGl/jNtC
WF6YVXyq7BKHz5znwCqVMQAFqW5x7MrgR6G3rHRqUk8dC/O7vXsKkq1v0ASn2fpp
PvHk5eWzNHzbSlub6nQ9B3vOZhLWzQHf5w0K5a8YT7eQ6E5/FGxBB7+4yMz/pG5I
N4xPBqXQIXYbxA5WsQ7wFPPgF2R2AR9q5ICNqK4uT5aGMjSlQ+qDPYsZx8GFe7pH
jENn6UZxiN5gx7sYqJ0k
-----END CERTIFICATE-----"""
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
