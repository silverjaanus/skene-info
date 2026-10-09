"""Laupäevane Telegrami meeldetuletus: saadab Silverile tänase story-pildi.

Story pilt + ig/today.json tulevad Andmekorjest (make_ig_daily.py).
Env: TELEGRAM_BOT_TOKEN (repo secret), TELEGRAM_CHAT_ID.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tg(method, data):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    url = f"https://api.telegram.org/bot{token}/{method}"
    body = urllib.parse.urlencode(data).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=30) as r:
        res = json.load(r)
    if not res.get("ok"):
        sys.exit(f"Telegram viga: {res}")


def main():
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        sys.exit("TELEGRAM_BOT_TOKEN puudub")
    chat = os.environ.get("TELEGRAM_CHAT_ID") or "1810496014"
    tana = datetime.now(ZoneInfo("Europe/Tallinn")).date().isoformat()
    try:
        with open(os.path.join(ROOT, "ig", "today.json"), encoding="utf-8") as f:
            d = json.load(f)
    except OSError:
        d = {}
    story = d.get("story") if d.get("date") == tana else None
    if story and story.get("image_url"):
        tekst = ("📸 Laupäeva story: salvesta pilt ja pane Instagrami story'ks.\n"
                 "Lisa lingikleeps: skene.info/liitu")
        tg("sendPhoto", {"chat_id": chat, "photo": story["image_url"], "caption": tekst})
    else:
        tg("sendMessage", {"chat_id": chat,
                           "text": "📸 Laupäeva story: tänast pilti ei tekkinud (vaata Andmekorje logi)."})
    print("saadetud")


if __name__ == "__main__":
    main()
