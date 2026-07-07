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
from django.utils import timezone
from accounts.models import PlatformConfig

# Create superuser if none exists
admin_user = None
if not User.objects.filter(is_superuser=True).exists():
    admin_user = User.objects.create_superuser(
        username=os.environ.get('SEED_ADMIN_USER', 'admin'),
        email=os.environ.get('SEED_ADMIN_EMAIL', 'admin@patanyumba.com'),
        password=os.environ.get('SEED_ADMIN_PASSWORD', 'admin123'),
    )
    print('Superuser created.')
else:
    admin_user = User.objects.filter(is_superuser=True).first()
    print('Superuser already exists.')

# Set superuser profile role to 'admin' so it bypasses subscription checks
if admin_user and admin_user.profile.role != 'admin':
    admin_user.profile.role = 'admin'
    admin_user.profile.save()
    print('Superuser role set to admin.')

# Create PlatformConfig if none exists
if not PlatformConfig.objects.exists():
    PlatformConfig.objects.create()
    print('PlatformConfig created.')
else:
    print('PlatformConfig already exists.')

# Set trial_started_at for any landlord accounts that don't have it
landlords = User.objects.filter(profile__role='landlord', profile__trial_started_at__isnull=True)
for user in landlords:
    user.profile.trial_started_at = timezone.now()
    user.profile.save()
    print(f'Trial started for landlord: {user.username}')

print('Seed complete.')
