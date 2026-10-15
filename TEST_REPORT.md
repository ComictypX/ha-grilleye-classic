# Prüfstand 0.2.1 – 16.10.2026

## Automatische Fühleraktivierung

25 lokale Parser-/Empfangstests bestehen unverändert. Zusätzliche echte HA-Tests prüfen
die Erkennung über frische positive Messwerte, den verzögerten HA-Reload mit
anschließender Anzeige unter unveränderten Entity-IDs, ignorierte Null-/Fehlerwerte,
manuelle/Device-/Config-Entry-Deaktivierungen, die Systemoption für neue Entitäten,
Abziehen, Neuladen und Entfernen des Listeners beim Entladen.
Der vollständige Prüflauf mit Release 0.2.1 wird nach Abschluss hier ergänzt.

## Historischer Prüfstand 0.2.0

## Veröffentlichung

**Release [v0.2.0](https://github.com/ComictypX/ha-grilleye-classic/releases/tag/v0.2.0)
ist veröffentlicht**, kein Entwurf und keine Vorabversion.
Tag und Manifest-Version wurden nach Veröffentlichung erneut geprüft.
Tag-Commit: `f9255de5fc28ea41f2f750960b78d1151fd1b36f`.

[Vollständiger Prüflauf inklusive Veröffentlichung](https://github.com/ComictypX/ha-grilleye-classic/actions/runs/38814030806):
**78 Tests bestanden** (25 Offline-, 42 HA- und 11 Release-Logiktests).
Ruff, pip check, HACS und hassfest sowie der anschließende Veröffentlichungsjob erfolgreich.
Die tatsächliche Updateanzeige in der Nutzerinstallation von HACS wurde nicht geprüft.

Die Release-Logik hat auch lokal **11 zusätzliche Tests bestanden**: exakter Commit,
Versions-/Changelog-Prüfung, erlaubter Branch/Ereignistyp, manuelle Wiederholung,
älterer Main-Stand, vorhandenes Release, Entwurf/Vorabversion, vorhandener Tag und API-Fehler.
Die CI führt diese Tests ebenfalls vor dem Veröffentlichungsjob aus.

## Alarm-Erweiterung

**32 zusätzliche Alarmtests bestanden**, mit echten HA-Automationen, Blueprint-
Schema/Substitution, Schalter-Helfern, Timern und gespeichertem Wiederherstellungszustand.
Benachrichtigungsziele und Temperatur-/Empfangsdaten werden simuliert.

- Inklusive Unter-/Obergrenzen, bereits verletzte Grenzen beim Einschalten und
  unveränderte/wechselnde Temperaturen ohne Paket-für-Paket-Benachrichtigungen.
- Wiederholungsabstand, Ende der Verletzung, Ausfall und Wiederempfang.
- Begrenzte Alarmruhe mit echtem Timerablauf; Empfangs-/Fühlerfehler trotz Alarmruhe.
- Unabhängige Alarmruhe bei zwei Fühlern, pausierter Timer, Ausschalten und neue
  Grillsitzung; Quittieren im ausgeschalteten Zustand kann die nächste Sitzung nicht stummschalten.
- HA-Start/Automations-Neuladen sowie wiederhergestellter Schalter und Timer,
  einschließlich während des HA-Ausfalls abgelaufener Alarmruhe.
- Fehlerhafte Grenzen, falsche Anzeigeeinheit, Fahrenheit, unbekannte und nicht
  numerische Werte, deaktivierte Temperaturgrenzen bei weiter aktiver Ausfallüberwachung.
- Echte dauerhafte HA-Meldung mit stabiler ID, erneuter Versuch bei simuliertem
  Benachrichtigungsfehler und gerenderter Critical-Push-Aufruf aus der Dokumentation.

## Lokal ausgeführt

- Python 3.14.7: **25 Offline-Tests bestanden**.
- Bekannte Funkpakete unverändert 36,0/107,0 °C und 32,0/108,0 °C.
- Alle 65.536 signed-16-Werte systematisch durch den echten Parser geprüft:
  Messbereich 0–300 °C, Zehntelgrad, unabhängiger zweiter Kanal.
- Alle sechs Kanalpositionen und unabhängiger Kanalausfall geprüft.
- Nullfilter an/aus, negative Werte, FFFF, 7FFF und obere Bereichsgrenze geprüft.
- Empfang: passive Registrierung, identische Temperaturen, Cache-Abgrenzung,
  fehlerhafte/alte/doppelte Pakete, Timeout, Wiederempfang, Proxywechsel und Cleanup.
- Ein formal gültiges Paket mit ungültigen Kanälen bestätigt den Empfang,
  macht jedoch keinen ungültigen Temperaturwert verfügbar.

## Vorheriger Alarm-/Parser-Prüflauf

**Alle drei Jobs bestanden:** [Prüflauf 38812929314](https://github.com/ComictypX/ha-grilleye-classic/actions/runs/38812929314).
Geprüfter Code-Commit: `d606011e83648bd8f93574368dfc88f77e638efd`.

- Ubuntu, Python 3.14.8, Home Assistant 2026.10.1.
- **25 Offline-Tests und 42 echte HA-Frameworktests bestanden**, zusammen **67 Tests**.
  Die 42 HA-Tests umfassen 32 Alarmtests und 10 bisherige Integrations-/Beispieltests.
- Optional aktivierte Kanäle, stabile Unique IDs, Rohwert-/Statusattribute,
  Nullwertoption, Reload, Timeout, Wiederempfang, Entdeckung und Entladen geprüft.
- Beide Alarmvorlagen mit dem echten HA-Konfigurationsvalidator geprüft.
- Ruff, pip check, HACS und hassfest: erfolgreich.

Die Diagnose liegt zusätzlich am dauerhaft verfügbaren Empfangssensor, da HA
zusätzliche Attribute nicht verfügbarer Temperatursensoren unterdrückt.

## Grenzen

Der Bluetooth-Empfang ist in Softwaretests simuliert. Der Nutzer hat für 0.1.0
bereits eine HA-Geräteseite mit Messwerten und laufenden Empfangszeitstempeln gezeigt.
Keine zusätzliche Hardware-/iOS-Abnahme von 0.2.0 durchgeführt.
Kanäle 3–6, Nullwerte und Abziehverhalten müssen am Gerät verglichen werden.
Die Diagnoseattribute unterstützen diese Prüfung; sie erkennen keinen
angeschlossenen Fühler unabhängig von dessen Rohwert.
Dashboard-Beispiel anhand offizieller Karten-Dokumentation erstellt;
keine automatische Installation oder visuelle Prüfung im Nutzer-Dashboard.
Softwaretests beweisen keine zuverlässige Funk-/Push-Zustellung. Die Alarmvorlage
muss separat importiert werden; es wurde keine laufende HA-Konfiguration verändert.
