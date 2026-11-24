p = 'postitused/2026-11-20-tulekul.md'
out = []
for ln in open(p, encoding='utf-8').read().split('\n'):
    try:
        f = ln.encode('cp1252').decode('utf-8')
        out.append(f)
    except Exception:
        out.append(ln)
open(p, 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
