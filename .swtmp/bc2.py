import glob
U = """mahtrarecords.bandcamp.com/album/khattra-tapes beyondtartu.bandcamp.com/album/palja-silmaga-n-htav fuzzolini.bandcamp.com/album/beauty-exists-in-everyone-2 fuzzolini.bandcamp.com/track/born-to-burn townflesh.bandcamp.com/album/the-town-flesh-extended-play townflesh.bandcamp.com/track/theres-a-last-time-for-everything-2 mangont.bandcamp.com/album/k-lmav-rinad seksound.bandcamp.com/album/club-ghost seksound.bandcamp.com/track/forever-far-single hidden-harmony.bandcamp.com/album/friends-to-keep-silence-with hidden-harmony.bandcamp.com/album/whispering-ln-vol-ii""".split()
txt = ''
for f in glob.glob('data/*.json') + glob.glob('*/data/*.json') + glob.glob('data/archive/*.json') + glob.glob('*/data/archive/*.json'):
    try: txt += open(f, encoding='utf-8').read().lower()
    except Exception: pass
for u in U: print('ok ' if u in txt else 'UUS', u)
