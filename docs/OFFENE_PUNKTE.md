# Offene Punkte

## Fachliche Prüfung der Stichprobe

Die Entwürfe (automatisch ermittelte Regionsgrenzen, Beschreibungen und Suchbegriffe des
KI-Assistenten, vorläufige Lesungen) wurden für alle sechs Objekte der Stichprobe durchgesehen und die
Objekte endbestätigt. Was geprüft ist, steht mit Name und Zeitpunkt im Prüfprotokoll jedes Objekts und im
Export.

Beleg ist nur für Genovefa, Scan 22 der unveränderte Export unter [ergebnis/](ergebnis/README.md). Für
„Die Heimath in Amerika“, Scan 6, und Genovefa, Scan 14, 16, 17 und 85 liegen die Exporte (JSON und CSV)
nur lokal im Datenordner der Prüfung unter `exports/` und sind absichtlich nicht im Repo, weil
Arbeitsdaten und Exporte nicht eingecheckt werden. Eine frisch gestartete Anwendung zeigt dagegen für
jedes Objekt den Quellstand, also alles offen.

Es gibt keine Zweitprüfung: In den Prüfprotokollen von Scan 6 sowie Scan 14, 16, 17 und 85 trägt jeder
Eintrag mit Person denselben Namen (Shota Tsertsvadze). Zu Scan 22 siehe die Tabelle. Die Endbestätigung
ist keine Ground-Truth-Freigabe.

| Objekt | Stand laut Export | Offen |
|---|---|---|
| Genovefa, Scan 22 (Leitbeispiel) | alle vier Prüfbereiche bestätigt, Klassifikation und Illustrator begründet entschieden, endbestätigt von Shota Tsertsvadze (08.11.2026) | Zum Illustrator nur der Bildausschnitt geprüft, keine weiteren Quellen. Rahmen, Beschreibung und Suchbegriffe tragen im Protokoll den Namen „shota“. Keine Zweitprüfung. |
| Genovefa, Scan 14 | alle vier Prüfbereiche bestätigt (Regionsgrenzen, Klassifikation, Beschreibung, Suchbegriffe), Hinweis Illustrator begründet entschieden, endbestätigt von Shota Tsertsvadze (12.11.2026). Klassifikation: „Manuelle Klasse trifft zu: Abbildung“ (Colibri automatisch: Druckermarke). Beschreibung gegenüber dem Entwurf geändert; Rahmen und Suchbegriffe unverändert | Zum Illustrator Bild und MODS geprüft, keine weiteren Quellen. Keine Zweitprüfung. |
| Genovefa, Scan 16 | wie Scan 14, endbestätigt von Shota Tsertsvadze (12.11.2026). Klassifikation: „Manuelle Klasse trifft zu: Abbildung“ (Colibri automatisch: Druckermarke). Beschreibung gegenüber dem Entwurf geändert; Rahmen und Suchbegriffe unverändert | Wie Scan 14. |
| Genovefa, Scan 17 | wie Scan 14, endbestätigt von Shota Tsertsvadze (12.11.2026). Klassifikation: „Manuelle Klasse trifft zu: Abbildung“ (Colibri automatisch: Exlibris). Beschreibung, Rahmen und Suchbegriffe unverändert gegenüber dem Entwurf | Wie Scan 14. |
| Genovefa, Scan 85 | wie Scan 14, endbestätigt von Shota Tsertsvadze (12.11.2026). Klassifikation: „Manuelle Klasse trifft zu: Abbildung“ (Colibri automatisch: Exlibris). Beschreibung gegenüber dem Entwurf geändert; Rahmen und Suchbegriffe unverändert | Der Gegenstand der Person rechts ist in der Beschreibung als „nicht erkennbar“ festgehalten und nicht bestimmt. Sonst wie Scan 14. |
| Die Heimath in Amerika, Scan 6 | alle drei Regionen, Beschreibung und beide Transkriptionen („Die Heimath in Amerika.“, „Verlag der I.P.Setzer'schen Buchhandlung in Rottweil.“) bestätigt, Hinweise Verlag („Unterschied geprüft; beide Angaben bleiben mit ihrem Bezug erhalten“, ohne ermittelte Ursache) und Illustrator („unbekannt; Feld bewusst leer“, Signatur „L.H.“ nicht aufgelöst) begründet entschieden, endbestätigt von Shota Tsertsvadze (12.11.2026). Regionen, Beschreibung und Transkriptionen unverändert gegenüber dem Quellstand | Die Startpaket-Lesung „L.L Setyerschen“ bleibt als `initial_user_transcription` im Export neben der bestätigten Lesung stehen. Keine Zweitprüfung. |

Der Pilotexport im Repo dokumentiert nur die Bestätigung der Region „Bildtitel“; die später bestätigten Regionen, die Beschreibung und beide Transkriptionen stehen nur im lokalen Export. Die Annahme der Pilot-Suchbegriffe stammt aus dem Startpaket und hat dort keinen eigenen
Protokolleintrag mit Name und Zeitpunkt. Zur Seitenzahl bei Genovefa: Die METS-Seitenbezeichnungen (8, 10, 11, 16, 79) entsprechen
vermutlich den gedruckten Zahlen; das ist nicht bestätigt, das Feld bleibt leer.

## Bekannte Einschränkungen

- Das Sicherungspaket entsteht unter der Datensperre eines Servers; es gilt wie die übrige Speicherung nicht für mehrere Server auf einem Datenordner. Zurückspielen geht nur per Kommandozeile in einen neuen Ordner.
- Mehrere Browserfenster an einem Server sind abgesichert, mehrere Server auf einem Datenordner nicht.
- Gedruckte Seitenzahl und Illustrator lassen sich nur bei importierten Büchern bearbeiten (Reiter „Angaben“), nicht bei den Beispielobjekten.
- Koordinaten lassen sich im Bild ziehen oder über Zahlenfelder bearbeiten.
- Regionen lassen sich nur bei importierten Büchern zurückziehen; ein Wiederherstellen ist nicht vorgesehen.
- Unter etwa 650 Pixel Fensterbreite stehen Bild und Bearbeitung untereinander; dann ist mehr Blättern nötig.
- Eine Entscheidung lässt sich ersetzen, unverändert erneut bestätigen oder mit Grund zurückziehen; sie bleibt dann im Datensatz archiviert.

## Nicht umgesetzt (mögliche Erweiterungen)

Siehe [BEZUG_ZUR_STELLE.md](BEZUG_ZUR_STELLE.md), Abschnitt „Nicht gezeigt“.
