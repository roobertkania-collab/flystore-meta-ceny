"""Dodatkowy feed dla katalogu Meta: cena rozbita na złote i grosze (do szablonu reklamy z ceną „4 599⁰⁰ zł”).

Czyta feed Shopera dla Meta (FacebookCatalogFeed), niczego w nim nie zmienia.
Wynik: ceny-zl-gr.csv z kolumnami id, custom_label_0 (złote), custom_label_1 (grosze)
i ostatnia_aktualizacja.txt z czasem wygenerowania.
Cena obowiązująca: promocyjna (sale_price), jeśli dziś mieści się w sale_price_effective_date, inaczej zwykła.
"""
import csv
import datetime as dt
import os
import re
import sys
import urllib.request

# Link z tokenem z panelu Shopera (Porównywarki cen) trzymany w sekrecie FEED_URL, bo repo jest publiczne.
# Stary link bez tokena działa do 27.01.2027 i do tego czasu jest zapasem.
FEED_URL = os.environ.get("FEED_URL", "").strip()
OLD_SOURCE = "https://flystore.pl/console/integration/execute/name/FacebookCatalogFeed/lang/pl_PL"
MIN_ROWS = 1000


def tag(entry, name):
    m = re.search(rf"<{name}>\s*(.*?)\s*</{name}>", entry, re.S)
    return m.group(1) if m else None


def split_price(raw):
    m = re.fullmatch(r"(\d+)(?:\.(\d{1,2}))?\s*PLN", raw or "")
    if not m:
        return None
    zl = f"{int(m.group(1)):,}".replace(",", " ")
    gr = (m.group(2) or "0").ljust(2, "0")
    return zl, gr


def effective_price(entry, now):
    price, sale = tag(entry, "price"), tag(entry, "sale_price")
    if not sale:
        return price
    rng = tag(entry, "sale_price_effective_date")
    if rng and "/" in rng:
        start, end = (dt.datetime.fromisoformat(s) for s in rng.split("/", 1))
        if not start <= now <= end:
            return price
    return sale


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "FlyStore-Meta-Ceny/1.0"})
    return urllib.request.urlopen(req, timeout=180).read().decode("utf-8")


def load_feed():
    if FEED_URL:
        try:
            xml = fetch(FEED_URL)
            print("Źródło: link z tokenem (sekret FEED_URL)")
            return xml
        except Exception as e:
            print(f"UWAGA: link z tokenem nie działa ({type(e).__name__}), biorę stary link")
    else:
        print("UWAGA: brak sekretu FEED_URL, biorę stary link (działa do 27.01.2027)")
    return fetch(OLD_SOURCE)


def main():
    xml = load_feed()
    now = dt.datetime.now(dt.timezone.utc)
    rows = []
    for entry in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        pid, p = tag(entry, "id"), split_price(effective_price(entry, now))
        if pid and p:
            rows.append((pid, *p))
    if len(rows) < MIN_ROWS:
        sys.exit(f"Za mało produktów w feedzie: {len(rows)} - plik zostaje bez zmian")
    with open("ceny-zl-gr.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["id", "custom_label_0", "custom_label_1"])
        w.writerows(rows)
    with open("ostatnia_aktualizacja.txt", "w", encoding="utf-8") as f:
        f.write(f"{now:%Y-%m-%d %H:%M} UTC, produktów: {len(rows)}\n")
    print(f"OK: {len(rows)} produktów")


if __name__ == "__main__":
    main()
