# GrillEye Classic für Home Assistant

Passive Bluetooth-Custom-Integration für **GrillEye Classic**, mit HACS-Verzeichnisstruktur.
Empfängt Werbepakete über die Home-Assistant-Bluetooth-Integration, einschließlich
Shelly-Bluetooth-Proxys. Keine Kopplung, keine GATT-Verbindung, kein Cloudkonto.

**Ein Alarm ersetzt niemals die Aufsicht am Gasgrill.** Grill nicht unbeaufsichtigt
betreiben. Fühler, Funk, Shelly, WLAN, Home Assistant, Internet und iPhone können
ausfallen. Echte Push-Zuverlässigkeit muss mit dem eigenen Gerät getestet werden;
ein erfolgreicher Aktionstest in HA beweist noch keine hörbare Zustellung am iPhone.
Keine zertifizierte Brand-, Gas- oder Sicherheitsüberwachung, keine automatische Gasabschaltung.

## Installation mit HACS

Voraussetzung: **Home Assistant Core 2026.10.0 oder neuer**, HACS und ein aktivierter
Bluetooth-Empfänger. Die Integration verwendet die aktuelle API für jedes einzelne
Werbepaket. Ältere Core-Versionen werden nicht unterstützt.

1. In HACS → Menü → Benutzerdefinierte Repositories die Adresse
   `https://github.com/ComictypX/ha-grilleye-classic` eintragen, Typ **Integration**.
2. **GrillEye Classic** herunterladen; Home Assistant neu starten.
3. Einstellungen → Geräte & Dienste → Integration hinzufügen → **GrillEye Classic**.
   Bei automatischer Entdeckung die Einrichtung bestätigen.
4. Manuell die **GrillEye-MAC `40:06:A0:8B:40:01`** angeben. Die Proxy-MAC
   `D4:8A:FC:48:51:86` ist die Empfangsquelle, nicht die Geräteadresse.
5. Unter den Integrationsoptionen den Timeout nach Bedarf einstellen: 30–3600 s,
   Standard **120 s**. Nach dem Speichern wartet die Integration auf ein neues Paket.

Alternativ den Ordner `custom_components/grilleye_classic` aus diesem Repository nach
`/config/custom_components/grilleye_classic` kopieren und HA neu starten.
Es gibt keine YAML-Konfiguration der Integration. HACS-Installation und Integrationseinrichtung
sind zwei getrennte Schritte. Eine Aufnahme in die HACS-Standardliste ist nicht erforderlich.

### Shelly vorbereiten

Shelly über die offizielle Shelly-Integration einrichten. Ein geeignetes,
netzversorgtes Gen2+-Gerät verwenden und dessen Bluetooth-Scanner in den
Integrationsoptionen auf **Passiv** oder **Auto** stellen. Prüfen, dass HA die
GrillEye-Werbepakete sieht. Shelly leitet Werbung weiter, unterstützt jedoch keine
aktiven GATT-Verbindungen als Proxy. Diese Integration benötigt ausschließlich Werbung.
Der Scanner bleibt zentral von HA/Shelly verwaltet; es wird kein eigener Scanner gestartet.

## Entitäten

| Entität | Bedeutung |
|---|---|
| Fühler 1 / Fühler 2 | Temperatur, °C, 0,1 °C Auflösung; HA kann die Anzeigeeinheit umrechnen |
| Signalstärke | RSSI des zuletzt angenommenen Pakets, dBm; Diagnose, kein kalibrierter Abstand |
| Letztes gültiges Werbepaket | UTC-Zeitstempel; bleibt nach Empfangsausfall sichtbar |
| Empfang | `on` bei frischem gültigem Paket, sonst `off`; Bluetooth-Verbindungsklasse |

Die Entity-IDs hängen von Sprache und vorhandenen Namen ab. Die Automationbeispiele
verwenden angenommene IDs wie `sensor.grilleye_classic_4001_probe_1` und
`binary_sensor.grilleye_classic_4001_receiving`. **Alle IDs in den Beispielen mit
den tatsächlichen IDs unter Geräte & Dienste abgleichen und ersetzen.**
Unique IDs basieren auf Geräte-MAC und Messkanal; ein Wechsel des Proxys erzeugt keine
neuen Entitäten. Beim Empfangsstatus stehen Quelle (`source`) und Timeout als Attribute.

### Ausfallverhalten

- Start ohne empfangenes Live-Paket: Temperaturen/RSSI `unavailable`, Empfang `off`,
  letzter Empfang `unknown`. Alte HA-Zustände werden nicht als frische Messung übernommen.
- Nach 120 s ohne gültiges Paket: Temperaturen/RSSI `unavailable`, Empfang `off`.
  Eine fehlerhafte Nachricht setzt den Timeout nicht zurück. Ein neues gültiges Paket stellt
  die Verfügbarkeit wieder her. Unveränderte gültige Temperaturpakete halten sie aufrecht.
- Fühlerwert `0000` oder `ffff`: nur dieser Fühler `unavailable`; der andere bleibt messbar.
  **Die Sentinel-Bedeutung ist eine vorsichtige Annahme und noch nicht am ausgesteckten
  Fühler nachgewiesen.** Ein echter Wert 0,0 °C wird deshalb ebenfalls unterdrückt.
- „BLE-Verbindungsabbruch“ bedeutet hier **Ausbleiben gültiger Werbung**. Es gibt keine
  aktive BLE-Verbindung, deren Trennung direkt gemeldet werden könnte. Ein HA-Ausfall
  selbst kann durch eine Automation im selben HA nicht gemeldet werden.
- Wenn der Backend-Treiber `raw` liefert, wird ausschließlich das aktuelle Paket geprüft.
  Ohne `raw` nutzt die Integration die von HA zusammengeführten Manufacturer-Daten;
  dabei lässt sich ein vom Backend weitergereichter älterer Teilwert nicht sicher erkennen.
  Diesen Fall bei der Abnahme beachten. RSSI/Quelle zeigen den zuletzt angenommenen
  Empfang, nicht eine garantierte Auswahl des stärksten Proxys.

## Alarm-Automationen und iOS Critical Notifications

Die Dateien unter [examples](examples) sind **Vorlagen für jeweils eine neue Automation
im UI-YAML-Editor**, keine automatische Änderung deiner laufenden HA-Konfiguration.

Zuerst unter Einstellungen → Geräte & Dienste → Helfer erstellen:

| Helfer | Vorgeschlagene Entity-ID | Zweck |
|---|---|---|
| Schalter | `input_boolean.grilleye_alarm_aktiv` | Bewusst nur für eine beaufsichtigte Grillsitzung aktivieren |
| Zahl | `input_number.grilleye_zieltemperatur` | Persönlicher Grenzwert für Fühler 1 |
| Zahl | `input_number.grilleye_maximaltemperatur` | Persönlicher oberer Grenzwert für Fühler 2 |

Die Zahlenhelfer mit einem zum Fühler passenden Bereich und der **gleichen Einheit wie
die angezeigten Temperatursensoren** konfigurieren. Grenzwerte selbst passend zum
Grill und Grillgut festlegen; die Integration gibt keine sicheren Gar- oder Brandgrenzen vor.
Fühler 1 wird im Beispiel als Kerntemperatur, Fühler 2 als Garraumtemperatur verwendet.

- [Temperaturalarm](examples/temperature_alarm.yaml): solange aktiviert, jede Minute
  prüfen und bei **strikter Überschreitung** eines Grenzwerts erneut alarmieren.
  Das erfasst auch bereits überschrittene Werte beim Einschalten oder nach Neustart/
  Wiederempfang. Es ist keine reine Schwellenübertrittserkennung. Verzögerung bis 60 s.
- [Empfang-/Fühleralarm](examples/reception_alarm.yaml): Empfang aus, Messwert unbekannt
  oder nicht verfügbar. Meldet bei Statuswechsel und wiederholt minütlich, auch nach
  Neustart. Bei vollständigem Funkausfall normalerweise nach Timeout, spätestens plus
  Prüfintervall. Entferne die Prüfung eines Fühlers nur, wenn du ihn bewusst nicht nutzt.

`notify.mobile_app_dein_iphone` durch die reale Benachrichtigungsaktion deiner
HA-Companion-App ersetzen. Auf dem iPhone Benachrichtigungen **und kritische Hinweise**
für Home Assistant erlauben. Das Beispiel nutzt `push.sound.critical: 1` und Lautstärke
`1.0`. Kritische Hinweise können Lautlos und Fokus übergehen; dies muss auf dem konkreten
iPhone, ggf. auch mit Apple Watch, praktisch geprüft werden.
Die Beispiele wiederholen absichtlich, solange der Zustand anhält. Überwachung nach der
Grillsitzung ausschalten. Wird der Helferzustand beim Neustart wiederhergestellt, kann der
Alarm ohne erneutes Einschalten weiterlaufen. Er verschickt bei fehlenden Messwerten
einen Ausfallhinweis und wertet diese nicht als Temperatur 0 aus.

### Abnahmetest vor Nutzung

1. Beide Anzeigen am GrillEye mit HA vergleichen, auch bei wechselnden Temperaturen.
2. Temperatur zehn Minuten konstant lassen: Empfang muss aktiv bleiben.
3. Fühler nacheinander abziehen und Rohpakete dokumentieren; Sentinel-Annahme prüfen.
4. GrillEye ausschalten: nach Timeout Empfang aus, Temperaturen nicht verfügbar;
   mit aktiviertem Alarm muss die Ausfallnachricht hörbar eintreffen.
5. Shelly vom Strom trennen, WLAN-Verbindung unterbrechen, danach Wiederempfang prüfen.
   Bei mehreren Proxys darf ein anderer den Empfang übernehmen.
6. iPhone sperren, Lautlos/Fokus einschalten, im WLAN und über Mobilfunk jeweils
   Testbenachrichtigung sowie beide echten Alarmwege auslösen. Empfang und Ton bestätigen.
7. HA neu starten und Alarm bei bereits überschrittenem Grenzwert sowie ohne Empfang testen.
   HA-Strom-/Host-/Internetausfall benötigt eine unabhängige Überwachung.

## Protokoll und bestätigte Beispiele

Die **20 Bytes** von `manufacturer_data[0]` enthalten nicht mehr die zweiby­tige
BLE-Company-ID. Layout relativ zu diesem Wert:

| Bytes (ab 0) | Interpretation |
|---|---|
| 0–1 | beobachtetes Präfix `0000` |
| 2–7 | Geräte-MAC in dargestellter Reihenfolge |
| 8–9 | Fühler 1, Little-Endian `uint16`, geteilt durch 10 |
| 10–11 | Fühler 2, Little-Endian `uint16`, geteilt durch 10 |
| 12–19 | unbekannt; keine erfundenen Batterie-/Fühlerwerte |

| Herstellerdaten | Fühler 1 | Fühler 2 |
|---|---:|---:|
| `00004006a08b400168012e040000000000000000` | 36,0 °C | 107,0 °C |
| `00004006a08b4001400138040000000000000000` | 32,0 °C | 108,0 °C |

Die Integration ist auf diese beobachtete Classic-Variante begrenzt. Andere Modelle,
Firmwarevarianten, zusätzliche Kanäle, Batteriestand und negative Temperaturen sind
nicht nachgewiesen. Unplausible hohe Zahlen werden nicht durch frei erfundene
Grenzen weggefiltert. Die Aussagekraft hängt vom bestätigten Paketformat ab.

## Entwicklung und Tests

Offline ohne zusätzliche Pakete:

```sh
python -m unittest discover -s tests/unit -v
```

Frameworktests unter Linux mit Python 3.14:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-test.txt
pip check
ruff check .
pytest -q
```

`tests/unit` prüft die echten Parser-/Empfangsfunktionen; am HA-Rand werden kleine
Testdoubles verwendet. `tests/ha` prüft echte Config-Flows, Entitäten, Timeout,
Wiederempfang, Optionen und Entladen mit dem Home-Assistant-Testframework. Nur der
Bluetooth-Empfang wird dort simuliert. GitHub Actions ergänzt HACS und hassfest.
Ein grüner CI-Lauf belegt keine Hardware-/iOS-Zustellung; siehe Abnahmetest.
Letzter lokaler Prüfstand und verbleibende Grenzen: [TEST_REPORT.md](TEST_REPORT.md).

## Quellen

- [HA Bluetooth APIs](https://developers.home-assistant.io/docs/core/bluetooth/api/)
- [Connectable und non-connectable Controller](https://developers.home-assistant.io/docs/bluetooth/)
- [Shelly Bluetooth Support](https://www.home-assistant.io/integrations/shelly/#bluetooth-support)
- [HACS Integrationsanforderungen](https://www.hacs.xyz/docs/publish/integration/)
- [iOS Critical Notifications](https://companion.home-assistant.io/docs/notifications/critical-notifications/)

MIT-Lizenz. Unabhängiges Community-Projekt, keine offizielle GrillEye-Integration.
