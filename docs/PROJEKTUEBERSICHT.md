# Kinderbuch-Bildlabor – Projektübersicht

## Ausgangsfrage

Das Projekt untersucht, wie sich einzelne Illustrationen aus digitalisierten Kinder- und Jugendbüchern
beschreiben, am Bild prüfen und mit ihrer Herkunft weitergeben lassen. Grundlage ist der öffentlich
zugängliche Colibri-Datensatz der Staatsbibliothek zu Berlin mit 53.533 Abbildungen und Metadaten.
An sechs Beispielen werden Bildregion, sichtbarer Inhalt, Aufdrucke und die zugehörigen Prüfentscheidungen
in einem nachvollziehbaren Arbeitsablauf zusammengeführt.

Das Bildlabor zeigt an einer kleinen, echten Stichprobe, wie sich diese Angaben nachvollziehbar
erfassen, einzeln prüfen und verlustfrei weitergeben lassen. Es ist ein Prototyp, kein Produktionssystem.

## Ablauf je Objekt

1. **Quelle:** Scan, IIIF-Bildinformation und METS/MODS-Antwort der Staatsbibliothek sowie die
   Colibri-Metadatenzeile werden unverändert gespeichert und über Prüfsummen gesichert.
2. **Regionen:** Die Illustration und Textbereiche werden als Rechtecke in Pixeln des Originalbildes
   erfasst. Die verkleinerte Anzeige ändert die Werte nicht.
3. **Beschreibung:** Der sichtbare Bildinhalt wird ohne Deutung beschrieben. Dazu kommen projektlokale
   Suchbegriffe; sie sind ausdrücklich keine geprüften GND-Verknüpfungen.
4. **Transkription:** Bildtitel und Aufdrucke werden zeichengetreu mit historischer Schreibweise
   erfasst, direkt unter dem Bildausschnitt. Die gespeicherte OCR-Ausgabe steht unverändert daneben.
5. **Bibliotheksdaten:** Aus der OAI-PMH-Antwort wird das Buch-MODS ausgewertet. Jedes Textelement
   bleibt mit seinem XPath erhalten, auch wiederholte Felder und Rollen. Der Abgleich mit den lokalen
   Angaben erfolgt zeichengenau und ohne automatische Übernahme.
6. **Prüfung:** Jeder Bereich (Regionsgrenzen, Beschreibung, Suchbegriffe, jede Transkription) wird
   einzeln mit Name und Zeitpunkt bestätigt. Eine spätere Änderung setzt nur diesen Bereich zurück.
7. **Export:** JSON mit vollständigem Arbeitsstand, Herkunft, Rechten und Prüfprotokoll sowie CSV
   mit einer Zeile je Region. Eine Rückladeprüfung zeigt, ob Unicode, Nullwerte, Koordinaten und
   Prüfstände erhalten blieben. Ein veralteter Export wird als solcher benannt, nicht als Fehler.

## Fachliche Grundsätze

- **Unbekannt bleibt unbekannt:** Der Illustrator ist nicht ermittelt und bleibt leer. Buchautor und
  Illustrator sind verschiedene Rollen.
- **Scan-Nummer ist keine Seitenzahl:** Die gedruckte Seitenzahl bleibt leer, bis sie am Scan
  bestätigt ist. Die Seitenbezeichnung im METS wird getrennt angezeigt.
- **Kontexte werden nicht vermischt:** Beim Pilotobjekt nennen Colibri und MODS Augsburg und
  J. A. Schlosser. Der Aufdruck auf dem Bildblatt nennt eine Rottweiler Buchhandlung. Beide Angaben
  bleiben mit ihrem Bezug erhalten. Die Abweichung ist ein Prüfhinweis, kein Katalogfehler.
- **Vorschläge sind keine Prüfungen:** Maschinelle Ausgaben (OCR, automatisch ermittelte Grenzen,
  Beschreibungsentwürfe des KI-Assistenten) tragen ihre Herkunft sichtbar mit und gelten erst nach
  einer menschlichen Bestätigung als geprüft.
- **Keine Ground Truth ohne Freigabe:** Es gibt keine freigegebene Referenztranskription. Deshalb
  gibt es auch keine OCR-Bewertung (CER/WER).
- **Parsing ist keine Validierung:** Die METS/MODS-Antwort wird geparst und inhaltlich geprüft, aber
  nicht gegen ein XSD-Schema validiert. Die Oberfläche sagt das ausdrücklich.

## Was fertig ist

| Bereich | Stand |
|---|---|
| Stichprobe | 6 Illustrationen aus 2 Büchern, alle Quelldateien lokal mit Prüfsummen |
| Regionen | Bearbeitung in Originalpixeln, Vorschau, Bereichsprüfung, Bestätigung |
| Beschreibung, Suchbegriffe | Bearbeitung, Herkunftsangabe, getrennte Bestätigung |
| Transkription | zwei Felder beim Pilotobjekt, je einzeln bestätigbar, OCR-Ausgabe unverändert daneben |
| METS/MODS | Struktur, Seitenbezug, Personen und Rollen, vollständiges Mapping, Abgleich |
| Validierung | technische Fehler, fachliche Hinweise und nicht ausgeführte Prüfungen getrennt |
| Export | JSON und CSV je Objekt, Sammlungs-CSV, Rückladeprüfung, Prüfprotokoll |
| Datensicherheit | Quelldateien werden nur gelesen und über Prüfsummen kontrolliert; kein Überschreiben neuerer Stände aus veralteten Fenstern |

## Grenzen

- Alle Prüfstände sind offen oder vorläufig. Bestätigt ist bisher nur, was im Prüfprotokoll mit
  Namen steht.
- Die Beschreibungen, Suchbegriffe und Regionsgrenzen der fünf Genovefa-Illustrationen sind Entwürfe
  (KI-Assistent bzw. automatische Rahmenerkennung) und noch nicht menschlich geprüft.
- Keine Live-Abfrage von OAI-PMH oder IIIF, keine neue OCR, keine GND-Anbindung, keine XSD-Validierung.
- Einzelplatzbetrieb: Mehrere Browserfenster an einem gestarteten Server sind abgesichert, mehrere
  gleichzeitig gestartete Server auf denselben Daten nicht.
- Weitere Punkte: [OFFENE_PUNKTE.md](OFFENE_PUNKTE.md).

## Beitrag

- **Shota Tsertsvadze:** Fragestellung und fachliche Anforderungen, Auswahl der Quellen, erste Lesung
  der Bildunterschriften des Pilotobjekts, Annahme der Pilot-Suchbegriffe, Bestätigung der
  Regionsgrenzen des Bildtitels (siehe Prüfprotokoll). Weitere fachliche Prüfungen der Stichprobe
  stehen noch aus und sind in [OFFENE_PUNKTE.md](OFFENE_PUNKTE.md) aufgeführt.
- **KI-Programmierassistent (Claude):** Umsetzung der Anwendung und der Tests nach diesen Vorgaben
  sowie die als „Entwurf des KI-Assistenten“ gekennzeichneten Beschreibungs- und Suchbegriffsvorschläge.
- **Quellen:** Digitalisate und Metadaten der Staatsbibliothek zu Berlin; Colibri-Datensatz von
  Sebastian Schmideler, Sigrun Putjenter und Jörg Lehmann (CC BY 4.0).
