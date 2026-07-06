"""Deploy script — pip install, migrate, collectstatic, restart."""
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load .env
if os.path.exists(BASE_DIR / '.env'):
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')

print('Installing requirements...')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(BASE_DIR / 'requirements.txt')])

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.core.management import call_command

print('Running migrations...')
call_command('migrate', '--noinput')

print('Collecting static files...')
call_command('collectstatic', '--noinput')

# Restart Passenger
restart_file = BASE_DIR / 'tmp' / 'restart.txt'
restart_file.parent.mkdir(parents=True, exist_ok=True)
restart_file.touch()
print(f'Restart file: {restart_file}')

print('Deploy complete.')
