import re, csv
from dateutil import parser
from collections import defaultdict

INPUT = "./servlog_local.txt"
OUTPUT = "./session_features.csv"

def parse_logs():
    line_re = re.compile(r'(?P<ts>[\d\-\:\s\.,]+)\s-\s(?P<msg>.+)')
    sessions = defaultdict(list)
    with open(INPUT, 'r', errors='ignore') as f:
        for ln in f:
            m = line_re.search(ln)
            if not m:
                continue
            # tolerant timestamp parsing
            ts_str = m.group('ts').strip()
            ts_str = ts_str.replace(',', '.')
            try:
                ts = parser.parse(ts_str)
            except Exception:
                try:
                    ts = parser.parse(ts_str.split('.')[0])
                except Exception:
                    continue
            msg = m.group('msg')
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', msg)
            ip = ip_match.group(1) if ip_match else 'unknown'
            sessions[ip].append((ts, msg))
    rows = []
    for ip, events in sessions.items():
        events.sort()
        start = events[0][0]
        end = events[-1][0]
        duration = (end - start).total_seconds()
        count = len(events)
        suspicious = sum(1 for _,m in events if any(k in m.lower() for k in ['login','passwd','sql','select','admin','upload','payload']))
        rows.append({
            'ip': ip,
            'start': start.isoformat(),
            'duration': duration,
            'requests': count,
            'suspicious': suspicious
        })
    with open(OUTPUT, 'w', newline='') as csvf:
        w = csv.DictWriter(csvf, fieldnames=['ip','start','duration','requests','suspicious'])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print('Wrote', OUTPUT)

if __name__ == '__main__':
    parse_logs()
