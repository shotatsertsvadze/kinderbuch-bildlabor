# Bezug zu den Aufgaben im Datenmanagement

| Aufgabe | Im Projekt gezeigt | Wo |
|---|---|---|
| Bibliografische Metadaten | Buchangaben aus Colibri, Rollen getrennt (Verfasser ≠ Illustrator), unbekannte Werte bleiben leer | Übersicht, Bibliotheksdaten |
| Digitalisierung | Scan-Nummer, physische Seite (METS), Seitenbezeichnung und gedruckte Seitenzahl getrennt; IIIF-Bildinformation geprüft | Übersicht, Prüfung |
| OCR/HTR | gespeicherte Tesseract-Ausgabe mit Modell, Version und Eingabeprüfsumme; Arbeitstranskription getrennt; keine Bewertung ohne Ground Truth | Transkription |
| Bildannotation | Regionen in Originalpixeln, Beschreibung, projektlokale Suchbegriffe, Herkunft jedes Vorschlags | Regionen, Beschreibung |
| Forschungsdatensätze | dokumentierte Stichprobe mit Quellen, Prüfsummen, Rechten, Annotationsregeln und Prüfständen | `docs/DATENSATZ.md`, `sammlung/` |
| OAI-Harvesting | Auswertung gespeicherter OAI-PMH-GetRecord-Antworten (METS/MODS) zweier Bücher | Bibliotheksdaten |
| Metadaten-Mapping und -Konvertierung | MODS-Feld mit XPath → Originalwert → lokales Feld; wiederholte Felder bleiben erhalten; Export als JSON und CSV | Bibliotheksdaten, Export |
| Qualitätssicherung | Validierung in drei Kategorien, Bestätigung je Bereich mit Protokoll, Rückladeprüfung, Schutz vor Überschreiben, 70 automatische Tests | Prüfung, Export, `tests/` |

Nicht gezeigt, als Erweiterung denkbar: Live-Harvesting über OAI-PMH, HTR, GND-Anbindung der
Suchbegriffe, XSD-Validierung, W3C Web Annotation als Exportformat, Massenbereinigung mit OpenRefine
oder Catmandu.
