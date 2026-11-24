import json, subprocess
src = json.load(open('.swtmp/sources_flat.json', encoding='utf-8'))
skip = {}
for i, e in enumerate(src):
    u = e['url']
    if 'ra.co/' in u: skip[i] = 'RA leht - loetud sweep/ra_snapshot.json-ist (tommatud 19.11); lisaks ra.co/events/ee/all avati ylekontrollis brauseris'
    elif not u: skip[i] = 'ARHIVEERITUD kirje (URL puudub)'
args = ['python', 'scripts/sweep_run_log.py', '--allikaid', str(len(src)), '--avatud', str(len(src) - len(skip)), '--uusi-www', '18', '--uusi-rap', '6', '--uusi-klubi', '15']
for i, r in skip.items():
    args += ['--skip', (src[i]['url'] or '(tyhi: ' + src[i]['nimi'] + ')') + '|' + r]
print(len(src), len(skip))
print(subprocess.run(args, capture_output=True, text=True, encoding='utf-8').stdout[-400:])
