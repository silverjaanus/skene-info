import re
p = 'HANDOVER.md'; a = 'HANDOVER-ARCHIVE.md'
t = open(p, encoding='utf-8').read()
NOTE = ("**Postkastijooks 22.11.2026: 1 kiri (kontaktivorm-spämm „Ford“, ainult märgitud) + kluub.ee Tallinn (samm 2c; skriptiga 429, loetud brauseriga). +3 www, +1 klubi, 1 rikastus, 4 UUT OTSUSTUSPUNKTI.** "
        "**CI:** Andmekorje 22.11 punane — check_bandcamp.py: uus album Rein Fuks «Ma tegin ju nalja» (Seksound) → otsustuspunkt, URL lisatud bandcamp_seen.json-i (CI roheliseks). "
        "**PUSH PARANDATUD:** 21.11 kaks lokaalset commitit olid rebase'is konfliktis (genereeritud feed/klubi/rap api/events.json → võetud upstream, regenereeritud) ja `.swtmp/` oli kogemata commitis (eemaldatud indeksist). "
        "git-credential-manager'i salvestatud GitHubi sisselogimine on ikka katki; push õnnestus ühekordse `git -c credential.helper= -c \"credential.helper=!gh auth git-credential\" push` abil (gh CLI on sisse logitud). Püsiv parandus Silverilt: GitHubi sisselogimine Git Credential Manageris uuendada. "
        "**+www:** Jimi Hendrix 84 I/II/III kontsert: Ukaredad, Vaiglad, Lillepea — 26./27./28.11 Philly Joe's (kluub.ee + FB event + Piletikeskus https://piletikeskus.ee/et/e/7nhiuj ; rock+bluus, CryBaby-pretsedent). "
        "**+klubi:** Baile do Lainão — The BreakOut 27.11 Uus Laine (tasuta; kluub.ee + FB https://www.facebook.com/events/2129740374388798 ; vol IV pretsedent). **Rikastus:** Likane Leppäne 26.11 → hind 5/8 €. "
        "**Otsustuspunktid [UUS]:** Rein Fuks reliis · GØK2 & Luka 27.11 Terminal · Lasten Hautausmaa Duo + Nova Lux + Riste 28.11 Anemon12 · Bar IDA: Plastik 27.11. "
        "**VÄLJA (vaikselt):** All In at Studio 27.11 (house/pop/R&B, Metaxa-kommertspidu), Klämmar: Elina Born 28.11 Fonoteek (peavoolupopp), Best Of 2010s D3, Off Campus / Staarid puldis @ Suhe, viktoriinid/bingo. Ülejäänud skoobis olevad (Wyatt E., Sonic Death, Burn Still, Chelsea Wolfe, Pulsation, MÜRK, Compress Rave, Stereo, Saaremets, G5, Moz, madeleine3000, Masta Robusta) juba sees.\n")
marker = '### Varem valja jaetud / jalgimisel (info, otsust ei vaja)\n\n'
assert marker in t
t = t.replace(marker, marker + NOTE, 1)
# move oldest daily notes (10.11, 11.11, 12.11) to archive verbatim
moved = []
for day in ['12.11.2026', '11.11.2026', '10.11.2026']:
    m = re.search(r'\*\*Postkastijooks ' + re.escape(day) + r'.*?\n\n', t, flags=re.S)
    if m:
        moved.append(m.group(0)); t = t[:m.start()] + t[m.end():]
open(p, 'w', encoding='utf-8').write(t)
with open(a, 'a', encoding='utf-8') as f:
    f.write('\n\n## Kärbe 2026-11-22 (postkastijooks)\n\n' + ''.join(reversed(moved)))
print('moved', len(moved), 'lines now', t.count('\n'))
