import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
files = {'www': 'data/manual.json', 'rap': 'rap/data/manual.json', 'klubi': 'klubi/data/manual.json'}
data = {k: json.load(open(v, encoding='utf-8')) for k, v in files.items()}
for kw in sys.argv[1:]:
    hits = []
    for k, arr in data.items():
        for e in arr:
            s = json.dumps(e, ensure_ascii=False).lower()
            if kw.lower() in s:
                hits.append('%s %s %s @ %s pu=%s' % (k, e.get('d'), e.get('n', '')[:60], e.get('v', ''), 'Y' if e.get('pu') else '-'))
    print('##', kw, '->', '; '.join(hits[:4]) if hits else 'PUUDUB')
