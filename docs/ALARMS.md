# Alarme komfortabel einrichten

Die Integration liefert Temperaturen; die **Alarmvorlage (Blueprint)** ergänzt
ein HA-Formular pro benötigtem Fühler. Sie funktioniert für jeden der sechs Kanäle.
Fühler 3–6 werden ab 0.2.1 bei einem gültigen positiven Messwert automatisch aktiviert;
manuell deaktivierte Kanäle bei Bedarf selbst wieder aktivieren. Die Vorlage steuert keinen Summer im
GrillEye: Hardwarealarme benötigen weiterhin einen anderen GATT-Verbindungsweg.

**Ein Alarm ersetzt niemals Aufsicht am Gasgrill.** Echte Funk- und Push-Zuverlässigkeit
müssen praktisch getestet werden. Ein Ausfall von HA selbst kann durch diese
Automation im selben HA nicht zuverlässig gemeldet werden.

## Einrichtung im HA-Formular

1. Unter Einstellungen → Geräte & Dienste → Helfer einen **Schalter** erstellen,
   beispielsweise „Grillüberwachung“. Dieser Schalter darf für alle Fühler gemeinsam
   verwendet werden. Bis zum Abschluss der Einrichtung ausgeschaltet lassen.
2. Pro benötigtem Fühler einen eigenen **Timer** erstellen, z. B. „Fühler 1 Alarmruhe“,
   mit Dauer **00:05:00** und aktivierter Wiederherstellung nach Neustart.
   Den Timer nicht zwischen Fühlern teilen.
3. Einstellungen → Automationen & Szenen → Blueprints → Blueprint importieren.
   Diese URL einfügen:

   `https://github.com/ComictypX/ha-grilleye-classic/blob/main/blueprints/automation/grilleye_probe_alarm.yaml`

4. Aus „GrillEye – Fühleralarm mit Alarmruhe“ eine Automation erstellen. Fühler,
   Empfang **desselben GrillEye**, Überwachungsschalter und den zugehörigen
   Alarmruhe-Timer auswählen. Unter-/Obergrenzen einzeln ein- oder ausschalten,
   Grenzwerte und Sensor-Anzeigeeinheit festlegen. Keine vorgegebenen sicheren
   Gar-/Brandtemperaturen: Werte passend zum eigenen Einsatz selbst wählen.
5. Alarmaktion wählen. Ohne Änderung entsteht eine **dauerhafte Meldung in HA**,
   keine Handy-Push-Nachricht. Wiederholungen aktualisieren dieselbe HA-Meldung
   pro Fühler; sie bleibt bis zum manuellen Verwerfen sichtbar.
6. Bei Bedarf für weitere Fühler wiederholen, jeweils mit eigenen Grenzen und Timer.
   Anschließend Grillüberwachung bewusst einschalten und alle Alarmwege testen.

HACS lädt die Custom-Integration. **Der Blueprint wird separat importiert**; ein
HACS-Update erzeugt keine Automationen, Helfer oder Benachrichtigungen in deinem HA.
Änderungen an Grenzen und Zielen erfolgen später im Blueprint-Automationsformular.
Zum Aktualisieren des Blueprints „Erneut importieren“ und Automationen neu laden.
Es werden keine vorhandenen Automationen automatisch ersetzt. Alte Beispielalarme
für dieselben Fühler deaktivieren, wenn sie sonst doppelte Meldungen erzeugen würden.

## Verhalten und Quittierung

- **Temperatur ≥ Obergrenze bzw. ≤ Untergrenze:** Alarm einschließlich Grenzwert.
  Einheitenwechsel wird erkannt: passt die angezeigte Einheit nicht mehr zur
  Formulareinstellung, folgt ein Konfigurationshinweis statt eines still falschen Vergleichs.
- **Empfang nicht `on`:** Empfangsalarm. Bei vollständigem Funkausfall erkennt die
  Integration das nach ihrem Empfangstimeout (Standard 120 s). Die Vorlage
  alarmiert auf den Statuswechsel; die zusätzliche Minutenprüfung fängt verpasste
  Ereignisse ab. Das ist keine sofortige physikalische GATT-Trennungserkennung.
- **Fühler unbekannt, nicht verfügbar oder nicht numerisch:** Fühleralarm; fehlende
  Daten werden nicht als null Grad interpretiert. Das Abziehverhalten bleibt durch
  die Nullwert-/Firmwareunsicherheit begrenzt: ein als gültig freigegebener Nullwert
  kann nicht unabhängig als fehlender Fühler erkannt werden.
- Neue Grenzübertritte, Empfangs-/Fühlerwechsel und Einschalten prüfen den aktuellen
  Zustand. Bei unverändertem Alarm wiederholt die Vorlage im gewählten Abstand
  von 1–60 Minuten. Die Minutenprüfung kann eine Wiederholung um bis zu 60 s
  verschieben. Neue Temperaturpakete innerhalb desselben Alarmbereichs erzeugen
  keine Meldung pro Paket. Grenzpendeln kann neue Alarme auslösen; keine Hysterese.
- **Quittieren = Alarmruhe-Timer starten.** Während `active` ruhen ausschließlich
  Temperaturmeldungen dieses Fühlers, auch bei erneutem Unter-/Obergrenzenalarm
  während derselben Ruhezeit. Empfangs-, Fühler- und Konfigurationsfehler melden
  sich weiterhin und wiederholen sich. Das ist keine dauerhafte Alarmabschaltung.
- Timer abgelaufen/abgebrochen: aktuelle Temperaturverletzung meldet sich wieder.
  Ein pausierter, unbekannter oder nicht verfügbarer Timer unterdrückt nichts.
  Bei Rückkehr in den normalen Temperaturbereich oder Ausschalten der Überwachung
  wird eine laufende Alarmruhe beendet; eine neue Grillsitzung beginnt ohne alte Ruhezeit.
- HA-Start und Automations-Neuladen prüfen bereits bestehende Alarmzustände erneut.
  Der Schalter-Helfer kann seinen Zustand wiederherstellen. War er eingeschaltet,
  läuft die Überwachung weiter. Der Timer soll seine Restzeit wiederherstellen;
  ist sie während des HA-Ausfalls abgelaufen, erfasst die Minutenprüfung den Zustand
  auch ohne ein nachträgliches `timer.finished`-Ereignis.
- Fühler mit deaktivierten Temperaturgrenzen bleiben auf Empfang-/Fühlerausfall
  überwacht. Bei zwei aktiven Grenzen muss Untergrenze < Obergrenze sein; andernfalls
  wird während aktiver Überwachung ein Konfigurationsalarm ausgegeben.

## iPhone: kritische Benachrichtigung

Im Feld „Alarmaktion / Benachrichtigungsziel“ die reale Companion-App-Aktion
deines iPhones auswählen. Beispiel für den YAML-Modus **dieses Aktionsfelds**:

```yaml
- action: notify.mobile_app_dein_iphone
  data:
    title: "{{ alarm_title }}"
    message: "{{ alarm_message }}"
    data:
      push:
        sound:
          name: default
          critical: 1
          volume: 1.0
```

Die Aktion kann auch eine andere Benachrichtigung oder ein eigenes Skript enthalten.
Verfügbare Variablen: `alarm_title`, `alarm_message`, `alarm_reason`, `alarm_probe`,
`alarm_temperature`, `alarm_unit`. `alarm_reason` ist `upper`, `lower`, `reception`,
`probe` oder `configuration`. Keine leere Aktion speichern: sonst wird nichts gemeldet.
Benachrichtigungsfehler stehen im Automationstrace; die Minutenprüfung versucht
bei fortbestehendem Zustand nach dem Wiederholungsintervall erneut auszulösen.

Auf dem iPhone Benachrichtigungen und kritische Hinweise für HA erlauben.
Echte Zustellung mit gesperrtem iPhone, Fokus/Lautlos, WLAN und Mobilfunk prüfen.
Ein simulierter Benachrichtigungsaufruf im Test beweist keinen Push-Empfang.

## Bedienkarte und Rückbau

[examples/alarm_controls.yaml](../examples/alarm_controls.yaml) liefert eine
zusätzliche manuelle Dashboard-Karte: Überwachung ein/aus, Alarmruhe starten,
Timerrestzeit anzeigen und Alarmruhe abbrechen. Tatsächliche Entity-IDs einsetzen.
Für weitere Fühler deren Timer mit eigenen Knöpfen ergänzen.

Zum Rückbau zuerst den Überwachungsschalter ausschalten, danach die aus diesem
Blueprint erstellten Automationen deaktivieren oder löschen. Die zusätzlich
angelegten Helfer und Karten können anschließend entfernt werden. Bestehende
GrillEye-Sensoren und andere Automationen müssen dafür nicht gelöscht werden.

## Praktische Abnahme

1. Grenzen vorübergehend so wählen, dass beide Vergleiche einschließlich Gleichheit
   sicher geprüft werden können. Keine gefährlichen Grilltemperaturen zum Test erzeugen.
2. Bereits überschrittenen Wert beim Einschalten und nach Automations-Neuladen prüfen.
3. Temperaturalarme quittieren: Ruhe und automatische Wiederaufnahme bestätigen.
4. Während der Alarmruhe Fühler abziehen und Gerät/Shelly ausschalten: Ausfallmeldung prüfen.
5. Mehrere Fühler: Timer eines Fühlers starten; andere müssen weiter melden.
6. Wiederempfang und neue Grillsitzung testen, anschließend echte Grenzwerte einstellen.

## Quellen

- [HA-Blueprint-Schema](https://www.home-assistant.io/docs/blueprint/schema/)
- [HA-Timer und Wiederherstellung](https://www.home-assistant.io/integrations/timer/)
- [iOS Critical Notifications](https://companion.home-assistant.io/docs/notifications/critical-notifications/)
