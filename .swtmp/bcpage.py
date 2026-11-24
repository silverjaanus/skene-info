import re, sys, html, urllib.request, json
url = sys.argv[1]
h = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})).read().decode('utf8')
for m in re.findall(r'<meta (?:property|name)="(og:[a-z]+|description)" content="([^"]*)"', h):
    print(m[0], '=', html.unescape(m[1]))
t = re.sub(r'<script.*?</script>|<style.*?</style>', '', h, flags=re.S)
t = html.unescape(re.sub(r'<[^>]+>', ' ', t))
t = re.sub(r'\s+', ' ', t)
for key in ['released', 'credits', 'tags']:
    i = t.find(key)
    if i >= 0:
        print('---', key, ':', t[max(0, i-200):i+600])
for m in re.findall(r'"datePublished":"([^"]+)"', h):
    print('datePublished', m)
