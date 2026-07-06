"""cPanel Passenger WSGI entry point — failsafe version."""
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

application = None
_startup_error = None

# Try to load Django app
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
    from config.wsgi import application as _app
    application = _app
except Exception as e:
    _startup_error = traceback.format_exc()

# Fallback WSGI app
def application(environ, start_response):
    if _startup_error:
        body = (
            b'<h1>Startup Error</h1>'
            b'<pre>' + _startup_error.encode() + b'</pre>'
        )
    else:
        body = b'<h1>App loaded (no errors)</h1>'
    status = '200 OK'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    return [body]
