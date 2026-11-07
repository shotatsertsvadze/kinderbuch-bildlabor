# Stichprobe: Quellen, Rechte, Annotationsregeln, Prüfstände

## Objekte

| Nr. | Objekt-ID | Buch | Scan | Seite laut METS | Colibri-Datei | Colibri manuell / automatisch |
|---|---|---|---|---|---|---|
| 1 | pilot-001 | Die Heimath in Amerika, Augsburg 1850 (PPN1814684999) | 6 | – | data/PPN1814684999/00000006_0.jpg | Abbildung / Abbildung |
| 2 | genovefa-scan-014 | Genovefa, Augsburg 1810 (PPN1772789429) | 14 | 8 | data/PPN1772789429/00000014_0.jpg | Abbildung / Druckermarke |
| 3 | genovefa-scan-016 | Genovefa | 16 | 10 | data/PPN1772789429/00000016_0.jpg | Abbildung / Druckermarke |
| 4 | genovefa-scan-017 | Genovefa | 17 | 11 | data/PPN1772789429/00000017_0.jpg | Abbildung / Exlibris |
| 5 | genovefa-scan-022 | Genovefa | 22 | 16 | data/PPN1772789429/00000022_0.jpg | Abbildung / Karte |
| 6 | genovefa-scan-085 | Genovefa | 85 | 79 | data/PPN1772789429/00000085_0.jpg | Abbildung / Exlibris |

Beide Bücher stammen von Christoph von Schmid und sind in Augsburg erschienen. Das Pilotbuch enthält
laut Colibri nur diese eine Abbildung (manuell und automatisch „Abbildung“; im Pilot-Arbeitsmodell sind
die Klassen nicht als Felder geführt).

**Auswahl bei „Genovefa“:** alle Zeilen der Colibri-CSV zu PPN1772789429 mit manueller Klasse. Die CSV
enthält 18 Zeilen zu diesem Buch; 13 tragen in der Spalte „groundtruth“ den Wert „-0“ statt einer Klasse
(automatisch jeweils „Abbildung“), fünf tragen „Abbildung“. Bei allen fünf weicht die automatische
Klasse ab: zweimal „Druckermarke“, zweimal „Exlibris“, einmal „Karte“. Geprüft am 07.11.2026 gegen
die öffentliche CSV, deren SHA-256 mit dem Wert im Manifest übereinstimmt. Die Werte stehen
unverändert in `colibri_groundtruth` und `colibri_classification` der Datensätze. Alle Zahlen gelten nur
für dieses Buch und diese fünf Beispiele. Es handelt sich um Buchillustrationen in gedruckten Büchern
(bei Genovefa in den Textseiten gedruckt, beim Pilotobjekt ein Frontispiz laut MODS-Umfangsangabe),
nicht um Originalzeichnungen, Nachlassmaterial oder Comics. Die Drucktechnik ist nicht bestimmt.

## Quellen und Dateien

- `Kinderbuch_Bildlabor_Start/`: Startpaket des Pilotobjekts mit `MANIFEST.json` (Quell-URLs,
  Abrufdatum, SHA-256). Das Feld `status_de` im Manifest beschreibt den Stand beim Abruf.
- `sammlung/genovefa/`: Scans in voller Auflösung über die IIIF-Image-API, unveränderte
  IIIF-`info.json`, die OAI-PMH-Antwort (METS/MODS) zum Buch und je ein Arbeitsmodell `scan_*.json`.
  Alles wurde am 06.11.2026 abgerufen; URLs und Prüfsummen stehen in `MANIFEST.json`.
- `sammlung/katalog.json`: welche Dateien zu welchem Objekt gehören.
- Aus der Colibri-CSV (`ColibriImagesMetadataAnnotations.csv`, Prüfsumme im Manifest) wurden nur die
  Zeilen dieser fünf Dateien übernommen. Colibri-Bilddateien selbst wurden nicht geladen.

## Rechte und Namensnennung

- Quellwerke: Public Domain Mark 1.0 (laut Colibri und MODS).
- Colibri-Metadaten und -Annotationen: CC BY 4.0. Namensnennung: Sebastian Schmideler, Sigrun
  Putjenter, Jörg Lehmann; Staatsbibliothek zu Berlin; Colibri, 2025. DOI 10.5281/zenodo.15535927.
- Beide Angaben stehen in jedem Datensatz und in jeder CSV-Zeile.

## Annotationsregeln

- **Regionen:** Rechteck `[x, y, Breite, Höhe]` in Pixeln des Ausgangsbildes, Ursprung links oben.
  Eine Illustration wird bis einschließlich ihrer gedruckten Rahmenlinie erfasst, ohne umgebenden Text.
- **Beschreibung:** nur Sichtbares, in sachlichem Deutsch. Personen werden nach Erscheinung benannt
  („Frau mit Krone“), nicht nach vermuteten Romanfiguren. Unsicheres wird als unsicher benannt.
- **Suchbegriffe:** projektlokal, ein Begriff je Zeile, im Singular, keine Deutung.
- **Transkription:** zeichengetreu, historische Schreibweise und Zeichensetzung bleiben erhalten, keine
  Normalisierung. Die OCR-Ausgabe wird nie korrigiert, sondern getrennt gespeichert.
- **Unbekannte Werte:** bleiben `null`, nicht leer und nicht geschätzt (Illustrator, gedruckte Seitenzahl).

## Klassifikationsentscheidung

Weichen manuelle und automatische Klasse ab, entscheidet eine benannte Person am Bild: manuelle Klasse
trifft zu, automatische trifft zu, keine von beiden, oder nicht entscheidbar. Eine Begründung ist
Pflicht. Die Entscheidung beruht auf den gespeicherten Regionsgrenzen der Illustration; ändern sie sich,
wird sie aufgehoben. Gleiches Verfahren gilt für die Hinweise zu Verlag und Illustrator. Beide
Ausgangswerte bleiben stets erhalten.

## Prüfstände

| Bereich | offen | bestätigt |
|---|---|---|
| Regionsgrenzen | Entwurf – visuelle Prüfung offen | Grenzen visuell geprüft |
| Beschreibung | ungeprüft | am Bild geprüft |
| Suchbegriffe | Vorschlag – Prüfung offen / geändert – erneute Prüfung offen | vom Nutzer akzeptiert |
| Klassifikation | Entscheidung am Bild offen / nicht entscheidbar | begründet entschieden |
| Transkription | vorläufig | geprüft |
| OCR-Ausgabe | ungeprüft (bleibt so; dient nur dem Vergleich) | – |

Jede Bestätigung steht mit Name, Zeitpunkt und Bereich im Prüfprotokoll (`review_log`). Jede
Speicherung steht im Änderungsprotokoll (`change_log`). Eine Bestätigung gilt immer dem angezeigten
Stand. Wurde der Inhalt inzwischen anderswo geändert, wird sie abgelehnt.

## Herkunft der Arbeitsstände bei Genovefa

- Regionsgrenzen: automatisch an der gedruckten Rahmenlinie ermittelt (Dunkelwert-Profil), ungeprüft.
- Beschreibungen und Suchbegriffe: Entwürfe des KI-Assistenten (Claude) vom 06.11.2026 nach Ansicht
  der Scans, ungeprüft.
- Die Herkunft steht in den Feldern `region_origin_de`, `description_origin_de` und
  `keyword_origin_de` und wird in Oberfläche und CSV angezeigt.
