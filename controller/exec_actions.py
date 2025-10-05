import paramiko

VM_IP = "192.168.56.101"
SSH_USER = "kali"
SSH_PASS = "kali"

def run_ssh(cmd):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VM_IP, username=SSH_USER, password=SSH_PASS, timeout=10)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    ssh.close()
    return out, err

def put_creds():
    cmd = 'echo "admin:Adm1nPass!" > /home/kali/trap_project/fake_creds.txt && chown kali:kali /home/kali/trap_project/fake_creds.txt'
    return run_ssh(cmd)

def enable_slow():
    cmd = 'touch /home/kali/trap_project/slow.mode && echo "SLOW_ON" >> /var/log/servlog.log'
    return run_ssh(cmd)

def disable_slow():
    cmd = 'rm -f /home/kali/trap_project/slow.mode && echo "SLOW_OFF" >> /var/log/servlog.log'
    return run_ssh(cmd)

def restart_trap():
    cmd = 'sudo systemctl restart trapd.service && echo "restarted"'
    return run_ssh(cmd)

ACTION_MAP = {
    0: ('noop', lambda: ('','')),
    1: ('put_creds', put_creds),
    2: ('enable_slow', enable_slow),
    3: ('disable_slow', disable_slow),
    4: ('restart_trap', restart_trap),
}

def apply_action(action_id):
    if action_id not in ACTION_MAP:
        return None, 'invalid'
    name, fn = ACTION_MAP[action_id]
    out, err = fn()
    return name, out+err

if __name__ == '__main__':
    print(apply_action(1))
