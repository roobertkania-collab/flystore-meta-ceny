# flystore-meta-ceny

Dodatkowy feed dla katalogu Meta (reklamy dynamiczne FlyStore.pl): cena z feedu sklepu rozbita na złote i grosze, żeby szablon reklamy pokazywał ją w formacie „4 599⁰⁰ zł”.

- `build.py` co godzinę (GitHub Actions) pobiera publiczny feed sklepu dla Meta i zapisuje `ceny-zl-gr.csv` (`id`, `custom_label_0` = złote, `custom_label_1` = grosze).
- `ostatnia_aktualizacja.txt` pokazuje, kiedy plik powstał. Starszy niż kilka godzin = zadanie nie działa.
- Meta czyta plik jako dodatkowe zestawienie: `https://raw.githubusercontent.com/roobertkania-collab/flystore-meta-ceny/main/ceny-zl-gr.csv`.

Dane w pliku to tylko numery produktów i ceny, publicznie widoczne w sklepie.
