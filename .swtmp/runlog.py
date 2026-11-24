import json, subprocess, sys
src = json.load(open('.swtmp/sources_flat.json', encoding='utf-8'))
skip = {}
for i, e in enumerate(src):
    u = e['url']
    if 'ra.co/' in u: skip[i] = 'RA leht - loetud sweep/ra_snapshot.json-ist (tommatud 19.11)'
    elif i in (13, 163, 172, 173, 175, 176, 268): skip[i] = 'Bandcampi konto - valvab check_bandcamp.py (Andmekorje)'
    elif 'open.spotify.com' in u: skip[i] = 'Spotify - uute reliiside nimekirja ei anna; valvab Bandcamp/discover'
    elif 'facebook.com/search/' in u: skip[i] = 'FB otsingu-URL, mitte events-tab (URL vajab parandamist /events kujule)'
    elif not u: skip[i] = 'ARHIVEERITUD kirje (URL puudub)'
    elif i == 168: skip[i] = 'mooduunud 2026 urituse FB-leht (Tartu Rock Fest 2026), 2027 kirje kontrollitud eraldi'
    elif i == 133: skip[i] = 'kluub.ee Tallinn - katab igapaevane postkastijooks (samm 2c); Tartu leht avati'
args = ['python', 'scripts/sweep_run_log.py', '--allikaid', str(len(src)), '--avatud', str(len(src) - len(skip)), '--uusi-www', '17', '--uusi-rap', '5', '--uusi-klubi', '10']
for i, r in skip.items():
    args += ['--skip', (src[i]['url'] or '(tühi: ' + src[i]['nimi'] + ')') + '|' + r]
print(len(src), len(skip))
print(subprocess.run(args, capture_output=True, text=True, encoding='utf-8').stdout[-800:])
