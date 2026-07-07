import os
import sys

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_ROOT, ".env"))
except Exception:
    pass

from config.wsgi import application
