# Feature-Ranking (Stand 12.11.2026)

Grundlage: `OFFENE_PUNKTE.md`, `BEZUG_ZUR_STELLE.md` („Nicht gezeigt“) und der umgesetzte Plan
`.gg/plans/top-three-features.md`. Schon vorhanden: Import eigener Bücher (Bild, PDF, IIIF),
Zeichenfläche für Regionen, lokale Tesseract-Zweitlesung. Das hier ist ein Vorschlag, kein Plan.

Aufwand: S = Tage, M = ein bis zwei Wochen, L = mehr. Risiko bezieht sich auf die Regeln in
`AGENTS.md` (getrennte Bestätigungen je Bereich, Invalidierung, Sperre und Verlauf, Export-Aktualität).

## 1. Metadaten importierter Bücher bearbeiten (umgesetzt, Beispielobjekte ausgenommen)

- **Nutzen:** Importierte Bücher zeigen Verfasser, Ort, Jahr, Verlag, Seitenzahl und Illustrator als „unbekannt“, lassen sich aber nicht ergänzen. Ohne das bleibt der Import halb nutzbar. Gleiches gilt für Seitenzahl und Illustrator der Beispielobjekte.
- **Aufwand:** M.
- **Risiko:** mittel. Es braucht einen eigenen Prüfbereich „Bibliografische Angaben“ mit eigener Bestätigung. Eine Änderung muss nur diesen Bereich und die Endbestätigung zurücksetzen. Herkunft (Import, Person, Zeitpunkt) muss je Feld sichtbar bleiben. Beispielobjekte behalten ihre Quellabgleiche unverändert.

## 2. Korrekturen zurücknehmen: Region löschen, Entscheidung zurückziehen (umgesetzt)

- **Nutzen:** Eine versehentlich gezeichnete Region lässt sich heute nicht entfernen. Eine Entscheidung lässt sich nicht ersatzlos zurücknehmen. Das ist die größte Lücke im Alltag der Zeichenfläche.
- **Aufwand:** S bis M.
- **Risiko:** mittel bis hoch. Gelöschtes darf keine Beweise vernichten: die Region bleibt als „zurückgezogen“ im Verlauf und im Export sichtbar, ihre Bestätigungen bleiben im `review_log`. Zugehöriges Transkriptionsfeld und Kandidaten brauchen eine klare Regel. Endbestätigung und Export-Aktualität müssen reagieren.

## 3. Zweitprüfung durch eine zweite Person

- **Nutzen:** Schließt die Lücke zur Ground Truth (ADR 0003: Endbestätigung ist keine Ground Truth). Grundlage für spätere Messungen wie CER/WER an freigegebenen Referenztranskriptionen.
- **Aufwand:** M bis L.
- **Risiko:** hoch. Neue Art von Bestätigung, die von einer anderen Person stammen muss als die erste. Das ist in einer lokalen Anwendung ohne Anmeldung nur Namenskonvention, kein Beweis. Das ist ehrlich zu benennen. Braucht einen neuen ADR. Folgt: CER/WER, erst nach Freigabe einer Referenz.

## 4. Export als W3C Web Annotation (JSON-LD) und IIIF-Annotationen

- **Nutzen:** Regionen, Beschreibung und Transkription lassen sich in Viewern und anderen Tools wiederverwenden. Passt zur bestehenden IIIF-Region `x,y,w,h` in Originalpixeln. Bringt den Export aus der Insel-Form heraus.
- **Aufwand:** M.
- **Risiko:** niedrig, wenn der Export wie das CSV nur serialisiert: Datensatz und JSON-Export bleiben unverändert, keine neuen Bestätigungen. Zu klären: Wie werden Prüfstände und Herkunft abgebildet, ohne Bestätigungen zu überhöhen? Export-Aktualität gilt auch für die neue Datei.

## 5. Sicherung und Wiederherstellung des Arbeitsstands

- **Nutzen:** `.history` ist keine Sicherung auf einem anderen Gerät. Ein Sicherungspaket (Arbeitsstände, Importe, Prüfsummen) und ein geprüftes Zurückspielen schützen die einzige Kopie der Prüfarbeit. Hilft auch beim Umzug auf einen anderen Rechner.
- **Aufwand:** M.
- **Risiko:** hoch, weil Zurückspielen überschreiben kann. Muss in einen leeren oder neuen Datenordner schreiben oder vor jedem Überschreiben den Stand exakt sichern (wie bei `.history`). Prüfsummen müssen vor dem Zurückspielen stimmen. Quelldateien und `sammlung/` bleiben tabu.

## Weitere Kandidaten (nicht priorisiert)

XSD-Validierung von METS/MODS (braucht lokal vorliegende Schemata); GND-Verknüpfung der Suchbegriffe;
Export als ALTO oder PAGE-XML; Live-Harvesting über OAI-PMH (widerspricht dem Offline-Grundsatz).

## Veraltete Aussagen in anderen Dokumenten

Keine bekannt: `OFFENE_PUNKTE.md` und `BEZUG_ZUR_STELLE.md` sind an Import, Zeichenfläche und Zweitlesung angepasst.

## Offene Beobachtungen aus dem Browserlauf (12.11.2026)

- Behoben: Nach dem Anlegen der ersten Textregion sprang die Ansicht auf „Übersicht“, weil dadurch der Reiter
  „Transkription“ neu entstand; der gewählte Reiter bleibt jetzt erhalten.
- Zurückgezogene Entscheidungen lassen sich nur bei Objekten mit Befund zurückziehen; bei importierten Büchern gibt es keine.
