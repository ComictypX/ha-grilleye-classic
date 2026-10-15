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

**Alle drei Jobs bestanden:** [Prüflauf 38804105992](https://github.com/ComictypX/ha-grilleye-classic/actions/runs/38804105992).
Geprüfter Code-Commit: `3b1d0c7aaeeb44ee7f726a8f407f445ebb842a32`.

- Ubuntu / Python 3.14.8 / Home Assistant **2026.10.1**.
- **20 Offline-Tests bestanden**, zusätzlich **7 echte HA-Frameworktests bestanden**.
- HA: Konfiguration, Bluetooth-Entdeckung, Duplikaterkennung, Sensorzustände,
  Timeout, Wiederempfang, unabhängiger Fühlerausfall, Entladen, Timeout-Validierung
  und Neuladen nach Optionsänderung. Der Funkempfang ist dabei simuliert.
- Beide Alarmbeispiele mit dem echten asynchronen HA-Konfigurationsvalidator geprüft.
- `pip check`, Ruff, HACS und hassfest: **erfolgreich**.

Die zusätzliche lokale Installation der Linux-Testabhängigkeiten war nicht freigegeben;
die echten Frameworktests wurden deshalb erfolgreich in GitHub Actions ausgeführt.
Der jeweils aktuelle Status ist unter [Actions](https://github.com/ComictypX/ha-grilleye-classic/actions) sichtbar.

## Noch praktisch abzunehmen

Keine Ende-zu-Ende-Abnahme an einem laufenden GrillEye/Shelly oder iPhone durchgeführt.
HA-Neustart, Shelly-Ausfall, konstante Temperaturen, Fühler abziehen und echte
hörbare Critical Notifications gemäß README testen. Die Interpretation `0`/`FFFF`
als unbrauchbarer Fühlerwert ist konservativ und noch nicht physisch bestätigt.
Ein grüner Softwaretest ersetzt diese Abnahme nicht.

