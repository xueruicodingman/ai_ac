#!/usr/bin/env python
import os
import sys
import subprocess
import time

os.chdir('/Users/ximenruixue/Desktop/AC_AI/backend')
os.environ['PYTHONPATH'] = '/Users/ximenruixue/Desktop/AC_AI/backend'
os.environ['PATH'] = '/opt/anaconda3/bin:' + os.environ.get('PATH', '')

# Redirect output
with open('/tmp/backend.log', 'w') as f:
    proc = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'src.main:app', '--host', '127.0.0.1', '--port', '8000'],
        stdout=f, stderr=subprocess.STDOUT
    )
    print(f'Backend started with PID: {proc.pid}')
    sys.exit(0)