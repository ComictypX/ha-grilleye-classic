# Veröffentlichungen und HACS-Updates

Dieses Projekt verwendet veröffentlichte GitHub-Releases mit stabilen Versionsnamen
wie `v0.2.0`. `hacs.json` blendet den Entwicklungsbranch aus der Downloadauswahl aus.
HACS lädt die Integrationsdateien aus dem Release-Tag; zusätzliche ZIP-Assets und
`zip_release` sind für diese Repository-Struktur nicht erforderlich.

## Neue Version veröffentlichen

1. `custom_components/grilleye_classic/manifest.json`: `version` erhöhen, ohne `v`,
   z. B. `0.2.1`. Nur stabile Versionen `major.minor.patch` sind vorgesehen.
2. `CHANGELOG.md`: passenden Abschnitt `## 0.2.1` mit den Änderungen ergänzen.
3. Änderungen prüfen und nach `main` zusammenführen.
4. Der Workflow **Validate** führt Python-/HA-Tests, Release-Logiktests, Ruff,
   Abhängigkeitsprüfung, HACS und hassfest aus. Erst wenn alle drei Prüfjobs
   erfolgreich sind, veröffentlicht der Job **release** ein GitHub-Release.

Das Release erhält den Tag `v` plus Manifest-Version, zeigt genau auf den geprüften
Commit und übernimmt die passenden Änderungen aus dem Changelog. Es ist weder
Entwurf noch Vorabversion. Pull Requests und andere Branches veröffentlichen nichts.
Nur der Veröffentlichungsjob hat Schreibrechte für Repository-Inhalte.

Eine bereits veröffentlichte Version wird nie überschrieben. Änderungen an derselben
Manifest-Version (etwa Dokumentationskorrekturen) erzeugen kein neues Release.
Für auszuliefernde Änderungen die Versionsnummer erhöhen. Besteht bereits ein
gleichnamiger Tag ohne Release, bricht der Job zur Prüfung ab.

Hat sich `main` inzwischen weiterbewegt, veröffentlicht ein älterer Prüflauf nichts;
der aktuelle Lauf übernimmt. Veröffentlichungsläufe werden nacheinander ausgeführt.
Nach einem vorübergehenden Fehler kann **Validate → Run workflow → main** erneut
ausgeführt werden; die Prüfungen laufen vor dem Veröffentlichungsjob erneut.

## Update in Home Assistant

HACS → GrillEye Classic → Informationen aktualisieren bzw. auf Updates prüfen,
Release installieren und **Home Assistant neu starten**. Die Integration nicht löschen
oder neu einrichten. Der HACS-Abgleich erfolgt zeitversetzt; eine neue Veröffentlichung
erscheint nicht zwingend sofort in der Oberfläche.

Beim ersten Wechsel einer bisherigen Branch-Installation auf Releases ggf. in HACS
**Erneut herunterladen** öffnen und die veröffentlichte Version `v0.2.0` auswählen.
Die tatsächliche Erkennung in der Nutzerinstallation ist separat zu prüfen.

Die Alarmvorlage bleibt ein eigener Import unter Automationen & Szenen → Blueprints.
Ein HACS-Update erzeugt keine Helfer oder Automationen; siehe [ALARMS.md](ALARMS.md).

## Rückkehr zu einer älteren Version

In HACS eine vorherige veröffentlichte Version erneut herunterladen und HA neu
starten. `v0.2.0` ist das erste veröffentlichte Release; erst spätere Releases
bieten diese Versionsauswahl für einen Rückwechsel. Die bisherige Version 0.1.0
wird nicht nachträglich als vermeintlich neuestes Release veröffentlicht.

## Quellen

- [HACS-Versionserkennung](https://www.hacs.xyz/docs/publish/start/#versions)
- [HACS-Integrationsstruktur](https://www.hacs.xyz/docs/publish/integration/)
