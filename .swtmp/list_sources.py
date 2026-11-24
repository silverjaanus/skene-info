import json, sys
s = json.load(open('sweep/sources.json', encoding='utf-8'))
out = []
def walk(o, p=''):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, list):
                for e in v:
                    if isinstance(e, dict):
                        out.append({'sek': p + k, 'nimi': e.get('nimi') or e.get('zanr') or '', 'url': e.get('url', ''), 'nb': (e.get('nb') or '')[:80]})
            elif isinstance(v, dict):
                walk(v, p + k + '.')
walk(s)
json.dump(out, open('.swtmp/sources_flat.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
for i, e in enumerate(out):
    print(i, e['sek'], '|', e['nimi'][:30], '|', e['url'])
