import json
import base64
import requests
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from .models import MpesaTransaction


def _get_access_token():
    url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    if settings.MPESA_ENV == 'production':
        url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    resp = requests.get(url, auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET), timeout=15)
    resp.raise_for_status()
    return resp.json()['access_token']


def _format_phone(phone):
    phone = phone.strip().replace(' ', '').replace('-', '').replace('+', '')
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    if not phone.startswith('254'):
        phone = '254' + phone
    return phone


def stk_push(payment, phone):
    phone = _format_phone(phone)
    token = _get_access_token()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_str = settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + timestamp
    password = base64.b64encode(data_str.encode()).decode()

    url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    if settings.MPESA_ENV == 'production':
        url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

    ref = f'PN-{payment.id}'
    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(payment.amount),
        'PartyA': phone,
        'PartyB': settings.MPESA_SHORTCODE,
        'PhoneNumber': phone,
        'CallBackURL': settings.MPESA_CALLBACK_URL,
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

    return True, receipt
