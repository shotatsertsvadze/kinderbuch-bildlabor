# Arbeitsauftrag: Kinderbuch-Bildlabor

Du unterstützt mich, Shota Tsertsvadze, beim Aufbau eines kleinen, fachlich nachvollziehbaren Portfolio-Projekts: **Kinderbuch-Bildlabor – Erschließung und Qualitätsprüfung historischer Illustrationen**. Arbeite als pragmatischer Python-Entwickler mit Verständnis für bibliothekarische Metadaten. Erkläre mir fachliche Entscheidungen verständlich, damit ich die Anwendung und ihre Ergebnisse selbst erläutern kann.

## Zweck und Rahmen

Ich habe mich auf eine Stelle im Datenmanagement einer Kinder- und Jugendbuchabteilung beworben. Relevante Aufgaben sind Digitalisierung und OCR/HTR, Forschungsdaten, OAI-Harvesting, Testdatensets und Ground Truth, Annotation grafischer Materialien sowie Mapping und Konversion. Das Projekt soll konkrete Arbeit an einer kleinen Stichprobe zeigen. Es ist ein eigenständiger Prototyp auf Basis öffentlich zugänglicher Quellen; interne Abläufe oder Probleme der Bibliothek sind nicht bekannt.

Für meine fachliche Mitarbeit stehen täglich 1–2 Stunden zur Verfügung. Ziel der ersten Vorführversion: sechs echte Illustrationen aus zwei Büchern, später zwölf aus ungefähr drei Büchern. **Vorhanden ist bisher nur ein Pilotdatensatz.** Erzeuge keine weiteren Sammlungsobjekte oder geprüften Annotationen als Füllmaterial. Ein brauchbarer Ablauf mit diesem einen Beispiel kommt zuerst.

Alle Oberflächentexte, fachlichen Beschreibungen, Berichte und Dokumentationen werden auf Deutsch geschrieben. Technische Bezeichner dürfen Englisch sein. Verwende keine Emojis. Historische Quellen werden originalgetreu wiedergegeben.

## Zuerst die beigefügten Dateien lesen

- `pilot_001.json`: lokales Arbeitsmodell, kein standardisiertes Austauschformat. Enthält Quellenbezüge, bibliografische Angaben, Beschreibung, drei vorgeschlagene Bildregionen und Prüfhinweise.
- `pilot_001_image_info.json`: originale IIIF-Image-API-Antwort; Ausgangsbild 1183 × 1950 Pixel.
- `pilot_001_page.jpg`: vollständiges Ausgangsbild dieser Größe.
- `pilot_001_title.jpg`: unveränderter IIIF-Ausschnitt der Titelregion, 550 × 80 Pixel.
- `pilot_001_title_ocr.json`: tatsächlich ausgeführter OCR-Versuch mit Tesseract 5.5.1, deutschem Modell und dokumentierter Modellrevision, Parametern und Prüfsummen.
- `pilot_001_oai_mets.xml`: echte OAI-PMH-GetRecord-Antwort für PPN1814684999 mit METS/MODS. XML wurde geparst und auf Datensatzidentität sowie das Vorhandensein von METS/MODS geprüft; eine XSD-Validierung wurde bisher nicht ausgeführt.
- `MANIFEST.json`: Dateiinventar, Prüfsummen und Herkunft der zusätzlichen Quelldateien.

## Fachliche Entscheidungen am Pilotbeispiel

1. Die Quelle ist ein digitalisiertes gedrucktes Buch, kein Nachlassobjekt. Die Darstellung ist eine Illustration, kein nachgewiesener Comic.
2. Buchautor und Illustrator sind verschiedene Rollen. Der Illustrator ist bislang unbekannt und bleibt leer.
3. Scan 6 ist nicht automatisch Druckseite 6. `printed_page_number` bleibt unbekannt.
4. Sichtbar sind vier Personen. Die akzeptierten lokalen Suchbegriffe lauten `Personengruppe`, `Baum`, `Landschaft`. Eine familiäre Beziehung wurde nicht nachgewiesen. Die Begriffe sind keine geprüften GND-Verknüpfungen.
5. Bibliografische Angaben aus Colibri nennen Augsburg und J. A. Schlosser's Buch- und Kunsthandlung. Auf dem Bildblatt wurde vorläufig eine Verlagsangabe zu Setzer in Rottweil gelesen. Beide Angaben mit ihrem jeweiligen Bezug bewahren; den Unterschied zur Prüfung anzeigen, nicht automatisch als Katalogfehler werten oder einen Wert überschreiben.
6. Titeltranskription: `Die Heimath in Amerika.` Die historische Schreibweise `Heimath` bleibt erhalten. Die Transkriptionsprüfung insgesamt ist noch nicht abgeschlossen; insbesondere die Lesung der Verlagsinitialen ist vorläufig.
7. Tatsächliche OCR-Ausgabe, einschließlich Zeichen und abschließendem Zeilenumbruch: `‘Die Geimatly „ir Amerika.\n`. Nicht verbessern und anschließend als ursprüngliche OCR-Ausgabe ausgeben.
8. Regionengrenzen sind Entwürfe. Akzeptierte Suchbegriffe bedeuten nicht, dass Regionen oder sämtliche Transkriptionen abschließend geprüft wurden. Prüfstati bleiben getrennt.
9. Quellwerk-Rechte und Lizenz des Colibri-Datensatzes unterscheiden. Herkunft, Rechteangaben und Namensnennung bei jedem Export erhalten. Den gesamten Colibri-Bildbestand nicht herunterladen.

## Technische Richtung

Meine vorgeschlagene Grundlage ist eine kleine lokale Anwendung mit Python und Streamlit. Prüfe bei der Umsetzung die aktuellen stabilen Versionen und offiziellen APIs, dokumentiere die tatsächlich eingesetzten Versionen und halte die Abhängigkeiten klein. Verwende kurze, verständliche Module und Funktionen. Eine lokale dateibasierte Ablage genügt zunächst. Änderungen müssen nach einem Neustart erhalten bleiben; die beigefügten Quelldateien bleiben unverändert. Keine Anmeldung, Cloud-Datenbank oder kostenpflichtige externe API erforderlich.

Die Kerndemo muss mit den beigefügten Dateien ohne neue Netzabrufe und ohne erneute OCR laufen. Live-Abruf und erneute OCR sind getrennte Aktionen. Melde bei einem nicht erreichbaren Dienst einen verständlichen Abruffehler; ein solcher Fehler ist kein Beweis für fehlende oder falsche Metadaten.

## Erster Umsetzungsschritt: ein vollständiger Ablauf mit einem Objekt

1. Lade das Pilotobjekt mit dem zugehörigen Bild. Zeige deutsche Beschreibungen, Quellenlink, Buchdaten und offene Prüfhinweise.
2. Zeige die drei Regionen auf dem vollständigen Bild und als Ausschnitte. Die Pixelkoordinaten beziehen sich immer auf 1183 × 1950 Pixel, unabhängig von der Bildschirmgröße. Einfache bearbeitbare Koordinatenfelder mit Vorschau genügen zunächst.
3. Erlaube die Bearbeitung von Beschreibung und Suchbegriffen sowie eine ausdrückliche Bestätigung einzelner Prüfbereiche. Speichere Änderungen mit Bezug zum Quellobjekt und zeige nach einem Neustart dieselben Werte an.
4. Stelle die gespeicherte OCR-Ausgabe und die vorläufige Transkription gegenüber. Kennzeichne den Prüfstand sichtbar. Stelle keine vorläufige Transkription als geprüfte Ground Truth dar.
5. Prüfe fehlende Pflichtangaben, doppelte Objekt-IDs, unzulässige Regionengrenzen und offene Prüfentscheidungen. Unbekannte optionale Angaben wie der Illustrator sind kein pauschaler Validierungsfehler. Unterscheide technische Fehler, fachliche Prüfhinweise und noch nicht ausgeführte Prüfungen.
6. Exportiere den bearbeiteten Datensatz als JSON und eine nachvollziehbare Übersicht als CSV. Lade den JSON-Export erneut und prüfe, dass Unicode, Nullwerte, Regionen und Prüfstände erhalten bleiben.

Setze diesen Abschnitt zuerst um und überprüfe ihn mit dem echten Pilotobjekt. Wenn deine Umgebung keine Dateien ausführen kann, benenne das ausdrücklich und liefere den vollständigen ausführbaren Code samt kurzen lokalen Prüfschritten. Behaupte keine ausgeführten Tests oder funktionierende Oberfläche ohne entsprechende Prüfung.

## Danach schrittweise ergänzen

- **OAI-PMH und Mapping:** zunächst die gespeicherte Antwort auswerten, anschließend einen begrenzten Live-GetRecord-Abruf anbieten. OAI-Hülle und eingebettete METS/MODS-Struktur unterscheiden. Eine kleine dokumentierte Zuordnung von ausgewählten MODS-Feldern zum lokalen Modell erstellen. Rollen, Sprachangaben und Quellenbezüge erhalten; mehrdeutige oder wiederholte Felder nicht stillschweigend verwerfen. Das Ergebnis mit dem Pilotdatensatz vergleichen. Unterschiede nicht ungeprüft vereinheitlichen.
- **Datenpflege:** eine tatsächliche kleine OpenRefine-Bereinigung mit Ausgangsdatei, überprüftem Ergebnis und exportierter Operationshistorie dokumentieren. Zusätzlich eine kleine ausführbare Catmandu-Konversion mit Eingabe, Mapping und Ausgabe vorbereiten und prüfen. Nicht ausgeführte Schritte ausdrücklich als ausstehend kennzeichnen. Mein bisheriger synthetischer OpenRefine-Übungsdatensatz liegt diesem Paket nicht bei.
- **OCR und Referenzdaten:** erneuten OCR-Lauf reproduzierbar anbieten. Erst nach ausdrücklicher fachlicher Freigabe Referenztexte als Ground Truth kennzeichnen. Für freigegebene Stichproben CER/WER mit dokumentierter Behandlung von Leerzeichen, Unicode, Interpunktion und Zeilenumbrüchen berechnen; keine unbemerkte Modernisierung der Orthografie. Ergebnisse nur auf die ausgewerteten Textregionen beziehen. Der vorhandene Versuch ist kein Training oder umfassender Modellvergleich.
- **Regionsexport:** aus den geprüften lokalen Regionen W3C-Web-Annotation-JSON-LD mit Quellenbild-URI und passendem FragmentSelector erzeugen. Bildabmessungen und Pixelbezug prüfen. Nicht mit einer IIIF-Manifest-Erstellung oder allgemeiner Standardkonformität gleichsetzen.
- **Dokumentation:** eine knappe Datenbeschreibung mit Auswahlkriterien, Provenienz, Rechten, Annotationsregeln, Prüfständen und Grenzen erstellen; dazu einen verständlichen deutschen Ergebnisbericht und einen Ablauf für eine dreiminütige Demonstration. README auf Einrichtung und Nutzung beschränken.

ALTO, TEI und HTR gehören zum fachlichen Umfeld, sind in dieser ersten Version aber noch keine implementierten Funktionen. Spätere Erweiterungen klar von ausgeführten Arbeiten trennen. Ein W3C-Annotationsexport allein ist keine ALTO-Datei. Eine erfolgreiche XML-Parseprüfung ist keine XSD-Validierung. Keine allgemeine RDA-/RNAB-Konformität behaupten.

## Erfolgskriterien und Arbeitsweise

- Beginne mit einer kurzen Bestandsaufnahme der tatsächlich gelesenen Dateien und höchstens fünf Umsetzungsschritten. Stelle nur Fragen, wenn eine fehlende Entscheidung den ersten Ablauf tatsächlich blockiert; entscheide Routinefragen begründet selbst.
- Arbeite in kleinen überprüfbaren Schritten. Prüfe insbesondere Koordinaten bei skalierter Darstellung, dauerhafte Speicherung, erneutes Laden exportierter Daten und die Trennung der Prüfstände. Ein Demoobjekt bleibt ein Demoobjekt; sechs echte Beispiele sind erst nach Auswahl und Prüfung vorhanden.
- Gib mir pro Schritt eine konkrete kleine fachliche Aufgabe, die ich selbst erledigen kann, und erkläre kurz ihren Zweck. Mein Ziel ist, die Entscheidungen und Ergebnisse im Bewerbungsgespräch zu verstehen und zu vertreten.
- Nenne am Ende, was tatsächlich funktioniert, welche Prüfungen ausgeführt wurden und welche fachlichen Entscheidungen noch offen sind. Keine erfundenen Qualitätswerte, Quellen, Nutzerbestätigungen oder Repositoriumsprüfungen.
- Veröffentliche nichts und versende keine Nachrichten. Eine später vorführbare lokale Version ist das erste Ziel.

## Quellen für die Umsetzung

- Originalansicht: https://digital.staatsbibliothek-berlin.de/werkansicht?PPN=PPN1814684999&PHYSID=PHYS_0006&DMDID=DMDLOG_0001
- Colibri: https://huggingface.co/datasets/SBB/Colibri
- SBB-Datenzugänge: https://lab.sbb.berlin/dc/
- OAI-PMH-Beispiel: https://oai.sbb.berlin/?verb=GetRecord&metadataPrefix=mets&identifier=oai:digital.staatsbibliothek-berlin.de:PPN1814684999
- Streamlit: https://docs.streamlit.io/get-started
- W3C Web Annotation: https://www.w3.org/TR/annotation-model/
- METS: https://www.loc.gov/standards/mets/
- MODS: https://www.loc.gov/standards/mods/
- Tesseract: https://tesseract-ocr.github.io/tessdoc/
- Catmandu: https://metacpan.org/pod/Catmandu
- OpenRefine: https://openrefine.org/docs

Lies jetzt die beigefügten Dateien und beginne mit dem ersten Umsetzungsschritt.
