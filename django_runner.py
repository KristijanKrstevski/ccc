#!/home/krstevski/.pyenv/versions/3.11.5/bin/python

import os
import sys
import subprocess

# Change to project directory
os.chdir('/home/krstevski/domains/autodinero.krstevski.me/public_html')

# Set up environment
os.environ['PYENV_ROOT'] = '/home/krstevski/.pyenv'
os.environ['PATH'] = '/home/krstevski/.pyenv/bin:' + os.environ.get('PATH', '')

# Run Django server on port 8001
subprocess.call([
    '/home/krstevski/.pyenv/versions/3.11.5/bin/python', 
    'manage.py', 
    'runserver', 
    '0.0.0.0:8001'
])