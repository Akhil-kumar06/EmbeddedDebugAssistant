"""Deterministic analysis of recorded telemetry. Does not require AI."""
import json, math
from pathlib import Path
def number(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
def analyze(path):
    path=Path(path)
    if path.stat().st_size>5*1024*1024: raise ValueError('Maximum log size is 5 MiB.')
    rows=[];kind=None;previous=None;bad=[];episodes=[];active={}
    invalid_first=None;invalid_prev=None;invalid_delta=0;resets=0
    def event(key,condition,line,ms):
        if condition and key not in active:
            item=dict(finding=key,start_line=line,start_ms=ms,end_line=None,end_ms=None)
            active[key]=item;episodes.append(item)
        elif not condition and key in active:
            item=active.pop(key);item.update(end_line=line,end_ms=ms)
    with path.open(encoding='utf-8-sig') as stream:
        for line,text in enumerate(stream,1):
            if not text.strip():continue
            try:
                r=json.loads(text)
                if not isinstance(r,dict) or not number(r.get('ms')) or r['ms']<0:raise ValueError()
                if all(k in r for k in ('engine','vehicle','rpm','temp','speed','invalid','alarm')):
                    current='CANLab'
                    if r['engine'] not in ('WAITING','OK','TIMEOUT') or r['vehicle'] not in ('WAITING','OK','TIMEOUT'):raise ValueError()
                    if not all(number(r[k]) and r[k]>=0 for k in ('rpm','temp','speed','invalid')) or not isinstance(r['alarm'],bool):raise ValueError()
                elif all(k in r for k in ('state','fault','temperature','fan','age_ms')):
                    current='FirmwareLab'
                    if r['state'] not in ('IDLE','RUNNING','WARNING','FAULT') or r['fault'] not in ('OK','SENSOR_INVALID','SENSOR_STALE','OVERTEMP'):raise ValueError()
                    if not all(number(r[k]) for k in ('temperature','fan','age_ms')) or not 0<=r['fan']<=1 or r['age_ms']<0:raise ValueError()
                else:raise ValueError()
            except (ValueError,TypeError):
                bad.append(line);continue
            if kind and current!=kind:raise ValueError('Mixed projects: use one project per log.')
            kind=current
            if previous is not None and r['ms']<previous:raise ValueError(f'Timestamps go backwards at line {line}; split separate runs.')
            previous=r['ms'];rows.append((line,r))
            if kind=='CANLab':
                for node in ('engine','vehicle'):
                    for state in ('TIMEOUT','WAITING'):event(node+' '+state,r[node]==state,line,r['ms'])
                event('Overheat alarm',r['alarm'],line,r['ms'])
                if invalid_prev is None:invalid_first=r['invalid']
                elif r['invalid']>=invalid_prev:invalid_delta+=r['invalid']-invalid_prev
                else:resets+=1
                invalid_prev=r['invalid']
            else:
                for fault in ('SENSOR_INVALID','SENSOR_STALE','OVERTEMP'):event(fault,r['fault']==fault,line,r['ms'])
                event('WARNING',r['state']=='WARNING',line,r['ms'])
    if not rows:raise ValueError('No valid FirmwareLab/CANLab telemetry records.')
    notes=[]
    if bad:notes.append(f'{len(bad)} invalid rows skipped. First affected lines: {bad[:12]}. Gaps can hide transitions.')
    if kind=='CANLab':
        notes.append(f'Rejected-frame increase within excerpt: {invalid_delta}; initial counter: {invalid_first}; resets: {resets}.')
        notes.append('TIMEOUT indicates missing accepted frames, not a proven cause. Possible causes include paused publisher, rejected frames, or host scheduling.')
    else:notes.append('FirmwareLab milliseconds are simulated time, not wall-clock performance.')
    return dict(project=kind,records=len(rows),skipped=len(bad),first_ms=rows[0][1]['ms'],
                last_ms=rows[-1][1]['ms'],latest_line=rows[-1][0],latest=rows[-1][1],
                episodes=episodes,notes=notes)
def format_report(d):
    out=[f"{d['project']} | {d['records']} valid records | {d['skipped']} skipped",
         f"Recorded interval: {d['first_ms']} to {d['last_ms']} ms",
         f"Latest [line {d['latest_line']}]: {json.dumps(d['latest'])}",'','Observed episodes:']
    if not d['episodes']:out.append('No monitored fault/warning/waiting episodes in valid rows. This does not prove the system is fault-free.')
    for e in d['episodes'][:60]:
        end=f"cleared by line {e['end_line']} at {e['end_ms']} ms" if e['end_line'] else 'still reported at end of valid records'
        out.append(f"- {e['finding']}: line {e['start_line']} at {e['start_ms']} ms; {end}.")
    if len(d['episodes'])>60:out.append('Only first 60 episodes displayed.')
    return '\n'.join(out+['','Notes:',*d['notes'],'Snapshot only. Clearing times are first observed samples. No live hardware diagnosis.'])
