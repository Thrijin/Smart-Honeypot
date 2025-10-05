import paramiko, sys

SSH_USER = "kali"
SSH_PASS = "kali"
VM_IP = "192.168.56.102"
REMOTE_LOG = "/home/kali/miniproject_honeypot_logs/servlog.log"
LOCAL_LOG = "./servlog_local.txt"
PORT = 22

def fetch():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("trying");
    try:
        print(f"[+] Connecting to {VM_IP}...")
        ssh.connect(VM_IP, username=SSH_USER, password=SSH_PASS, timeout=10)
        sftp = ssh.open_sftp()
        print(sftp,"this is an sftp\n");
        with sftp.open(REMOTE_LOG, 'r') as remote:
            data = remote.read().decode()
        with open(LOCAL_LOG, "w") as f:
            f.write(data)
        print(f"[+] Saved {LOCAL_LOG}")
        sftp.close()
    except paramiko.AuthenticationException:
        print("Authentication failed. Check credentials.")
        sys.exit(1)
    except Exception as e:
        print("Error:", e)
        sys.exit(1)
    finally:
        try:
            ssh.close()
        except:
            pass

if __name__ == "__main__":
    fetch()
