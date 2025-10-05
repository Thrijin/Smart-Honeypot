import subprocess, time

PY = 'python3'
FETCH = 'fetch_logs.py'
FEATURE = 'make_features.py'
AGENT = 'learn_agent.py'

def run_cmd(cmd):
    print('RUN:', cmd)
    subprocess.run(cmd, shell=True, check=True)

if __name__ == '__main__':
    while True:
        try:
            run_cmd(f"{PY} {FETCH}")
            run_cmd(f"{PY} {FEATURE}")
            run_cmd(f"{PY} {AGENT}")
            print('Iteration done. Sleep 10s before next cycle.')
            time.sleep(10)
        except KeyboardInterrupt:
            print('Stopped by user.')
            break
        except Exception as e:
            print('Error:', e)
            time.sleep(5)
