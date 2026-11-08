# Abgeschlossenes Beispiel: Genovefa, Scan 22

Dieser Ordner enthält zwei unveränderte Exporte aus der Anwendung. Sie lassen sich ohne Installation
ansehen. Die Anwendung selbst startet dagegen mit dem Quellstand: Dort sind alle Prüfbereiche offen,
bis jemand im eigenen Datenordner prüft.

| Datei | Inhalt | SHA-256 |
|---|---|---|
| [genovefa-scan-022.json](genovefa-scan-022.json) | vollständiger Arbeitsstand mit Entscheidungen, Prüfprotokoll und Änderungsgeschichte | `05647307abbf6d57297dbda2dd181355c6b8fdc891addd5f8f446f1a279c6bcc` |
| [genovefa-scan-022.csv](genovefa-scan-022.csv) | eine Zeile je Region mit beiden Colibri-Klassen, Entscheidung, Herkunft und Rechten | `c0f23225f243f05d235446ac164c34b3515e350f603c3fed4da562160bb0c9e3` |
| [pilot-001.json](pilot-001.json) | Pilotobjekt „Die Heimath in Amerika“, Scan 6 | `febad0e61af20420cf85ffc58110dd325d6f2b4f2de167848fcac64595e955fd` |
| [pilot-001.csv](pilot-001.csv) | dasselbe als CSV | `9ed2e6abad8beb95d094b90dca3545a0567b04f090b82ea8576ada05082bcd8a` |

## Genovefa, Scan 22

Geprüft im Arbeitsordner der bewerbenden Person, exportiert am 08.11.2026 um 12:27 Uhr. Der Export
entspricht dem gespeicherten Arbeitsstand. Alle Einträge im Prüfprotokoll tragen den Namen „Shota“.
Zeiten in Berliner Ortszeit:

| Zeit | Vorgang |
|---|---|
| 11:34 | Regionsgrenzen der Illustration bestätigt (Koordinaten unverändert: 229, 299, 924, 617) |
| 11:36 | Klassifikation entschieden: „Manuelle Klasse trifft zu: Abbildung“. Begründung: „Manuelle Klasse trifft zu, es ist eine Abbildung.“ |
| 11:37 | Bildbeschreibung bestätigt (Entwurf des KI-Assistenten, Text unverändert) |
| 12:25 | Suchbegriffe bestätigt (Entwurf des KI-Assistenten, unverändert: Mann, Frau, Gewölbe, Treppe, Gitterfenster) |
| 12:26 | Hinweis Illustrator entschieden: „Illustrator bleibt unbekannt; Feld bewusst leer“. Begründung: „test 2“ |
| 12:26 | Endbestätigung erteilt |

Das Beispiel zeigt, wie eine Entscheidung weitergegeben wird:
- Beide Colibri-Werte bleiben unverändert erhalten (manuell „Abbildung“, automatisch „Karte“).
- Die Entscheidung steht daneben, mit Name, Zeitpunkt und den Regionsgrenzen, auf denen sie beruht.
- Herkunft (automatisch ermittelte Grenzen, KI-Entwürfe) und Prüfstand sind getrennt ausgewiesen.
- Die Änderungsgeschichte gehört zum Export und wird beim Zurücklesen verglichen.

## Einschränkungen

- Beide Begründungen stehen wörtlich so, wie sie gespeichert wurden. Die Begründung zur Klassifikation
  wiederholt die gewählte Antwort und nennt keine Beobachtung am Bild. Die Begründung zum Illustrator
  lautet „test 2“ und ist keine fachliche Begründung.
- Die Endbestätigung ist keine Ground-Truth-Freigabe. Es gab keine Zweitprüfung durch eine andere
  Person.
- Geprüft ist nur Scan 22. Die Scans 14, 16, 17 und 85 sind offen (siehe [OFFENE_PUNKTE.md](../OFFENE_PUNKTE.md)).
- Im JSON stehen die Herkunftsfelder in ihrem überlieferten Wortlaut, einschließlich „ungeprüft“. Der
  Prüfstand steht in den eigenen Statusfeldern; die CSV zeigt beides getrennt.

## Pilotobjekt „Die Heimath in Amerika“

Der Pilotexport (07.11.2026, 23:05 Uhr) stammt aus dem vorigen Übergabe-ZIP und wurde unverändert
übernommen. Sein Inhalt stimmt mit dem lokalen Arbeitsstand des Pilotobjekts überein. Er belegt eine
einzelne Bestätigung: den Rahmen um den Bildtitel, von Shota Tsertsvadze am 06.11.2026 um 15:50 Uhr. Die
übrigen Regionen, die Beschreibung und beide Transkriptionen sind offen. Die Suchbegriffe tragen den
Status „vom Nutzer akzeptiert“ aus dem Startpaket, ohne Protokolleintrag mit Name und Zeitpunkt.
