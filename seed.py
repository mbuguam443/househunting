"""Seed database with initial data."""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load .env
_env = BASE_DIR / '.env'
if _env.exists():
    from dotenv import load_dotenv
    load_dotenv(_env)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.contrib.auth.models import User
from accounts.models import PlatformConfig

# Create superuser if none exists
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username=os.environ.get('SEED_ADMIN_USER', 'admin'),
        email=os.environ.get('SEED_ADMIN_EMAIL', 'admin@patanyumba.com'),
        password=os.environ.get('SEED_ADMIN_PASSWORD', 'admin123'),
    )
    print('Superuser created.')
else:
    print('Superuser already exists.')

# Create PlatformConfig if none exists
if not PlatformConfig.objects.exists():
    PlatformConfig.objects.create()
    print('PlatformConfig created.')
else:
    print('PlatformConfig already exists.')

print('Seed complete.')
