#!/home/krstevski/.pyenv/versions/3.11.5/bin/python

import os
import sys
from datetime import datetime

# Add pyenv path (based on your Passenger WSGI)
pyenv_root = os.path.expanduser('~/.pyenv')
pyenv_bin = os.path.join(pyenv_root, 'bin')
if pyenv_bin not in os.environ.get('PATH', '').split(':'):
    os.environ['PATH'] = pyenv_bin + ':' + os.environ.get('PATH', '')

# Add project paths
project_dir = os.path.dirname(__file__)
sys.path.insert(0, project_dir)

# Set environment variables
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dealership_menagment.settings')
os.environ.setdefault('PYENV_ROOT', pyenv_root)

# Simple debug logging
def log_debug(message):
    try:
        log_path = '/home/krstevski/domains/autodinero.krstevski.me/public_html/logs/debug.log'
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(f"{datetime.now()}: {message}\n")
    except:
        pass

def application(environ, start_response):
    log_debug(f"WSGI called - Python {sys.version_info.major}.{sys.version_info.minor}")
    log_debug(f"SERVER_SOFTWARE: {environ.get('SERVER_SOFTWARE', 'Unknown')}")
    
    try:
        # Try to import Django WSGI application
        from django.core.wsgi import get_wsgi_application
        django_app = get_wsgi_application()
        log_debug("Django WSGI app created successfully")
        
        # Use Django to handle the request
        return django_app(environ, start_response)
        
    except Exception as e:
        log_debug(f"Django error: {str(e)}")
        
        # Fallback response with error info
        start_response("500 Internal Server Error", [("Content-Type", "text/html")])
        
        response_body = f"""<html><body>
        <h1>Django Integration Error</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <p>Python Version: {sys.version}</p>
        <p>Python Executable: {sys.executable}</p>
        <p>Server: {environ.get('SERVER_SOFTWARE', 'Unknown')}</p>
        <p>Request Method: {environ.get('REQUEST_METHOD', 'Unknown')}</p>
        <p>Path Info: {environ.get('PATH_INFO', 'Unknown')}</p>
        <p>Check logs/debug.log for details</p>
        </body></html>"""
        
        return [response_body.encode('utf-8')]
