"""Lista produktów flystore.pl z wysyłką w 24 godziny (dla kafli list w sklepie: „Darmowa dostawa jutro”).

Czyta feed Shopera dla Ceneo (CeneoV2), niczego w nim nie zmienia. avail="1" oznacza czas wysyłki 24 h
i stan > 0 (sprawdzone z API Shopera 11.11.2026: 976 z 976 zgodnych).
Wynik: wysylka-24h.json = {"t": czas feedu (Last-Modified, UTC), "ids": [id produktów]}.
Moduł 559 sklepu pomija plik starszy niż 26 h, więc gdy skrypt przestanie działać, kafle wracają do samego „Darmowa dostawa”.
"""
import datetime as dt
import email.utils
import json
import os
import re
import sys
import urllib.request

# Link z tokenem (Porównywarki cen) w sekrecie CENEO_URL; bez niego stary link, który działa do 27.01.2027.
CENEO_URL = os.environ.get("CENEO_URL", "").strip()
OLD_SOURCE = "https://flystore.pl/console/integration/execute/name/CeneoV2/lang/pl_PL"
MIN_IDS = 300


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "FlyStore-Wysylka24/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read().decode("utf-8"), r.headers.get("Last-Modified")


def main():
    try:
        xml, lm = fetch(CENEO_URL or OLD_SOURCE)
    except Exception as e:
        if not CENEO_URL:
            raise
        print(f"UWAGA: link z tokenem nie działa ({type(e).__name__}), biorę stary link")
        xml, lm = fetch(OLD_SOURCE)
    t = email.utils.parsedate_to_datetime(lm) if lm else dt.datetime.now(dt.timezone.utc)
    ids = sorted({int(m.group(1)) for m in re.finditer(r'<o id="(\d+)"[^>]*?\bavail="1"', xml)})
    if len(ids) < MIN_IDS:
        sys.exit(f"Za mało produktów z wysyłką 24 h: {len(ids)} - plik zostaje bez zmian")
    with open("wysylka-24h.json", "w", encoding="utf-8") as f:
        json.dump({"t": t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "ids": ids}, f, separators=(",", ":"))
    print(f"OK: {len(ids)} produktów z wysyłką 24 h, feed z {t:%Y-%m-%d %H:%M} UTC")


if __name__ == "__main__":
    main()
