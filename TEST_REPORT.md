# Prüfstand – 15.10.2026

## Lokal ausgeführt

- Python 3.14.7: `python -m unittest discover -s tests/unit -v` – **20 Tests bestanden**.
- Beide bereitgestellten GrillEye-Pakete: **36,0/107,0 °C** und **32,0/108,0 °C**.
- Paketlängen, Präfix, eingebettete MAC, Little Endian, Zehntelgrad und unabhängige
  Fühlerverfügbarkeit geprüft.
- Empfangslogik mit HA-Boundary-Testdoubles: identische Pakete, Fehlerpakete, alte/
  doppelte Pakete, Timeout, Wiederempfang, Proxywechsel, Raw- statt historischer
  Manufacturer-Daten und Callback-/Timerbereinigung geprüft.
- Python-Dateien kompilieren; JSON und YAML erfolgreich eingelesen.

## GitHub Actions

Der Workflow prüft echte Home-Assistant-Frameworktests, Lint, HACS und hassfest.
Der jeweils aktuelle Status ist unter
[Actions](https://github.com/ComictypX/ha-grilleye-classic/actions) sichtbar.
Die zusätzliche lokale Installation der Linux-Testabhängigkeiten wurde nicht freigegeben;
deshalb stellen die lokalen Tests allein keinen echten HA-Lauf dar.

## Noch praktisch abzunehmen

Keine Ende-zu-Ende-Abnahme an einem laufenden GrillEye/Shelly oder iPhone durchgeführt.
HA-Neustart, Shelly-Ausfall, konstante Temperaturen, Fühler abziehen und echte
hörbare Critical Notifications gemäß README testen. Die Interpretation `0`/`FFFF`
als unbrauchbarer Fühlerwert ist konservativ und noch nicht physisch bestätigt.
Ein grüner Softwaretest ersetzt diese Abnahme nicht.
