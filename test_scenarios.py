import re
import sys
import requests
from datetime import date

BASE = 'http://127.0.0.1:8000'

out = []
ok = 0
fail = 0
warn = 0

def log(label, status, detail=''):
    global ok, fail, warn
    if status == 'PASS':
        ok += 1
    elif status == 'FAIL':
        fail += 1
    else:
        warn += 1
    out.append(f"  [{status}] {label}")
    if detail:
        for line in detail.strip().split('\n'):
            out.append(f"          {line}")

def get_csrftoken_text(text):
    m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', text)
    if m:
        return m.group(1)
    return None

def login(s, username, password):
    r = s.get(f'{BASE}/accounts/login/')
    t = get_csrftoken_text(r.text)
    if not t:
        return None, 'no CSRF on login page'
    r = s.post(f'{BASE}/accounts/login/', data={
        'csrfmiddlewaretoken': t, 'username': username, 'password': password,
    })
    if r.status_code in (302, 303) or any(h.status_code in (302, 303) for h in r.history):
        return r, 'redirected'
    if 'sessionid' in s.cookies:
        return r, 'session cookie set'
    return r, f'status {r.status_code}, url {r.url}'

def status_str(r):
    if r.history:
        return ' -> '.join(f'{h.status_code} {h.url}' for h in r.history + [r])
    return f'{r.status_code} {r.url}'

# ──────────────────────────────────────────────
# SETUP: Login as admin and discover landlord IDs
# ──────────────────────────────────────────────
s_admin = requests.Session()
s_admin.headers['User-Agent'] = 'TestScript/1.0'
r, msg = login(s_admin, 'admin', 'admin123')
log('Admin login', 'PASS' if r else 'FAIL', msg or status_str(r))

# Discover landlord IDs from the page
r = s_admin.get(f'{BASE}/accounts/admin/landlords/')
landlord_ids = sorted(set(
    int(x) for x in re.findall(r'/accounts/admin/landlords/(\d+)/', r.text)
))
log(f'Discovered landlord IDs', 'PASS' if landlord_ids else 'FAIL',
    f'IDs: {landlord_ids}')

# Use the first valid landlord ID for subscription/fee tests
lid = landlord_ids[0] if landlord_ids else 2
log(f'Using landlord ID', 'INFO' if landlord_ids else 'WARN', f'lid={lid}')

# ──────────────────────────────────────────────
# 1. Admin creates a landlord
# ──────────────────────────────────────────────
print("\n1. Admin creates a landlord")

r = s_admin.get(f'{BASE}/accounts/admin/landlords/create/')
if r.status_code == 200:
    log('GET create landlord page', 'PASS', 'Status 200')
else:
    log('GET create landlord page', 'FAIL', f'Status {r.status_code}')

import time
unique_suffix = str(int(time.time()))[-6:]
landlord_uname = f'testlandlord{unique_suffix}'
t = get_csrftoken_text(r.text)
r2 = s_admin.post(f'{BASE}/accounts/admin/landlords/create/', data={
    'csrfmiddlewaretoken': t or s_admin.cookies.get('csrftoken', ''),
    'username': landlord_uname,
    'email': 'test@test.com',
    'password1': 'StrongTest789!',
    'password2': 'StrongTest789!',
})
# Check if redirected to landlord list (success)
if r2.history and any(h.status_code in (302, 303) for h in r2.history):
    log(f'POST create landlord ({landlord_uname})', 'PASS', status_str(r2))
else:
    # Parse error messages
    errs = re.findall(r'<li[^>]*>(.*?)</li>', r2.text, re.DOTALL)
    kept = [e.strip() for e in errs if len(e.strip()) > 5][:5]
    detail = '; '.join(kept)[:300] if kept else status_str(r2)
    log(f'POST create landlord ({landlord_uname})', 'FAIL', detail)

# ──────────────────────────────────────────────
# 2. Admin assigns a subscription
# ──────────────────────────────────────────────
print(f"\n2. Admin assigns a subscription (landlord ID={lid})")

r = s_admin.get(f'{BASE}/accounts/admin/landlords/{lid}/subscription/')
if r.status_code == 200:
    log(f'GET assign subscription page (ID={lid})', 'PASS', 'Status 200')
else:
    log(f'GET assign subscription page (ID={lid})', 'FAIL', f'Status {r.status_code}')
    # Try to find a valid link on the page
    links = re.findall(r'/accounts/admin/landlords/(\d+)/subscription/', r.text)
    log(f'  Subscription links in response', 'INFO',
        f'Found: {links[:5]}') if links else None

t = get_csrftoken_text(r.text) if r.status_code == 200 else None
r2 = s_admin.post(f'{BASE}/accounts/admin/landlords/{lid}/subscription/', data={
    'csrfmiddlewaretoken': t or s_admin.cookies.get('csrftoken', ''),
    'months': '1',
    'payment_reference': 'test123',
})
if r2.history and any(h.status_code in (302, 303) for h in r2.history):
    log(f'POST assign subscription (ID={lid})', 'PASS', status_str(r2))
else:
    log(f'POST assign subscription (ID={lid})', 'FAIL', status_str(r2))

# ──────────────────────────────────────────────
# 3. Admin sets landlord fee
# ──────────────────────────────────────────────
print(f"\n3. Admin sets landlord fee (ID={lid})")

r = s_admin.post(f'{BASE}/accounts/admin/landlords/{lid}/set-fee/', data={
    'csrfmiddlewaretoken': s_admin.cookies.get('csrftoken', ''),
    'fee_per_unit': '60.00',
})
if r.history and any(h.status_code in (302, 303) for h in r.history):
    log(f'POST set fee (ID={lid})', 'PASS', status_str(r))
elif r.status_code == 200 and r.url.endswith('/admin/landlords/'):
    log(f'POST set fee (ID={lid})', 'PASS', f'Redirected to landlord list: {r.url}')
else:
    log(f'POST set fee (ID={lid})', 'FAIL', status_str(r))

# ──────────────────────────────────────────────
# 4. Admin creates an admin listing
# ──────────────────────────────────────────────
print("\n4. Admin creates an admin listing")

r = s_admin.get(f'{BASE}/accounts/admin/listings/create/')
if r.status_code == 200:
    log('GET create listing page', 'PASS', 'Status 200')
else:
    log('GET create listing page', 'FAIL', f'Status {r.status_code}')

t = get_csrftoken_text(r.text)
r2 = s_admin.post(f'{BASE}/accounts/admin/listings/create/', data={
    'csrfmiddlewaretoken': t or s_admin.cookies.get('csrftoken', ''),
    'title': 'Test House',
    'description': 'Test desc',
    'county': 'Nairobi',
    'town': 'Westlands',
    'house_type': 'one_bedroom',
    'bedrooms': '2',
    'bathrooms': '1',
    'rent': '25000',
    'contact_name': 'Test',
    'contact_phone': '0712345678',
})
if r2.history and any(h.status_code in (302, 303) for h in r2.history):
    log('POST create listing', 'PASS', status_str(r2))
elif r2.status_code == 200 and r2.url.endswith('/admin/listings/'):
    log('POST create listing (probably succeeded, redirected)', 'PASS', status_str(r2))
else:
    # Check for error messages
    alerts = re.findall(r'class="alert[^"]*"[^>]*>(.*?)</div>', r2.text, re.DOTALL)
    detail = '; '.join(a.strip()[:150] for a in alerts)[:300] if alerts else status_str(r2)
    errs = re.findall(r'<li[^>]*>(.*?)</li>', r2.text, re.DOTALL)
    kept = [e.strip() for e in errs if len(e.strip()) > 5][:3]
    if kept:
        detail += ' | ' + '; '.join(kept)
    log('POST create listing', 'FAIL', detail[:400])

# ──────────────────────────────────────────────
# 5. Landlord marks rent as paid
# ──────────────────────────────────────────────
print("\n5. Landlord (grace) marks rent as paid")

s_grace = requests.Session()
s_grace.headers['User-Agent'] = 'TestScript/1.0'
r, msg = login(s_grace, 'grace', 'grace123')
log('Login as grace', 'PASS' if r else 'FAIL', msg or status_str(r))

r = s_grace.get(f'{BASE}/dashboard/tenants/rent-collection/')
if r.status_code == 200:
    log('GET rent collection', 'PASS', 'Status 200')
else:
    log('GET rent collection', 'FAIL', f'Status {r.status_code}')

# Find mark-paid URLs and unpaid payment IDs
urls = re.findall(r'/dashboard/tenants/payments/(\d+)/mark-paid/', r.text)
if urls:
    log(f'Found mark-paid links', 'PASS', f'{len(urls)} links, first PK: {urls[0]}')
else:
    # Try finding just payment IDs
    pks = re.findall(r'href="[^"]*/payments/(\d+)/[^"]*"', r.text)
    log(f'Found payment links', 'WARN', str(pks) if pks else 'No mark-paid URLs found')

if urls:
    pk = urls[0]
    r2 = s_grace.get(f'{BASE}/dashboard/tenants/payments/{pk}/mark-paid/')
    if r2.status_code == 200:
        log(f'GET mark-paid #{pk}', 'PASS', 'Status 200')
        t = get_csrftoken_text(r2.text) or s_grace.cookies.get('csrftoken', '')
        r3 = s_grace.post(f'{BASE}/dashboard/tenants/payments/{pk}/mark-paid/', data={
            'csrfmiddlewaretoken': t,
            'amount': '15000',
            'paid_date': str(date.today()),
            'payment_method': 'cash',
            'reference': 'manual_test',
            'notes': 'Test payment',
        })
        if r3.history and any(h.status_code in (302, 303) for h in r3.history):
            log(f'POST mark-paid #{pk}', 'PASS', status_str(r3))
        else:
            alerts = re.findall(r'class="alert[^"]*"[^>]*>(.*?)</div>', r3.text, re.DOTALL)
            det = '; '.join(a.strip()[:150] for a in alerts)[:300] if alerts else status_str(r3)
            log(f'POST mark-paid #{pk}', 'FAIL', det)
    else:
        log(f'GET mark-paid #{pk}', 'FAIL', f'Status {r2.status_code}')
else:
    log('Skip mark-paid - no URLs', 'WARN')

# ──────────────────────────────────────────────
# 6. Tenant views lease and pay pages
# ──────────────────────────────────────────────
print("\n6. Tenant (johndoe) views lease & pay")

s_tenant = requests.Session()
s_tenant.headers['User-Agent'] = 'TestScript/1.0'
r, msg = login(s_tenant, 'johndoe', 'password123')
log('Login as johndoe', 'PASS' if r else 'FAIL', msg or status_str(r))

r = s_tenant.get(f'{BASE}/portal/lease/')
log('GET /portal/lease/', 'PASS' if r.status_code == 200 else 'FAIL', status_str(r))

r = s_tenant.get(f'{BASE}/portal/pay/')
log('GET /portal/pay/', 'PASS' if r.status_code == 200 else 'FAIL', status_str(r))

# ──────────────────────────────────────────────
# 7. 404 and error handling
# ──────────────────────────────────────────────
print("\n7. 404 and error handling")

s_anon = requests.Session()
s_anon.headers['User-Agent'] = 'TestScript/1.0'

r = s_anon.get(f'{BASE}/house/99999/')
log('GET /house/99999/', 'PASS' if r.status_code == 404 else 'FAIL', status_str(r))

# Login as admin then visit non-existent landlord
s_a2 = requests.Session()
s_a2.headers['User-Agent'] = 'TestScript/1.0'
login(s_a2, 'admin', 'admin123')
r = s_a2.get(f'{BASE}/accounts/admin/landlords/99999/')
if r.status_code == 404:
    log('GET admin landlord 99999 (logged in)', 'PASS', status_str(r))
else:
    log('GET admin landlord 99999 (logged in)', 'INFO', status_str(r))

# ──────────────────────────────────────────────
# RESULTS
# ──────────────────────────────────────────────
print('-' * 50)
print(f'RESULTS: {ok} passed, {fail} failed, {warn} warnings')
print('-' * 50)
print('\n'.join(out))
