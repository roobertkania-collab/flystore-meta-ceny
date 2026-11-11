# flystore-meta-ceny

Dodatkowy feed dla katalogu Meta (reklamy dynamiczne FlyStore.pl): cena z feedu sklepu rozbita na złote i grosze, żeby szablon reklamy pokazywał ją w formacie „4 599⁰⁰ zł”.

- `build.py` co godzinę (GitHub Actions) pobiera publiczny feed sklepu dla Meta i zapisuje `ceny-zl-gr.csv` (`id`, `custom_label_0` = złote, `custom_label_1` = grosze).
- `ostatnia_aktualizacja.txt` pokazuje, kiedy plik powstał. Starszy niż kilka godzin = zadanie nie działa.
- Meta czyta plik jako dodatkowe zestawienie: `https://raw.githubusercontent.com/roobertkania-collab/flystore-meta-ceny/main/ceny-zl-gr.csv`.

Dane w pliku to tylko numery produktów i ceny, publicznie widoczne w sklepie.

## Lista produktów z wysyłką 24 h (od 11.11.2026)
- `wysylka24.py` co godzinę pobiera feed sklepu dla Ceneo i zapisuje `wysylka-24h.json` (`t` = czas feedu UTC, `ids` = produkty z `avail="1"`, czyli wysyłka 24 h i stan > 0).
- Czyta go moduł 559 szablonu sklepu (kafle list: „Darmowa dostawa jutro”). Plik starszy niż 26 h moduł pomija.
- Adres: `https://raw.githubusercontent.com/roobertkania-collab/flystore-meta-ceny/main/wysylka-24h.json`.
