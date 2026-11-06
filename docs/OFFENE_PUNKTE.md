# Offene Punkte

## Prüfaufgaben (fachlich, nur durch eine Person)

Alle Aufgaben erledigen Sie in der Anwendung, mit Ihrem Namen unter „Prüfende Person“. Die Zeiten
sind Schätzungen.

| Nr. | Objekt | Aufgabe | Zeit |
|---|---|---|---|
| 1 | Genovefa, Scan 14 | Regionsgrenzen am Bildrahmen prüfen; Beschreibung lesen, korrigieren, bestätigen; Suchbegriffe prüfen | 10 Min. |
| 2 | Genovefa, Scan 16 | wie 1 | 10 Min. |
| 3 | Genovefa, Scan 17 | wie 1 | 10 Min. |
| 4 | Genovefa, Scan 22 | wie 1 | 10 Min. |
| 5 | Genovefa, Scan 85 | wie 1; im Entwurf als unsicher markiert: der Gegenstand der Person rechts | 10 Min. |
| 6 | Heimath, Scan 6 | Grenzen „Illustration“ und „Verlagsangabe“ prüfen; Beschreibung bestätigen | 10 Min. |
| 7 | Heimath, Scan 6 | Bildtitel und Verlagsangabe an der vergrößerten Vorlage abschließend lesen (I.P. oder L.P. Setzer?) | 15 Min. |
| 8 | alle | danach je Objekt neu exportieren und die Sammlungs-CSV erzeugen | 5 Min. |

Zur Seitenzahl bei Genovefa: Die Scans zeigen oben gedruckte Zahlen, die wie die
METS-Seitenbezeichnungen (8, 10, 11, 16, 79) aussehen. Das ist nicht bestätigt; das Feld
„gedruckte Seitenzahl“ bleibt deshalb leer. Bearbeiten lässt es sich in dieser Version nicht.

## Bekannte Einschränkungen

- Mehrere Browserfenster an einem gestarteten Server sind abgesichert: Speichern ist eine gesperrte
  Lese-Änderungs-Schreib-Einheit, und veraltete Eingaben können neuere Stände nicht überschreiben.
  Zwei gleichzeitig gestartete Server auf demselben Datenordner sind nicht abgesichert.
- Gedruckte Seitenzahl und Illustrator lassen sich in der Oberfläche nicht bearbeiten.
- Im Reiter „Prüfung“ ist eine ausdrückliche Endbestätigung mit Name und Zustimmung möglich.
  Alle Einzelbereiche müssen bestätigt und alle technischen und fachlichen Blocker gelöst sein.
  Bestehende review_items und MODS-Abweichungen bleiben Blocker; ihre Auflösung ist nicht automatisiert.
  Nicht ausgeführte optionale Prüfungen bleiben sichtbar, blockieren aber nicht.
  Inhaltsänderungen heben die Endbestätigung auf; das Protokoll bleibt erhalten.
  Endbestätigung ist keine Ground-Truth-Freigabe. Ältere Datensätze bleiben ohne Migration offen.
- Die Koordinaten werden über Zahlenfelder bearbeitet, nicht durch Ziehen im Bild.
- Bei schmalen Fenstern (unter etwa 1000 Pixel) stehen Bild und Bearbeitung untereinander;
  bedienbar, aber weniger übersichtlich.
- Ein Export, der älter als eine Modellumstellung ist, wird als „veraltet“ angezeigt.

## Nicht umgesetzt (mögliche Erweiterungen)

- Live-Abruf über OAI-PMH und IIIF
- XSD-Validierung der METS/MODS-Antworten
- GND-Verknüpfung der Suchbegriffe
- OCR-Bewertung (CER/WER) nach Freigabe einer Referenztranskription; HTR
- W3C-Web-Annotation-Export; Beispiele für OpenRefine oder Catmandu
