# GrillEye Classic: belegtes Protokoll und Integrationsentscheidungen

Grundlage: statische REA-Analyse der vom Nutzer bereitgestellten Android-APK
`qlnet.com.grilleye`, Version 2.0.0, Code 64.
SHA-256: `9f518332fc44ccecd0329c33e307383f486110cf6e2610fbd859ea2dc601b240`.
Keine App-/Firmwareausführung oder Funkaufzeichnung des GATT-Handshakes.
Die Herstellerherkunft wurde nicht über eine unabhängige Signaturprüfung bestätigt.
Diese Dokumentation enthält keine APK oder dekompilierten Herstellerquellen.

## Passive Werbung

Die Original-App liest Temperaturdaten sowohl aus Werbung als auch aus GATT.
Company-ID 0; beobachtete Payloadlänge 20 Bytes: Header 8 Bytes, dann sechs
Little-Endian int16 in Zehntel-°C. Die ersten zwei Headerbytes sind beobachtet
`0000`, danach steht in den Mitschnitten die MAC in lesbarer Reihenfolge.
Die Integration validiert dieses konkrete Format, auch wenn die App ihre
Kanalzahl aus der AD-Länge ableitet. Länge 20 ist eine bewusste Kompatibilitätsgrenze.

REA-Methode: `MyBbqBleService.j.onLeScan`, Evidence
`ev_f3072841f273943eb787cefd4798ba151b55bfbd8217e3da022ca1c827e73ddd`.
Signed-Decoder: `MyBbqBleService.a(byte[], int): short`, Überladung 4, Evidence
`ev_00f429e19fb46f85fe2778c3b9fa2d59ceedee363ef723d233ed9cc16010a46e`.

## Wertebereich und Verfügbarkeit

Die App verwendet Java Math.round nach Division durch 10 und prüft dann 1–300 °C,
ab Geräteversion 3.2 bzw. höherem Major 0–300 °C. Das ist die Version aus Antwort
`23`, nicht zwingend die separate Firmwarezeichenfolge aus `2A26`.
`FFFF` wird signed zu −1, also −0,1 °C; modern kann das nach Rundung 0 ergeben.
Ein expliziter `FFFF`-Sentinel ist in diesem Decoder nicht belegt.

Unsere Entscheidung: Rohbereich 0–3000 einschließlich, Zehntelgrad unverändert,
Nullwerte standardmäßig gefiltert und bewusst freischaltbar. Damit wird etwa
300,4 °C abgewiesen, obwohl die App es auf 300 °C runden kann. Werte unter 0 °C
werden auch dann nicht übernommen, wenn die App sie auf 0 runden würde.
Das ist eine Integrationsregel, keine behauptete exakte App-Nachbildung.
Ein gefilterter Kanal macht andere Kanäle nicht unverfügbar. Ein strukturell
gültiges Paket mit sechs ungültigen Kanälen bestätigt weiterhin den Funkempfang.
Ein fehlerhafter Rahmen hält den Empfang nicht künstlich aufrecht.

Fühler 3–6 sind zunächst deaktiviert, da nur Kanal 1/2 praktisch belegte Messungen
haben. Nullfilter abschalten ersetzt keinen Nachweis eines angeschlossenen Fühlers.
Der 120-s-Standardtimeout ist unsere Entscheidung; die App setzt im untersuchten
Ausfallpfad beim Start effektiv 20 s. Unveränderte Werte erneuern den HA-Timeout.

## Aktives GATT: dokumentiert, nicht implementiert

Alle kurzen UUIDs sind auf `0000xxxx-0000-1000-8000-00805f9b34fb` zu erweitern.

| UUID | App-Nutzung |
|---|---|
| FFF0 | Service |
| FFF1 | Notifications: Anmeldung, Version, Batterie, Alarmquittierung |
| FFF2 | Anmeldung schreiben, 15 Bytes |
| FFF4 | Temperatur-Notifications, je zwei Bytes pro Kanal ohne Advertising-Header |
| FFF5 | sechs Byte lange Steuerbefehle schreiben |
| 2902 | CCCD zum Aktivieren von Notifications, `01 00` |
| 180A / 2A26 | Device Information / Firmware Revision String |

Die App aktiviert zunächst FFF1-Notifications, schreibt Anmeldung nach erfolgreichem
CCCD und aktiviert später FFF4. Auf Anmeldungserfolg folgt eine Initialisierungsqueue.
Es gibt feste 15-Byte-Loginarrays; die Analyse belegt keine dynamische kryptografische
Challenge oder vollständige Pairing-/Verschlüsselungseigenschaften.

| FFF5-Befehlspräfix | untersuchte Verwendung |
|---|---|
| `01 ch lowLE highLE` | Schwellen in Zehntel-°C, Kanal 0–5 |
| `02 00` / `02 01` | Celsius / Fahrenheit gemäß UI-Pfad |
| `04 ch` / `04 FF` | Kanal-/Gesamtreset bzw. Quittierung; genaue Gerätewirkung offen |
| `08 23` | Geräteversion abfragen |
| `08 24` | Batterie abfragen |
| `0B 01` | Temperaturpfad aktivieren, aus Log/Initialisierung erschlossen |
| `FD 01 01 01` / `FD 01 00 01` | Gerätealarm ein/aus |
| `03 FF secondsLE` | Cooling-Time laut Log, Gerätewirkung offen |
| `12 03` | Initialisierung, Bedeutung offen |

Kurze Befehle sind auf sechs Bytes mit Null zu ergänzen. Diese Tabelle ist keine
Anleitung, ungeprüfte Befehle an ein laufendes Gerät zu senden. Die Integration
sendet keine GATT-Befehle. Batterieantwort `24` enthält zwei signed LE-Rohwerte;
die App verwendet eine skalierte Schwellwerttabelle, keine einfache Prozentdivision.
Ein Batteriefeld in der vorliegenden Werbung ist nicht belegt.

Shelly unterstützt über die offizielle HA-Integration Werbung, keine GATT-Proxy-
Verbindungen. Eine aktive Erweiterung wäre ein separates Transport-/Testprojekt.
[Shelly-Dokumentation](https://www.home-assistant.io/integrations/shelly/#bluetooth-support).

## Ausstehende Geräteabnahme

- Fühler 1–6 einzeln bestücken/abziehen und frische Rohwerte vergleichen.
- Nullwert mit kontrollierter Messung prüfen, Geräteversion und Firmware erfassen.
- Geräteeinheiten °C/°F wechseln und identische Rohdatenskalierung bestätigen.
- Timeout, Wiederempfang, Proxywechsel und HA-Neustart praktisch testen.
- Echte iOS-Push-Zustellung im Hintergrund, mit Fokus/Lautlos und Mobilfunk prüfen.

Ein Alarm ersetzt niemals Aufsicht am Gasgrill. Softwaretests beweisen keine
zuverlässige Funk-/Push-Zustellung.
