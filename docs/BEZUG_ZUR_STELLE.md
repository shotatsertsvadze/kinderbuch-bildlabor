# Bezug zur Stelle „Bibliothekar:in für Datenmanagement“ (SBB-IIIK-1-2026)

Was das Projekt tatsächlich zeigt, mit Fundstelle. Geplantes steht getrennt darunter.

## Gezeigt

| Aufgabe laut Ausschreibung | Belegt im Projekt | Wo |
|---|---|---|
| Annotation grafischer Materialien (Illustrationen) | Regionen als Rechtecke in Originalpixeln; sachliche Bildbeschreibung; projektlokale Suchbegriffe; Ablauf für begründete Klassifikationsentscheidungen zu fünf abweichenden Colibri-Klassen, davon eine (Scan 22) entschieden und exportiert; Herkunft jedes Vorschlags | Reiter Klassifikation, Regionen, Beschreibung; [ergebnis/](ergebnis/README.md) |
| Qualitätssicherung von Digitalisierung und OCR | IIIF-Bildinformation gegen Bilddatei und Datensatz geprüft; Prüfsummen aller Quelldateien; eine gespeicherte Tesseract-Ausgabe mit Modellrevision, Parametern und Eingabeprüfsumme neben der Lesung am Bildausschnitt; Validierung in technische Fehler, fachliche Hinweise, nicht ausgeführte Prüfungen und begründet entschiedene Hinweise | Transkription, Prüfung |
| Testdatensets, Transkription und Annotation von Ground Truth, Dokumentation | dokumentierte Stichprobe mit nachvollziehbarem Auswahlkriterium, gegen die Colibri-CSV geprüft; zeichengetreue Transkription mit getrenntem Prüfstand je Feld; ausdrücklich keine Ground-Truth-Freigabe ohne Zweitprüfung | `docs/DATENSATZ.md`, Transkription |
| Forschungsdaten bereitstellen | JSON-Export mit vollständigem Arbeitsstand, Entscheidungen, Rechten (PDM 1.0, CC BY 4.0) und Protokoll; CSV je Region und für die Sammlung; Rückladeprüfung; Aktualität eines Exports über die Änderungsgeschichte | Export, Startseite |
| Harvesting über OAI-Schnittstelle | Auswertung zweier gespeicherter OAI-PMH-`GetRecord`-Antworten (`metadataPrefix=mets`, Set `kinder.und.jugendbuecher`): Hülle, Kennung, Datumsstempel | Bibliotheksdaten |
| Mapping, Konkordanz, Konversion; METS, MODS | Buch-MODS über die DMDID der logischen METS-Wurzel; Seitenbezug über `smLink` und `ORDERLABEL`; 27 XPath-Regeln, jedes MODS-Textelement mit exaktem Pfad, wiederholte Felder und Rollen erhalten; zeichengenauer Abgleich mit Colibri; Konversion Colibri-Zeile → Arbeitsmodell → JSON/CSV | Bibliotheksdaten, Export |
| KI-Prompting (erwünscht) | KI-Entwürfe für Beschreibungen sind als solche gekennzeichnet und gelten erst nach menschlicher Bestätigung | Beschreibung |

## Tatsächlicher Umfang der Standards

- **OAI-PMH:** zwei einzelne, am 06.11.2026 abgerufene `GetRecord`-Antworten, lokal ausgewertet. Kein
  Live-Abruf, kein `ListRecords`, keine Resumption Tokens, kein inkrementelles Harvesting.
- **METS/MODS:** gelesen und gemappt, nicht geschrieben. XML-Parsing und inhaltliche Prüfungen, keine
  XSD-Validierung. Export erfolgt als JSON und CSV, nicht als MODS.
- **IIIF:** gespeicherte Image-API-`info.json` und Vollbilder. Regionen nutzen dieselbe Form
  `x,y,w,h` in Originalpixeln wie der IIIF-Regionsparameter; der gespeicherte OCR-Eingabeausschnitt
  wurde genau so abgerufen (`400,1640,550,80`). Keine Presentation-API-Manifeste, keine Live-Kacheln,
  kein Annotationsexport im IIIF- oder W3C-Format.
- **OCR:** ein einzelner, dokumentierter Tesseract-5.5.1-Lauf (Modell `deu`, tessdata_best) auf dem
  Titelausschnitt. Keine neue OCR in der Anwendung, kein ALTO, keine CER/WER-Bewertung.

## Nicht gezeigt, als Erweiterung denkbar

Live-Harvesting über OAI-PMH; XSD-Validierung; Export als MODS, ALTO, PAGE oder W3C Web Annotation;
GND-Verknüpfung der Suchbegriffe; CER/WER nach Freigabe einer Referenztranskription; HTR;
Massenbearbeitung mit OpenRefine oder Catmandu; Zweitprüfung durch eine zweite Person.
Workshops und Öffentlichkeitsarbeit sind nicht Gegenstand des Prototyps.
