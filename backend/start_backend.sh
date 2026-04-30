#!/bin/bash
cd /Users/ximenruixue/Desktop/AC_AI/backend
export PYTHONPATH=/Users/ximenruixue/Desktop/AC_AI/backend
exec /opt/anaconda3/bin/python3.11 run_server.py </dev/null >/dev/null 2>&1 &
echo "Backend started with PID: $!"