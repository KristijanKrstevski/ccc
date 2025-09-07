#!/home/krstevski/.pyenv/versions/3.11.5/bin/python

import sys
import os

print("Content-Type: text/html")
print()

# Check Python version immediately and stop if wrong
if sys.version_info < (3, 10):
    print(f"""<html><body>
    <h1>Python Version Mismatch</h1>
    <p><strong>Current:</strong> Python {sys.version_info.major}.{sys.version_info.minor}</p>
    <p><strong>Required:</strong> Python 3.10+</p>
    <p><strong>Server:</strong> {os.environ.get('SERVER_SOFTWARE', 'Unknown')}</p>
    <hr>
    <p>Configure your server to use: <code>/home/krstevski/.pyenv/versions/3.11.5/bin/python</code></p>
    <p>Current executable: <code>{sys.executable}</code></p>
    </body></html>""")
    sys.exit(1)

try:
    # Clean up sys.path to avoid mixing Python versions
    sys.path = [path for path in sys.path if not path.startswith('/usr/lib')]
    
    # Add correct paths
    correct_site_packages = '/home/krstevski/.pyenv/versions/3.11.5/lib/python3.11/site-packages'
    project_dir = os.path.dirname(__file__)
    vendor_dir = os.path.join(project_dir, 'vendor')
    
    # Insert paths in correct order
    sys.path.insert(0, project_dir)
    if os.path.exists(vendor_dir):
        sys.path.insert(0, vendor_dir)
    sys.path.insert(0, correct_site_packages)
    
    # Set environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dealership_menagment.settings')
    
    # Import and setup PyMySQL
    import pymysql
    pymysql.install_as_MySQLdb()
    
    # Import Django and setup
    import django
    django.setup()
    
    # Simple Django response for now
    from dealership_app.frontend_views import index as index_view
    from django.test import RequestFactory
    
    factory = RequestFactory()
    path_info = os.environ.get('PATH_INFO', '/')
    query_string = os.environ.get('QUERY_STRING', '')
    
    request = factory.get(path_info + ('?' + query_string if query_string else ''))
    response = index_view(request)
    
    print(response.content.decode('utf-8'))
    
except Exception as e:
    import traceback
    print(f"""<html><body>
    <h1>Application Error</h1>
    <p>An error occurred while loading the Django application.</p>
    <p><strong>Error:</strong> {str(e)}</p>
    <hr>
    <details>
    <summary>Technical Details</summary>
    <pre>Python: {sys.version}
Executable: {sys.executable}
Error: {traceback.format_exc()}</pre>
    </details>
    </body></html>""")