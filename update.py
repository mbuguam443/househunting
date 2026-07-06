"""Update script — pull latest from GitHub and deploy."""
import os
import sys
import shutil
import zipfile
import tempfile
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ── CONFIG ──────────────────────────────────────────────
GITHUB_REPO = 'your-username/your-repo'       # <-- CHANGE THIS
GITHUB_BRANCH = 'main'
ZIP_URL = f'https://github.com/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip'

# Files/dirs to never overwrite
SKIP_NAMES = {'.env', '.htaccess', 'db.sqlite3', 'media', 'static_assets', 'tmp'}
# ────────────────────────────────────────────────────────

import requests

print(f'Downloading {ZIP_URL}...')
resp = requests.get(ZIP_URL, stream=True, timeout=60)
resp.raise_for_status()

with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
    for chunk in resp.iter_content(chunk_size=8192):
        tmp.write(chunk)
    zip_path = tmp.name

print('Extracting...')
with zipfile.ZipFile(zip_path, 'r') as zf:
    members = zf.namelist()
    top_dir = members[0].split('/')[0]

    for member in members:
        rel = '/'.join(member.split('/')[1:])
        if not rel:
            continue
        name = rel.split('/')[0]
        if name in SKIP_NAMES:
            continue
        target = BASE_DIR / rel
        if member.endswith('/'):
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(target, 'wb') as dst:
                shutil.copyfileobj(src, dst)

os.unlink(zip_path)
print('Extracted (skipped .env, .htaccess, media, static_assets, tmp, db.sqlite3).')

# Install any new dependencies
print('Installing requirements...')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(BASE_DIR / 'requirements.txt')])

# Run deploy steps
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.core.management import call_command

print('Running migrations...')
call_command('migrate', '--noinput')

print('Collecting static files...')
call_command('collectstatic', '--noinput')

restart_file = BASE_DIR / 'tmp' / 'restart.txt'
restart_file.parent.mkdir(parents=True, exist_ok=True)
restart_file.touch()
print(f'Restart file: {restart_file}')

print('Update complete.')
