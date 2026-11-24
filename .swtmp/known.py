import json, re, glob, os
from collections import defaultdict
files = []
for site in ['data', 'rap/data', 'klubi/data']:
    for f in ['manual.json', 'data.json', 'blocklist.json']:
        p = os.path.join(site, f)
        if os.path.exists(p): files.append(p)
    files += glob.glob(os.path.join(site, 'archive', '2026.json'))
    files += glob.glob(os.path.join(site, 'archive', '2027.json'))
files += ['HANDOVER.md', 'sweep/otsused.json', 'data/dupe_ok.json']
txt = ''
for f in files:
    try: txt += open(f, encoding='utf-8').read() + '\n'
    except Exception as e: print('skip', f, e)
arc = open('HANDOVER-ARCHIVE.md', encoding='utf-8').read().splitlines()
txt += '\n'.join(arc[-3000:])
fb = sorted(set(re.findall(r'facebook\.com/events/(?:[^"\s)]*?/)?(\d{12,20})', txt)))
def b36(n):
    n = int(n); s = ''
    a = '0123456789abcdefghijklmnopqrstuvwxyz'
    while n: s = a[n % 36] + s; n //= 36
    return s
enc = ','.join(b36(i) for i in fb)
open('.swtmp/fbknown.txt', 'w').write(enc)
print('fb ids', len(fb), 'enc len', len(enc))
# other hosts: keep path keys
keys = defaultdict(set)
for m in re.finditer(r'https?://(?:www\.)?(fienta\.com|gateme\.com|piletilevi\.ee|piletitasku\.ee|piletikeskus\.ee|sviby\.com|ticketer\.ee|tourmotor\.net|ra\.co|bandcamp\.com|[a-z0-9-]+\.bandcamp\.com)(/[^"\s)<>\]]*)', txt):
    host, path = m.group(1), m.group(2).rstrip('/.,')
    keys[host].add(path.split('?')[0].split('#')[0])
for h, v in keys.items(): print(h, len(v))
json.dump({h: sorted(v) for h, v in keys.items()}, open('.swtmp/otherknown.json', 'w'), indent=0)
