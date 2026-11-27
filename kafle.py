"""Oceny i parametry na kafle list produktów flystore.pl (blok CT szablonu, test 50/50 od 27.11.2026).

Wynik: kafle.json = {"t": czas UTC, "o": {"id": [ocena x 10, liczba opinii]}, "p": {"id": [waga, klasa, czas lotu]}}.
- "o": oceny z TrustMate (te same co na karcie produktu), tylko produkty z co najmniej jedną opinią.
  Co godzinę odświeżamy 1/24 produktów (id % 24 == godzina UTC), więc każdy produkt raz na dobę.
  Pierwszy raz (brak kafle.json) albo z FULL=1 odświeżamy wszystkie.
- "p": parametry dronów z kafle-parametry.json (wysyła go komputer w firmie: parametry_dronow.py z API Shopera).
Lista produktów: feed Meta, który build.py i tak pobiera. Produkty spoza feedu wypadają z pliku.
Błąd TrustMate dla produktu = zostaje stara ocena. Gdy w porcji było >= 10 ocen, a teraz jest 0, zostaje cała stara porcja.
Moduł 559 sklepu pomija plik starszy niż 7 dni, więc gdy automat stanie, kafle wracają do obecnego wyglądu.
"""
import concurrent.futures as cf
import datetime as dt
import json
import os
import re
import time
import urllib.request

WIDGET = "https://trustmate.pro/en/widget/api/df1d0c0c-1520-432e-ac20-2a9ac051973c/html?language=pl&product="
WZOR = re.compile(r'"ratingValue"\s*:\s*"?([\d.,]+)"?\s*,\s*"reviewCount"\s*:\s*"?(\d+)')
PLIK, PARAMETRY = "kafle.json", "kafle-parametry.json"
MIN_ID = 1000
BRAK = object()  # błąd pobrania: zostaje stara wartość


def ocena(pid):
    url = WIDGET + pid
    for proba in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "kafle-oceny/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                html = r.read().decode("utf-8", "replace")
            m = WZOR.search(html)
            if not m:
                return None  # produkt bez opinii
            wartosc, ile = float(m.group(1).replace(",", ".")), int(m.group(2))
            return [int(round(wartosc * 10)), ile] if ile > 0 else None
        except Exception:
            time.sleep(1 + proba)
    return BRAK


def wczytaj(sciezka):
    try:
        with open(sciezka, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main(xml):
    ids = sorted({int(m.group(1)) for m in re.finditer(r"<entry>.*?<id>\s*(\d+)\s*</id>", xml, re.S)})
    if len(ids) < MIN_ID:
        print(f"UWAGA kafle: za mało produktów w feedzie ({len(ids)}), plik bez zmian")
        return
    stary = wczytaj(PLIK)
    oceny = {k: v for k, v in (stary.get("o") or {}).items()}
    teraz = dt.datetime.now(dt.timezone.utc)
    pelny = os.environ.get("FULL") == "1" or not stary
    porcja = [str(i) for i in ids if pelny or i % 24 == teraz.hour]
    start = time.time()
    with cf.ThreadPoolExecutor(max_workers=3) as pula:
        wyniki = dict(zip(porcja, pula.map(ocena, porcja)))
    bledy = sum(1 for v in wyniki.values() if v is BRAK)
    nowe = {k: v for k, v in wyniki.items() if v is not BRAK and v}
    stare_w_porcji = sum(1 for k in porcja if k in oceny)
    if stare_w_porcji >= 10 and not nowe:
        print(f"UWAGA kafle: TrustMate nie dał żadnej oceny dla porcji ({len(porcja)} produktów, błędów {bledy}), zostają stare")
    else:
        for k, v in wyniki.items():
            if v is BRAK:
                continue
            if v:
                oceny[k] = v
            else:
                oceny.pop(k, None)
    w_feedzie = {str(i) for i in ids}
    oceny = {k: v for k, v in oceny.items() if k in w_feedzie}
    parametry = wczytaj(PARAMETRY).get("p") or (stary.get("p") or {})
    dane = {"t": teraz.strftime("%Y-%m-%dT%H:%MZ"), "o": oceny, "p": parametry}
    with open(PLIK, "w", encoding="utf-8", newline="\n") as f:
        json.dump(dane, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    print(f"OK kafle: porcja {len(porcja)}{' (pełna)' if pelny else ''}, z opiniami {len(nowe)}, błędów {bledy}, "
          f"razem z opiniami {len(oceny)}, dronów {len(parametry)}, {time.time() - start:.0f} s, "
          f"{os.path.getsize(PLIK) / 1024:.1f} KB")
