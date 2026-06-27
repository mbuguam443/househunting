import json
import requests
from django.conf import settings
from .mpesa_utils import _get_access_token, _is_production

def _get_c2b_confirmation_url(landlord=None):
    if landlord and hasattr(landlord, 'profile') and landlord.profile.c2b_confirmation_url:
        return landlord.profile.c2b_confirmation_url
    from accounts.models import PlatformConfig
    cfg = PlatformConfig.objects.filter(pk=1).first()
    if cfg and cfg.c2b_confirmation_url:
        return cfg.c2b_confirmation_url
    base = getattr(settings, 'MPESA_CALLBACK_URL', '')
    if base:
        base = base.replace('/mpesa/callback/', '/').replace('/callback/', '/')
        return base.rstrip('/') + '/c2b/confirmation/'
    return 'https://patanyumba.co.ke/c2b/confirmation/'

def _get_c2b_validation_url(landlord=None):
    if landlord and hasattr(landlord, 'profile') and landlord.profile.c2b_validation_url:
        return landlord.profile.c2b_validation_url
    from accounts.models import PlatformConfig
    cfg = PlatformConfig.objects.filter(pk=1).first()
    if cfg and cfg.c2b_validation_url:
        return cfg.c2b_validation_url
    base = getattr(settings, 'MPESA_CALLBACK_URL', '')
    if base:
        base = base.replace('/mpesa/callback/', '/').replace('/callback/', '/')
        return base.rstrip('/') + '/c2b/validation/'
    return 'https://patanyumba.co.ke/c2b/validation/'

def register_c2b_urls(landlord=None):
    import logging
    logger = logging.getLogger(__name__)
    try:
        token = _get_access_token(landlord)
    except Exception as e:
        logger.error(f'Failed to get access token for landlord {landlord}: {e}')
        return {'error': f'Failed to get access token: {e}'}
    shortcode = None
    if landlord and hasattr(landlord, 'profile'):
        if landlord.profile.c2b_shortcode:
            shortcode = landlord.profile.c2b_shortcode
        elif landlord.profile.mpesa_shortcode:
            shortcode = landlord.profile.mpesa_shortcode
    if not shortcode:
        shortcode = getattr(settings, 'MPESA_SHORTCODE', '174379')

    url = 'https://sandbox.safaricom.co.ke/mpesa/c2b/v2/registerurl'
    if _is_production():
        url = 'https://api.safaricom.co.ke/mpesa/c2b/v2/registerurl'

    payload = {
        'ShortCode': shortcode,
        'ConfirmationURL': _get_c2b_confirmation_url(landlord),
        'ValidationURL': _get_c2b_validation_url(landlord),
        'ResponseType': 'Completed',
    }

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    logger.info(f'Registering C2B for shortcode {shortcode}, URLs: conf={payload["ConfirmationURL"]}, val={payload["ValidationURL"]}')
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        data = resp.json()
    except Exception as e:
        logger.error(f'C2B register request failed: {e}')
        return {'error': f'Request failed: {e}'}

    logger.info(f'C2B register response: {data}')
    success = (resp.status_code == 200 and data.get('ResponseCode') == '0') or \
              ('Duplicate notification info' in data.get('errorMessage', ''))
    if success and landlord and hasattr(landlord, 'profile'):
        landlord.profile.c2b_registered = True
        landlord.profile.save(update_fields=['c2b_registered'])

    if 'Duplicate notification info' in data.get('errorMessage', ''):
        return {'ResponseCode': '0', 'ResponseDescription': 'Already registered'}

    return data


def process_c2b_confirmation(data):
    """
    Handle a C2B payment notification from Safaricom.
    data keys: TransactionType, TransID, TransTime, TransAmount,
               BusinessShortCode, BillRefNumber, InvoiceNumber,
               OrgAccountBalance, ThirdPartyTransID, MSISDN,
               FirstName, MiddleName, LastName
    """
    trans_id = data.get('TransID', '')
    amount = data.get('TransAmount', '0')
    phone = data.get('MSISDN', '')
    bill_ref = data.get('BillRefNumber', '').strip()
    first_name = data.get('FirstName', '')
    last_name = data.get('LastName', '')

    from .models import C2BTransaction
    C2BTransaction.objects.create(
        trans_id=trans_id,
        amount=amount,
        phone=phone,
        bill_ref=bill_ref,
        first_name=first_name,
        last_name=last_name,
        raw_data=data,
    )

    return {'ResultCode': 0, 'ResultDesc': 'Accepted'}


def process_c2b_validation(data):
    """Validate a C2B transaction. Accept all for now."""
    return {'ResultCode': 0, 'ResultDesc': 'Success'}
