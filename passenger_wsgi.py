"""cPanel Passenger WSGI entry point."""
import os
import sys
import traceback

_app_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _app_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Load .env before Django
_env_path = os.path.join(_app_root, '.env')
if os.path.exists(_env_path):
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
    except ImportError:
        pass

try:
    import django
    django.setup()
    from django.core.management import call_command
    _setup_flag = os.path.join(_app_root, 'tmp', '.setup_done')
    if not os.path.exists(_setup_flag):
        try:
            call_command('migrate', '--noinput')
            call_command('collectstatic', '--noinput')
            os.makedirs(os.path.dirname(_setup_flag), exist_ok=True)
            open(_setup_flag, 'w').close()
        except Exception:
            pass
    from config.wsgi import application
except Exception:
    _startup_error = traceback.format_exc()
    def application(environ, start_response):
        body = '<h1>Startup Error</h1><pre>{}</pre>'.format(
            _startup_error.replace('&', '&amp;').replace('<', '&lt;')
        ).encode()
        start_response('200 OK', [('Content-type', 'text/html')])
        return [body]
