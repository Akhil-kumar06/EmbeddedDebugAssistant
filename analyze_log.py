import argparse,json
from core import analyze,format_report
p=argparse.ArgumentParser();p.add_argument('log');p.add_argument('--json',action='store_true');a=p.parse_args()
try:
    d=analyze(a.log);print(json.dumps(d,indent=2) if a.json else format_report(d))
except (ValueError,OSError) as e:p.exit(1,str(e)+'\n')
