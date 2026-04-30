#!/usr/bin/env python3
import sys
import os
os.chdir('/Users/ximenruixue/Desktop/aitalent/backend')
os.environ['PYTHONPATH'] = '/Users/ximenruixue/Desktop/aitalent/backend'
import uvicorn
from src.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)