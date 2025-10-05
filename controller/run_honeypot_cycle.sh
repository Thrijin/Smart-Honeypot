#!/usr/bin/env bash
# run_honeypot_cycle.sh
# Usage: ./run_honeypot_cycle.sh [HONEYPOT_IP] [SSH_USER]
# Defaults: HONEYPOT_IP=192.168.56.101  SSH_USER=kali
# Run from your attacker/controller working directory (where make_features.py etc live)

set -euo pipefail
IFS=$'\n\t'

HONEYPOT="${1:-192.168.56.101}"
SSH_USER="${2:-kali}"
REMOTE_LOG="/home/kali/miniproject_honeypot_logs/servlog.log"
LOCAL_LOG="./servlog_local.txt"

echo "== Honeypot cycle script =="
echo " Honeypot: $HONEYPOT"
echo " SSH user: $SSH_USER"
echo " Remote log: $REMOTE_LOG"
echo

# 1) wait for honeypot to respond to ping (timeout 60s)
echo -n "Waiting for $HONEYPOT to respond to ping "
TRIES=0
MAX_TRIES=30
until ping -c 1 -W 1 "$HONEYPOT" >/dev/null 2>&1; do
  TRIES=$((TRIES+1))
  if [ "$TRIES" -ge "$MAX_TRIES" ]; then
    echo
    echo "Timeout waiting for $HONEYPOT to respond to ping. Exiting."
    exit 2
  fi
  echo -n "."
  sleep 1
done
echo " OK"

# 2) quick connectivity checks
echo "Checking ports on $HONEYPOT (8080,22)..."
nc -vz -w 2 "$HONEYPOT" 8080 2>/dev/null || echo "  port 8080: closed or filtered"
nc -vz -w 2 "$HONEYPOT" 22 2>/dev/null || echo "  port 22: closed or filtered"
echo

# 3) run probe sequence
echo "Running probe sequence against http://$HONEYPOT:8080 ..."
# Basic GETs
curl -s "http://$HONEYPOT:8080/" >/dev/null || true
curl -s "http://$HONEYPOT:8080/admin" >/dev/null || true
curl -s "http://$HONEYPOT:8080/login" >/dev/null || true

# SQLi-like GETs and a POST
curl -G "http://$HONEYPOT:8080/search" --data-urlencode "q=' OR '1'='1" -s -o /dev/null || true
curl -s -X POST "http://$HONEYPOT:8080/login" -d "username=admin' OR '1'='1&password=x" -o /dev/null || true

# short burst to create a session
echo "Creating short burst (20 requests, 1s interval) ..."
for i in $(seq 1 20); do
  curl -s "http://$HONEYPOT:8080/?probe=attack${i}" >/dev/null || true
  sleep 1
done
echo "Probes finished."
echo

# 4) fetch the remote log via scp (interactive)
echo "Fetching remote log via scp (you will be prompted for password if needed)..."
if scp -q "${SSH_USER}@${HONEYPOT}:${REMOTE_LOG}" "${LOCAL_LOG}"; then
  echo "Saved ${LOCAL_LOG} (size: $(stat -c%s "${LOCAL_LOG}") bytes)"
else
  echo "scp failed. Attempting ssh-cat fallback..."
  if ssh "${SSH_USER}@${HONEYPOT}" "cat '${REMOTE_LOG}'" > "${LOCAL_LOG}"; then
    echo "Saved ${LOCAL_LOG} via ssh-cat fallback."
  else
    echo "Failed to fetch remote log. Exiting."
    exit 3
  fi
fi

# 5) show a few lines of the fetched log
echo
echo "---- head of ${LOCAL_LOG} ----"
head -n 40 "${LOCAL_LOG}" || true
echo "---- end head ----"
echo

# 6) run feature extraction and learning (assumes python scripts exist here)
if [ -f make_features.py ]; then
  echo "Running make_features.py ..."
  python3 make_features.py || { echo "make_features.py failed"; exit 4; }
else
  echo "make_features.py not found in $(pwd). Skipping feature step."
fi

if [ -f learn_agent.py ]; then
  echo "Running learn_agent.py ..."
  python3 learn_agent.py || { echo "learn_agent.py failed"; exit 5; }
else
  echo "learn_agent.py not found in $(pwd). Skipping learning step."
fi

# 7) summarize session_features.csv and policy_q.json if present
echo
if [ -f session_features.csv ]; then
  echo "Top suspicious sessions (ip, suspicious, requests):"
  awk -F, 'NR>1{print $1","$5","$4}' session_features.csv | sort -t, -k2,2nr | head -n 20
  echo
  echo "session_features.csv (first 20 rows):"
  column -t -s, session_features.csv | sed -n '1,20p' || true
else
  echo "session_features.csv not present."
fi

if [ -f policy_q.json ]; then
  echo
  echo "policy_q.json (Q-values):"
  python3 - <<'PY'
import json,sys
print(json.dumps(json.load(open('policy_q.json')), indent=2))
PY
else
  echo "policy_q.json not present."
fi

echo
echo "Honeypot cycle complete."

