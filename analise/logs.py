import time
import re

SNORT_LOG = '/var/log/snort/alert'
APP_LOG = '/app/log/server.log'

def tail(f):
    f.seek(0, 2)
    while True:
        line = f.readline()
        if not line:
            time.sleep(1)
            continue
        yield line

def analyze_snort():
    print("Monitorando alertas do Snort...")
    with open(SNORT_LOG, 'r') as f:
        loglines = tail(f)
        for line in loglines:
            if 'SQL Injection Attempt' in line:
                print(f"[ALERTA SNORT] {line.strip()}")

def analyze_app():
    print("Monitorando erros do app Flask...")
    with open(APP_LOG, 'r') as f:
        loglines = tail(f)
        for line in loglines:
            if re.search(r"Database error", line):
                print(f"[ERRO APP] {line.strip()}")

if __name__ == '__main__':
    import threading
    t1 = threading.Thread(target=analyze_snort, daemon=True)
    t2 = threading.Thread(target=analyze_app, daemon=True)
    t1.start()
    t2.start()
    while True:
        time.sleep(1)
