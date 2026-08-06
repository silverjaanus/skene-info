# -*- coding: utf-8 -*-
"""Lokaalne arendusserver, mis jaljendab vercel.json marsruute.

MIKS SEE OLEMAS ON: tavaline `python -m http.server` EI naita peasaiti (www) oiges valguses.
Leht laeb `api/events.json`, mida juurkaustas failina EI OLE - Vercel suunab selle
`/feed/events.json` peale (vt build_api.py kommentaari: juurkausta api/ sees on Verceli
funktsioon, mistottu Vercel peidab kogu kausta staatilisest valjundist). Lokaalselt andis see
404 -> ALLX jai tuhjaks -> skoobi-chipid olid kinni ja peasait nagi katki valja, kuigi kood
oli korras. rap/ ja klubi/ tootasid, sest neil on paris failid rap/api/events.json jne.

Kasutus:
    python scripts/devserver.py [port]        # vaikimisi 8877
    -> http://127.0.0.1:8877/index.html       (www)
    -> http://127.0.0.1:8877/rap/index.html
    -> http://127.0.0.1:8877/klubi/index.html
"""
import sys, os, functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# vercel.json: {"src": "/api/(events|archive)\\.json", "dest": "/feed/$1.json"}
ROUTES = {
    "/api/events.json": "/feed/events.json",
    "/api/archive.json": "/feed/archive.json",
}


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        tee = self.path.split("?", 1)[0]
        if tee in ROUTES:
            self.path = ROUTES[tee]
        return SimpleHTTPRequestHandler.do_GET(self)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        SimpleHTTPRequestHandler.end_headers(self)

    def log_message(self, fmt, *args):
        pass  # vaikne


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8877
    srv = ThreadingHTTPServer(
        ("127.0.0.1", port),
        functools.partial(Handler, directory=ROOT),
    )
    print("skene.info dev server: http://127.0.0.1:%d/index.html" % port)
    print("marsruudid: " + ", ".join("%s -> %s" % kv for kv in ROUTES.items()))
    print("peatamiseks Ctrl+C")
    srv.serve_forever()
