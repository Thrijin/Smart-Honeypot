import json
import random
import time
import paramiko
from make_features import parse_logs

HONEYPOT_IP = "192.168.56.102"     # change if needed
USERNAME = "kali"                  # SSH user
PASSWORD = "kali"                  # your password
REMOTE_LOG = "/home/kali/miniproject_honeypot_logs/servlog.log"

LOCAL_LOG = "./servlog_local.txt"
FEATURES_CSV = "./session_features.csv"
POLICY_FILE = "./policy_q.json"

ACTIONS = {
    0: "noop",          # do nothing
    1: "alert",         # pretend to alert
    2: "block_ip",      # pretend to block
    3: "throttle",      # pretend to slow down
    4: "restart_trap"   # pretend to restart honeypot
}

# ------------------------------------------------------------------
# Reward function
# ------------------------------------------------------------------
def compute_reward(session):
    suspicious = int(session.get('suspicious', 0))
    requests = int(session.get('requests', 0))
    ip = session.get('ip', '')

    if ip == "127.0.0.1":
        return 0

    if suspicious > 0:
        return 10 * suspicious   # big reward for catching suspicious

    if requests > 20:
        return -1                # penalty for noisy but non-suspicious

    return 0


# ------------------------------------------------------------------
# Fetch logs via SSH/SFTP
# ------------------------------------------------------------------
def fetch_logs():
    print("trying")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HONEYPOT_IP, username=USERNAME, password=PASSWORD)

    sftp = ssh.open_sftp()
    print(sftp, "this is an sftp")
    sftp.get(REMOTE_LOG, LOCAL_LOG)
    sftp.close()
    ssh.close()
    print(f"[+] Saved {LOCAL_LOG}")


# ------------------------------------------------------------------
# Main learning loop
# ------------------------------------------------------------------
def main():
    try:
        with open(POLICY_FILE, "r") as f:
            Q = json.load(f)
            Q = {int(k): float(v) for k, v in Q.items()}
    except FileNotFoundError:
        Q = {a: 0.0 for a in ACTIONS.keys()}

    # baseline: fetch logs and build sessions
    print("Fetching baseline logs...")
    fetch_logs()
    parse_logs()

    with open(FEATURES_CSV) as f:
        header = f.readline().strip().split(",")
        for line in f:
            parts = line.strip().split(",")
            session = dict(zip(header, parts))
            print("Session:", session)

            # choose random action
            action = random.choice(list(ACTIONS.keys()))
            print(f"Applied action: {action} {ACTIONS[action]}")

            # compute reward
            reward = compute_reward(session)
            print("Reward", reward, "Q", Q)

            # update Q-values (very simple update)
            Q[action] = Q[action] + 0.1 * (reward - Q[action])

    # save policy
    with open(POLICY_FILE, "w") as f:
        json.dump(Q, f, indent=2)
    print("Q saved")


if __name__ == "__main__":
    main()
