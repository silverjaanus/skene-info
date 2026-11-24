import json, re, os
d = json.load(open('sweep/ra_snapshot.json', encoding='utf-8'))
ev = d['kirjed']
print('tommatud', d['tommatud'], 'kirjeid', len(ev))
print('sample', json.dumps(ev[0], ensure_ascii=False)[:500])
def load(p):
    try: x = json.load(open(p, encoding='utf-8'))
    except Exception: return []
    if isinstance(x, dict):
        out = []
        for v in x.values():
            if isinstance(v, list): out += [e for e in v if isinstance(e, dict)]
        return out
    return [e for e in x if isinstance(e, dict)]
known = []
for s in ['data', 'rap/data', 'klubi/data']:
    for f in ['manual.json', 'data.json', 'blocklist.json']:
        known += load(os.path.join(s, f))
blob = json.dumps(known, ensure_ascii=False).lower()
def words(s): return [w for w in re.findall(r'[a-zäöüõšž0-9]{4,}', s.lower()) if w not in ('tallinn','tartu','with','night','club','party','presents','live')]
for e in ev:
    dd = str(e.get('d') or e.get('date') or '')[:10]
    t = e.get('n') or e.get('title') or ''
    url = e.get('url') or e.get('ou') or e.get('su') or ''
    same = [k for k in known if str(k.get('d','')) == dd]
    hit = False
    for k in same:
        kt = (k.get('n','') + ' ' + ' '.join(map(str, k.get('b',[]) or [])) + ' ' + str(k.get('ou','')) + str(k.get('su','')) + str(k.get('pu',''))).lower()
        if (url and url.lower().split('?')[0] in kt) or any(w in kt for w in words(t)):
            hit = True; break
    if not hit and url and url.lower().split('?')[0] in blob: hit = True
    if not hit:
        print('NEW', dd, '|', t[:70], '|', e.get('v') or e.get('venue',''), '|', url, '|', ','.join((e.get('b') or e.get('artists') or [])[:8]) if isinstance(e.get('b') or e.get('artists'), list) else '')
