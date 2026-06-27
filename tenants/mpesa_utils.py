import json
import base64
import requests
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from .models import MpesaTransaction, RentPayment


def _get_callback_url(landlord=None):
    """Check landlord profile first, then PlatformConfig, then settings."""
    if landlord and hasattr(landlord, 'profile') and landlord.profile.mpesa_callback_url:
        base = landlord.profile.mpesa_callback_url.rstrip('/')
        if not base.endswith('/mpesa/callback'):
            return base + '/mpesa/callback/'
        return base + '/'
    from accounts.models import PlatformConfig
    cfg = PlatformConfig.objects.filter(pk=1).first()
    if cfg and cfg.callback_url:
        base = cfg.callback_url.rstrip('/')
        if not base.endswith('/mpesa/callback'):
            return base + '/mpesa/callback/'
        return base + '/'
    return settings.MPESA_CALLBACK_URL


def _get_config(key, settings_attr, landlord=None):
    """Check landlord profile first, then fall back to settings."""
    if landlord and hasattr(landlord, 'profile'):
        val = getattr(landlord.profile, key, '')
        if val:
            return val
    return getattr(settings, settings_attr, '')


def _is_production():
    return settings.MPESA_ENV == 'production'

def _get_access_token(landlord=None):
    url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    if _is_production():
        url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    key = _get_config('mpesa_consumer_key', 'MPESA_CONSUMER_KEY', landlord)
    secret = _get_config('mpesa_consumer_secret', 'MPESA_CONSUMER_SECRET', landlord)
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


def stk_push(payment, phone, landlord=None):
    phone = _format_phone(phone)
    token = _get_access_token(landlord)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    shortcode = _get_config('mpesa_shortcode', 'MPESA_SHORTCODE', landlord)
    passkey = _get_config('mpesa_passkey', 'MPESA_PASSKEY', landlord)
    data_str = shortcode + passkey + timestamp
    password = base64.b64encode(data_str.encode()).decode()

    url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    if _is_production():
        url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

    ref = f'PN-{payment.id}'
    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(payment.amount),
        'PartyA': phone,
        'PartyB': shortcode,
        'PhoneNumber': phone,
        'CallBackURL': _get_callback_url(landlord),
        'AccountReference': ref,
        'TransactionDesc': f'Rent payment ref {ref}',
    }

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    resp = requests.post(url, json=payload, headers=headers, timeout=20)
    data = resp.json()

    tx = MpesaTransaction.objects.create(
        payment=payment, phone=phone, amount=payment.amount,
        merchant_request_id=data.get('MerchantRequestID', ''),
        checkout_request_id=data.get('CheckoutRequestID', ''),
        response_code=data.get('ResponseCode', ''),
        response_description=data.get('ResponseDescription', ''),
        status='pending',
    )

    if data.get('ResponseCode') != '0':
        tx.status = 'failed'
        tx.save()
        return tx, data.get('ResponseDescription', 'STK push failed')

    return tx, None


def process_callback(data):
    callback = data.get('Body', {}).get('stkCallback', {})
    checkout_id = callback.get('CheckoutRequestID', '')
    result_code = callback.get('ResultCode', 1)
    result_desc = callback.get('ResultDesc', '')

    try:
        tx = MpesaTransaction.objects.get(checkout_request_id=checkout_id)
    except MpesaTransaction.DoesNotExist:
        return False, 'Transaction not found'

    tx.result_code = str(result_code)
    tx.result_desc = result_desc
    tx.raw_callback = data

    if result_code != 0:
        tx.status = 'failed'
        tx.save()
        return False, result_desc

    metadata = callback.get('CallbackMetadata', {}).get('Item', [])
    receipt = ''
    txn_date = None
    for item in metadata:
        name = item.get('Name', '')
        if name == 'MpesaReceiptNumber':
            receipt = item.get('Value', '')
        elif name == 'TransactionDate':
            val = str(item.get('Value', ''))
            if len(val) >= 14:
                txn_date = datetime.strptime(val, '%Y%m%d%H%M%S')
                txn_date = timezone.make_aware(txn_date)

    tx.receipt = receipt
    tx.transaction_date = txn_date
    tx.status = 'completed'
    tx.save()

    pmt = tx.payment
    pmt.status = 'paid'
    pmt.paid_date = timezone.now().date()
    pmt.reference = receipt
    pmt.save()

    paid_amount = pmt.amount
    tenancy = pmt.tenancy

    invoices = RentPayment.objects.filter(tenancy=tenancy).exclude(status='paid').order_by('due_date', 'id')
    remaining = paid_amount
    for inv in invoices:
        if inv.id == pmt.id:
            continue
        if remaining <= 0:
            break
        if inv.amount <= remaining:
            inv.status = 'paid'
            inv.paid_date = timezone.now().date()
            inv.reference = receipt
            inv.save()
            remaining -= inv.amount
        else:
            inv.amount -= remaining
            inv.save()
            remaining = Decimal('0')

    return True, receipt


def query_stk_status(checkout_request_id):
    token = _get_access_token()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    shortcode = _get_config('mpesa_shortcode', 'MPESA_SHORTCODE')
    passkey = _get_config('mpesa_passkey', 'MPESA_PASSKEY')
    data_str = shortcode + passkey + timestamp
    password = base64.b64encode(data_str.encode()).decode()

    url = 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query'
    if _is_production():
        url = 'https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query'

    payload = {
        'BusinessShortCode': shortcode,
        'Password': password,
        'Timestamp': timestamp,
        'CheckoutRequestID': checkout_request_id,
    }

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    resp = requests.post(url, json=payload, headers=headers, timeout=20)
    return resp.json()
