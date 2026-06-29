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

    BillRefNumber is expected to be the unit/house number.
    On success, looks up the active tenancy for that unit and
    reduces the outstanding rent balance.
    """
    import logging
    from decimal import Decimal
    from django.utils import timezone

    logger = logging.getLogger(__name__)

    trans_id = data.get('TransID', '')
    amount = data.get('TransAmount', '0')
    phone = data.get('MSISDN', '')
    bill_ref = data.get('BillRefNumber', '').strip()
    first_name = data.get('FirstName', '')
    last_name = data.get('LastName', '')

    from .models import C2BTransaction, RentPayment, Tenancy
    from units.models import Unit

    c2b_txn, created = C2BTransaction.objects.get_or_create(
        trans_id=trans_id,
        defaults=dict(
            amount=amount,
            phone=phone,
            bill_ref=bill_ref,
            first_name=first_name,
            last_name=last_name,
            raw_data=data,
        ),
    )
    if not created:
        logger.info(f'C2B: Duplicate callback for TransID {trans_id}, skipped')
        return {'ResultCode': 0, 'ResultDesc': 'Already processed'}

    if bill_ref:
        business_shortcode = str(data.get('BusinessShortCode', '')).strip()
        landlord = None
        if business_shortcode:
            from django.contrib.auth.models import User
            landlord_match = User.objects.filter(
                profile__c2b_shortcode=business_shortcode,
                profile__role='landlord',
            ).first()
            if landlord_match:
                landlord = landlord_match

        units = Unit.objects.filter(unit_number=bill_ref)
        if landlord:
            units = units.filter(property__owner=landlord)
            if not units.exists():
                logger.warning(f'C2B: No unit "{bill_ref}" found for landlord with shortcode {business_shortcode} (TransID {trans_id})')
        else:
            logger.info(f'C2B: No landlord matched for shortcode "{business_shortcode}", falling back to global unit lookup (TransID {trans_id})')

        if units.count() > 1:
            logger.warning(f'C2B: Multiple units ({units.count()}) found for number "{bill_ref}" (TransID {trans_id}), using first match')
        unit = units.first()
        if not unit:
            logger.warning(f'C2B: No unit found with number "{bill_ref}" (TransID {trans_id})')
        else:
            tenancy = Tenancy.objects.filter(unit=unit, status='active').first()
            if tenancy:
                c2b_txn.matched_tenant = tenancy.tenant
                c2b_txn.save(update_fields=['matched_tenant'])

                receipt = trans_id
                pmt = RentPayment.objects.create(
                    tenancy=tenancy,
                    amount=amount,
                    due_date=timezone.now().date(),
                    paid_date=timezone.now().date(),
                    status='paid',
                    payment_method='mpesa',
                    reference=receipt,
                    notes=f'C2B payment via paybill (TransID {trans_id})',
                )

                paid_amount = Decimal(str(amount))
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

                logger.info(f'C2B: Applied KES {amount} to tenancy {tenancy.id} (unit {bill_ref})')
            else:
                logger.warning(f'C2B: No active tenancy for unit "{bill_ref}" (TransID {trans_id})')
    else:
        logger.warning(f'C2B: Empty BillRefNumber (TransID {trans_id})')

    return {'ResultCode': 0, 'ResultDesc': 'Accepted'}


def process_c2b_validation(data):
    """Validate a C2B transaction. Accept all for now."""
    return {'ResultCode': 0, 'ResultDesc': 'Success'}
