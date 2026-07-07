"""Database setup — pip install, migrate, collectstatic, restart."""
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# 1. Install packages first (so dotenv, pymysql etc. are available)
print('Installing requirements...')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(BASE_DIR / 'requirements.txt')])

# 2. Load .env
_env = BASE_DIR / '.env'
if _env.exists():
    from dotenv import load_dotenv
    load_dotenv(_env)

# 3. Run Django management commands
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.core.management import call_command

print('Running migrations...')
call_command('migrate', '--noinput')

print('Collecting static files...')
call_command('collectstatic', '--noinput')

# 4. Restart Passenger
restart = BASE_DIR / 'tmp' / 'restart.txt'
restart.parent.mkdir(parents=True, exist_ok=True)
restart.touch()
print(f'Restarted: {restart}')
print('Setup complete.')
