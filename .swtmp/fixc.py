import json
for p in ['data/manual.json', 'rap/data/manual.json', 'klubi/data/manual.json']:
    d = json.load(open(p, encoding='utf-8'))
    n = 0
    for e in d:
        if e.get('lisatud') == '2026-11-20' and 'c' in e and e['c'] not in ('Tallinn', 'Tartu', 'mujal', 'Euroopa', 'Läti', 'Leedu', 'Soome', 'Rootsi'):
            e['linn'] = e['c']; e['c'] = 'mujal'; n += 1
        if e.get('n', '').startswith("Käbliku Beer Camp & Rock'N'Roll 2027") and 'linn' not in e:
            e['linn'] = 'Põlva'
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(p, n)
