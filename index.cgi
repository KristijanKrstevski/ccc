#!/home/krstevski/.pyenv/versions/3.11.5/bin/python

import os
import sys

# Add project paths
project_dir = os.path.dirname(__file__)
sys.path.insert(0, project_dir)

# Set environment variables
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dealership_menagment.settings')

# Initialize PyMySQL
import pymysql
pymysql.install_as_MySQLdb()

# Import Django
import django
from django.core.wsgi import get_wsgi_application

# Setup Django
django.setup()

# Get Django WSGI application
application = get_wsgi_application()

# CGI handler
if __name__ == '__main__':
    from wsgiref.handlers import CGIHandler
    CGIHandler().run(application)