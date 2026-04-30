#!/bin/bash
source /opt/anaconda3/bin/activate root
cd /Users/ximenruixue/Desktop/AC_AI/backend
export PYTHONPATH=/Users/ximenruixue/Desktop/AC_AI/backend
exec python -m uvicorn src.main:app --host 127.0.0.1 --port 8000