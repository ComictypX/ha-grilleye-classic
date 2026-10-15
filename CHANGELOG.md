# Änderungen

## 0.2.1

- Fühler 3–6 werden beim ersten gültigen positiven Live-Messwert automatisch aktiviert.
- HA übernimmt dies durch verzögertes Neuladen; bis zum nächsten Live-Paket können Werte kurz unverfügbar sein.
- Manuelle Deaktivierungen und die HA-Einstellung „Neue Entitäten deaktivieren“ bleiben erhalten.
- Nullwerte und ungültige/veraltete Pakete aktivieren keinen zusätzlichen Kanal.
- Einmal erkannte Fühler bleiben für Verlauf und Ausfallalarme aktiviert, auch nach Abziehen/Neustart.

## 0.2.0

- Versionierte GitHub-Releases für HACS; automatische Veröffentlichung erst nach grünen Prüfungen.
- Importierbare Alarmvorlage für jeden Fühler mit individuellen inklusiven Unter-/Obergrenzen,
  Benachrichtigungsziel, Wiederholung und begrenzter Alarmruhe. Ausfallfehler bleiben aktiv.
- Bedienkarte, Einrichtungsanleitung und echte HA-Verhaltenstests der Alarme ergänzt.
- Sechs signed Temperaturfelder nach statischer REA-Analyse statt zwei unsigned Feldern.
- Fühler 3–6 optional aktivierbar; vorhandene Geräte-/Sensoridentitäten bleiben erhalten.
- Expliziter Messbereich 0–300 °C mit Zehntelgrad; Nullwerte separat freischaltbar.
- Rohwert und Filterstatus pro Fühler für die praktische Abnahme sichtbar.
- Deutsch/Englisch, Protokollbelege, Updatehinweise und Live-Dashboard-Beispiel ergänzt.
- Passive Shelly-Unterstützung, Empfangsfrist und Alarm-Automationen beibehalten.

## 0.1.0

- Erste passive Integration mit Fühler 1/2, Empfangsdiagnose und HACS-Struktur.
