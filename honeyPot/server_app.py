#!/usr/bin/env python3
# server_app.py  - simple RL-friendly honeypot server (binds to host-only IP)
# Logs are written to ~/miniproject_honeypot_logs/servlog.log (user-writable)

from flask import Flask, request
import logging
import pathlib
import os
import time
import json

# --- user-writable logging location (in home directory) ---
HOME = pathlib.Path.home()
LOG_DIR = HOME / "miniproject_honeypot_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOGFILE = str(LOG_DIR / "servlog.log")

logging.basicConfig(filename=LOGFILE, level=logging.INFO, format="%(asctime)s - %(message)s")

app = Flask(__name__)

# Use trap_project directory inside the user's home (safer than hard-coded /home/kali)
TRAP_DIR = HOME / "trap_project"
TRAP_DIR.mkdir(parents=True, exist_ok=True)

SLOW_FLAG = str(TRAP_DIR / "slow.mode")              # presence toggles slow responses
CREDS_FILE = str(TRAP_DIR / "fake_creds.txt")       # file served at /creds if present

def maybe_delay():
    try:
        if os.path.exists(SLOW_FLAG):
            time.sleep(4)  # slow down by 4 seconds to keep attacker engaged
    except Exception:
        # Don't let delay checks crash the server
        pass

def log_request(label='', payload=''):
    remote = getattr(request, "remote_addr", "unknown")
    try:
        logging.info(f"{label} {remote} {request.method} {request.path} {payload}")
    except Exception:
        # logging shouldn't crash the app
        pass

@app.route('/', defaults={'path': ''}, methods=['GET','POST'])
@app.route('/<path:path>', methods=['GET','POST'])
def catch_all(path):
    maybe_delay()
    body = request.get_data(as_text=True) or ''
    log_request('REQ', body)
    if path == 'creds' and os.path.exists(CREDS_FILE):
        try:
            with open(CREDS_FILE, 'r') as f:
                data = f.read()
            log_request('SERVE_CREDS', data)
            return data, 200
        except Exception:
            # if reading fails, just return generic message
            return 'Service running', 200
    return 'Service running', 200

@app.route('/login', methods=['POST'])
def login():
    maybe_delay()
    try:
        data = request.form.to_dict() or request.get_json() or {}
    except Exception:
        data = {}
    log_request('LOGIN', json.dumps(data))
    return 'Login failed', 403

if __name__ == '__main__':
    # bind to your host-only IP; change if your honeypot IP is different
    app.run(host='192.168.56.102', port=8081)
