#!/usr/bin/env python3
"""Kontrollib, et vercel.json Content-Security-Policy lubab koiki valisaadresse,
kuhu saidi lehed brauserist poorduvad.

07.10.2026: 28.08 lisatud CSP connect-src ei sisaldanud assets.mailerlite.com-i ->
uudiskirjaga liitumine oli 6 nadalat vaikselt katki (Tarvo teade). See kontroll
oleks selle pushi hetkel kinni puudnud.

Mida vaatab (koik *.html repos, v.a data/ ja node_modules/):
  fetch("https://..."), fetch(MUUTUJA) kus MUUTUJA="https://...",
  navigator.sendBeacon, XMLHttpRequest .open, new EventSource/WebSocket -> connect-src
  <form action="https://...">                                        -> form-action
  <script src="https://...">                                          -> script-src

Jooksuta:  python scripts/check_csp.py
Valjumiskood 1, kui moni host pole lubatud. Paranda vercel.json-i CSP rida.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"data", "node_modules", ".git", "templates"}

URL = r"""(['"`])(https?://[^'"`\s]+)\1"""
RE_FETCH_LIT = re.compile(r"\bfetch\(\s*" + URL)
RE_FETCH_VAR = re.compile(r"\bfetch\(\s*([A-Za-z_$][\w$]*)\s*[,)]")
RE_OTHER = re.compile(r"(?:sendBeacon|new\s+EventSource|new\s+WebSocket)\(\s*" + URL)
RE_XHR = re.compile(r"\.open\(\s*(['\"])[A-Z]+\1\s*,\s*" + URL)
RE_FORM = re.compile(r"<form\b[^>]*\baction=(['\"])(https?://[^'\"]+)\1", re.I)
RE_SCRIPT = re.compile(r"<script\b[^>]*\bsrc=(['\"])(https?://[^'\"]+)\1", re.I)


def load_csp(path):
    cfg = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    for route in cfg.get("routes", []):
        csp = (route.get("headers") or {}).get("Content-Security-Policy")
        if csp:
            out = {}
            for part in csp.split(";"):
                bits = part.split()
                if bits:
                    out[bits[0]] = bits[1:]
            return out
    return None


def allowed(host, sources):
    for s in sources:
        h = urlparse(s).hostname if "://" in s else None
        if not h:
            continue
        if h == host or (h.startswith("*.") and host.endswith(h[1:])):
            return True
    return False


def targets(txt):
    """Tagastab (direktiiv, url) paarid."""
    out = []
    for m in RE_FETCH_LIT.finditer(txt):
        out.append(("connect-src", m.group(2)))
    for m in RE_FETCH_VAR.finditer(txt):
        name = re.escape(m.group(1))
        d = re.search(r"\b" + name + r"\s*=\s*" + URL, txt)
        if d:
            out.append(("connect-src", d.group(2)))
    for rx in (RE_OTHER,):
        for m in rx.finditer(txt):
            out.append(("connect-src", m.group(2)))
    for m in RE_XHR.finditer(txt):
        out.append(("connect-src", m.group(3)))
    for m in RE_FORM.finditer(txt):
        out.append(("form-action", m.group(2)))
    for m in RE_SCRIPT.finditer(txt):
        out.append(("script-src", m.group(2)))
    return out


def main():
    # valikuline argument: muu vercel.json (testimiseks, nt vana versioon)
    csp = load_csp(sys.argv[1] if len(sys.argv) > 1 else ROOT / "vercel.json")
    if not csp:
        print("CSP: vercel.json-ist Content-Security-Policy paist ei leitud")
        return 1
    vigu, nahtud = 0, set()
    for f in sorted(ROOT.rglob("*.html")):
        if SKIP & set(f.relative_to(ROOT).parts):
            continue
        txt = f.read_text(encoding="utf-8", errors="replace")
        for direktiiv, url in targets(txt):
            host = urlparse(url).hostname
            if not host or host == "skene.info" or host.endswith(".skene.info"):
                continue
            src = csp.get(direktiiv) or csp.get("default-src") or []
            key = (direktiiv, host)
            if key in nahtud:
                continue
            nahtud.add(key)
            if not allowed(host, src):
                print(f"CSP VIGA {f.relative_to(ROOT)}: {direktiiv} ei luba {host} ({url})")
                vigu += 1
    if vigu:
        print(f"\n{vigu} host(i) blokeeritud. Lisa need vercel.json CSP vastavasse direktiivi.")
        return 1
    print(f"CSP OK: {len(nahtud)} valist sihti, koik lubatud")
    return 0


if __name__ == "__main__":
    sys.exit(main())
