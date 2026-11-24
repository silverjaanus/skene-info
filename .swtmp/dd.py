import json, sys, os, re
# usage: python dd.py cands.txt   (lines: date|kw1,kw2|label)
def load(p):
    try:
        d = json.load(open(p, encoding='utf-8'))
    except Exception:
        return []
    if isinstance(d, dict):
        for k in ('events', 'items', 'entries', 'block', 'blocklist'):
            if isinstance(d.get(k), list): return d[k]
        out = []
        for v in d.values():
            if isinstance(v, list): out += [x for x in v if isinstance(x, dict)]
        return out
    return [x for x in d if isinstance(x, dict)]
srcs = []
for s in ['data', 'rap/data', 'klubi/data']:
    for f in ['manual.json', 'data.json', 'blocklist.json', 'archive/2026.json', 'archive/2027.json']:
        p = os.path.join(s, f)
        if os.path.exists(p): srcs.append((p, load(p)))
for line in open(sys.argv[1], encoding='utf-8'):
    line = line.strip()
    if not line or line.startswith('#'): continue
    d, kws, lab = (line.split('|') + ['', ''])[:3]
    kws = [k.strip().lower() for k in kws.split(',') if k.strip()]
    hits = []
    for p, arr in srcs:
        for e in arr:
            txt = (str(e.get('n', '')) + ' ' + ' '.join(map(str, e.get('b', []) or [])) + ' ' + str(e.get('nb', ''))[:0]).lower()
            ed = str(e.get('d', ''))
            dm = (ed == d) or (d == '*')
            km = any(k in txt for k in kws)
            if (dm and km) or (km and d == '*'):
                hits.append(f"{p}: {ed} {e.get('n','')[:60]} | b={len(e.get('b',[]) or [])} ou={'Y' if e.get('ou') else '-'} pu={'Y' if e.get('pu') else '-'} hind={'Y' if e.get('hind') else '-'} img={'Y' if e.get('img') else '-'}")
            elif dm and not km and d != '*' and 'v' in e and any(k in str(e.get('v','')).lower() for k in kws):
                hits.append(f"(koht) {p}: {ed} {e.get('n','')[:60]}")
    print(f"== {lab} [{d} {','.join(kws)}]:", 'UUS' if not hits else '')
    for h in hits[:6]: print('   ', h)
