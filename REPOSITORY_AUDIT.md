# Kinderbuch-Bildlabor: Repository-Audit

Stand: 15. November 2026. Read-only Audit; keine Implementierung oder Bereitstellung.

**Das Bildlabor ist ein überzeugender lokaler Portfolio-Prototyp, aber noch keine belastbar freigegebene öffentliche Live-Demo. Der kleinste glaubwürdige MVP sollte den geprüften Review-Ablauf zeigen, nicht sämtliche optionalen Integrationen anbieten.**

## 1. Gesamturteil und Prüfrahmen

| Priorität | Bewertung |
|---|---|
| Live Demo Readiness | Für eine betreute lokale Vorführung mit vorbereiteten Beispielen geeignet; öffentliche schreibende Nutzung noch nicht freigabereif. |
| Professional Credibility für SBB-IIIK-1-2026 | Fachlich überzeugend bei Quellenbezug, Metadatenvergleich, nachvollziehbaren Entscheidungen und Qualitätssicherung. Grenzen müssen ausdrücklich benannt werden. |
| Kleinster glaubwürdiger deploybarer MVP | Eine kuratierte, öffentlich nur lesbare Beispielsammlung mit Prüfpfad und bereinigten Ergebnisdateien. Schreibende Arbeit zunächst lokal oder zugangsbeschränkt. |

Während des Audits wurden keine Anwendung, Konfiguration oder realen Arbeitsdaten geändert. Kein Deployment, keine Installation und kein Paketbau wurden durchgeführt. Diese Berichtsdatei wurde anschließend auf ausdrücklichen Wunsch gespeichert.

Die bereits vorhandene, zuvor angeforderte Datei `repository-audit-plan.md` blieb beim Audit unverändert und erschien weiterhin als unversionierte Datei im Git-Status.

## 2. Architektur und Datenhaltung

Die Architektur passt zum **lokalen Ein-Server-Prototyp**:

- Streamlit stellt Sammlung und objektbezogene Prüfoberfläche bereit.
- Quellen liegen getrennt von Arbeitskopien und Exporten.
- `BILDLABOR_DATA_DIR` verlagert veränderliche Daten.
- Speicherung und Review-Logik berücksichtigen konkurrierende Bearbeitungen innerhalb eines Serverprozesses.
- Frühere Arbeitsstände werden vor Überschreibungen als historische Snapshots erhalten.

**Belege:** `app.py:load_collection`, `src/kinderbuch_bildlabor/store.py`, `src/kinderbuch_bildlabor/review.py`, `tests/test_store.py`, `tests/test_app.py`.

Wichtige Betriebsgrenzen:

- Mehrere Server mit gemeinsamem Datenverzeichnis sind nicht abgesichert.
- Das Öffnen älterer Arbeitskopien kann Migrationen speichern; ein bloßer App-Start ist deshalb nicht grundsätzlich schreibfrei.
- Die Anwendung benötigt checkout-relative Quellen und Assets. Ein erfolgreich gebautes Python-Paket allein beweist keine vollständige Deployment-Fähigkeit.

## 3. Funktionsumfang: implementiert ist nicht gleich nachgewiesen

| Funktion | Implementierung und Nachweis |
|---|---|
| Sammlung mit sechs Beispielen aus zwei Büchern | Implementiert; Sammlung und Navigation durch erfolgreiche AppTests abgedeckt. |
| Regionen, Beschreibung, Suchbegriffe, Transkription | Implementiert; Änderungen, Bestätigungen und Konfliktfälle automatisiert getestet. |
| Begründete Entscheidungen und Endbestätigung | Implementiert und getestet; ausdrücklich keine Ground-Truth-Freigabe. |
| Zweitprüfung | Implementiert und getestet; unterschiedliche Namenseingaben beweisen keine unabhängigen Personen. |
| JSON-/CSV-Export und Exportaktualität | Implementiert und getestet; Rückladeprüfung bezieht sich auf JSON, nicht auf sämtliche Exportformate. |
| Web Annotation und PAGE-XML | Implementiert; ausgewählte Strukturprüfungen bestehen. Importierte Objekte verursachen jedoch einen reproduzierten Fehler. |
| JPEG/PNG-Import | Implementiert; Veröffentlichung, Wiederladen und Duplikatverhalten getestet. |
| PDF-Import | Implementiert; Adapter mit simulierten Prozessantworten getestet. Kein realer Poppler-End-to-End-Nachweis in diesem Audit. |
| IIIF-Import | Implementiert für unterstützte einfache Presentation-2/3-Strukturen; keine Live-Interoperabilitätsfreigabe. |
| Lokale Tesseract-Zweitlesung | Implementiert; zentrale Prozessintegration mit Mocks getestet. |
| Ollama-Vorschläge | Implementiert; simulierte Antworten getestet, keine reale Modellqualität nachgewiesen. |
| GND-Kandidatensuche | Implementiert; Abruf und Cache mit simulierten Antworten getestet. Keine persistierte GND-Verknüpfung. |
| Ähnliche Illustrationen | Implementiert und mit synthetischen Bildern getestet; visuelle Ähnlichkeit, kein semantisches Verständnis. |

**Nicht als vorhandene Leistung darstellen:** vollständiges OAI-Harvesting, MODS-/ALTO-Export, XSD-validierte Standardkonformität, unabhängig freigegebene Ground Truth oder belastbare OCR-Qualitätsmessung gegen eine Referenz.

**Belege:** entsprechende Module unter `src/kinderbuch_bildlabor/` und `tests/test_imports.py`, `tests/test_annotations.py`, `tests/test_ocr.py`, `tests/test_proposals.py`, `tests/test_authority.py`, `tests/test_similar.py`.

## 4. Verifikation und konkreter Fehlerbefund

Die Prüfungen wurden mit deaktiviertem Bytecode und Cache sowie einem temporären Anwendungsdatenverzeichnis außerhalb des Repositories ausgeführt:

| Prüfung | Ergebnis |
|---|---|
| Ruff | Erfolgreich |
| Formatprüfung | 85 Dateien bereits formatiert |
| mypy | Keine Probleme in 43 Quelldateien |
| pytest | **234 bestanden**, 34,80 Sekunden |
| Git-Status vorher/nachher | Unverändert |

Diese Ergebnisse stammen aus dem Auditlauf vor Speicherung dieser Berichtsdatei.

### Reproduzierter Import-Export-Fehler

`imports.imported_record()` setzt `source.image_info_url` auf `None`.

Sowohl `annotations.annotation_page()` als auch `pagexml.page_xml()` rufen darauf `.removesuffix("/info.json")` auf. Beide Aufrufe wurden mit einem ausschließlich im Speicher erzeugten Importdatensatz geprüft:

```text
AttributeError: 'NoneType' object has no attribute 'removesuffix'
```

**Auswirkung:** `actions.py:run_export` schreibt zunächst JSON und CSV und erzeugt anschließend Annotationen und PAGE-XML. Der Fehler kann somit einen teilweise geschriebenen Export hinterlassen. Abgefangen wird dort lediglich `OSError`, nicht dieser `AttributeError`.

Der bestehende Test `test_imported_exports_preserve_identity_and_unknowns` prüft JSON und CSV, aber nicht den vollständigen UI-Exportablauf.

**Priorität: P0 für jede Demo, die Import → Export verspricht.**

Die 234 erfolgreichen Tests sind deshalb ein guter Qualitätsnachweis, aber kein Beweis für lückenlose Ende-zu-Ende-Funktionalität.

## 5. Datenqualität, Standards und wissenschaftliche Aussagekraft

Besonders überzeugend sind:

- getrennte Bestätigungen je Prüfbereich;
- Invalidierung betroffener Bestätigungen nach Änderungen;
- begründete Entscheidungen statt Löschen widersprüchlicher Evidenz;
- Quellenbezug und erhaltene Herkunft;
- Unterscheidung zwischen technischem Fehler, fachlichem Hinweis und nicht ausgeführter Prüfung;
- Exportaktualität über Änderungsgeschichte statt nur Zeitstempel.

**Belege:** `src/kinderbuch_bildlabor/review.py`, `validate.py`, `export.py`, `oai.py` und zugehörige Tests.

Die Standards sind enger zu beschreiben als eine vollständige Integrationsplattform:

- **OAI-PMH:** Auswertung gespeicherter `GetRecord`-Antworten, kein laufender Harvester.
- **METS/MODS:** Lesen, Mapping und Vergleich; kein nachgewiesener standardvalidierter Schreibworkflow.
- **Web Annotation:** Bilddienstadresse als Ziel, nicht automatisch eine Presentation-Canvas-ID.
- **PAGE-XML:** Textregionen und Texte werden serialisiert; erfolgreiche XML-Strukturtests ersetzen keine Schema- oder Zielsystemvalidierung.
- **CER/WER:** Abstand zur aktuellen Arbeitstranskription, nicht zwingend Fehlerquote gegenüber verifizierter Ground Truth.

Die sechs Beispiele demonstrieren einen Arbeitsablauf. Sie tragen keine repräsentative Aussage über den gesamten Colibri-Bestand.

## 6. Live-Demo-Sicherheit, Datenschutz und Rechte

### Technische Bewertung

Positiv:

- Streamlit bindet standardmäßig an `localhost`.
- Nutzungsstatistik ist deaktiviert.
- Schriften werden lokal ausgeliefert.
- IIIF-Abrufe prüfen öffentliche Netzwerkziele, validieren Weiterleitungen und pinnen die geprüfte Zieladresse.
- Downloadgrenzen und Zeitlimits sind vorhanden.

**Belege:** `.streamlit/config.toml`, `src/kinderbuch_bildlabor/import_transport.py`.

Für öffentliche Nutzung reicht das nicht:

- Die Prüfperson ist eine Namenseingabe, keine authentifizierte Identität.
- Eine benutzerbezogene Trennung gemeinsam gespeicherter Arbeitsstände ist nicht nachgewiesen.
- Import, OCR, Modellaufrufe und Export benötigen für öffentliche Nutzung ein belastbares Ressourcen- und Berechtigungskonzept.
- Backup-Downloads können Namen und gesamte Prüfarbeit enthalten.

### Rechtliche Einordnung

Die Quelldatensätze unterscheiden **Public Domain Mark 1.0** und **CC BY 4.0** für Colibri. Diese Angaben dürfen nicht zu einer pauschalen Lizenz für alle Inhalte zusammengezogen werden. Für lokale Schriften liegen OFL-Dateien vor.

**Belege:** `Kinderbuch_Bildlabor_Start/pilot_001.json`, `sammlung/genovefa/scan_022.json`, `static/fonts/OFL-*.txt`.

Vor öffentlicher Bereitstellung sind mindestens zu klären:

- Betreiber, Hosting und gegebenenfalls Anbieterkennzeichnung;
- personenbezogene Daten in Prüfprotokollen, Downloads und Serverlogs;
- Rechtsgrundlage, Datenschutzhinweise und Aufbewahrung;
- vollständige Attribution und Rechte für tatsächlich veröffentlichte Materialien;
- anwendbare Barrierefreiheitsanforderungen.

Das ist keine Feststellung, dass jede genannte Pflicht in jeder Hostingform gleichermaßen gilt. Ohne Betreiber- und Nutzungskontext ist eine rechtliche Freigabe nicht möglich. Ein Cookie-Banner ist nicht automatisch erforderlich.

## 7. Sicherung, Wiederherstellung und Betriebsfähigkeit

Das Projekt verfügt über mehr als eine bloße Exportfunktion:

- historische Arbeitskopien;
- ZIP-Sicherung von Arbeitsständen, Importen und Exporten;
- Prüfsummenprüfung;
- Wiederherstellung in einen neuen beziehungsweise leeren Zielordner;
- Tests für manipulierte Pakete, Pfadtraversal und Schutz vorhandener Zieldaten.

**Belege:** `src/kinderbuch_bildlabor/backup.py`, `tests/test_backup.py`, `tests/test_store.py`.

**Nachgewiesen:** Wiederherstellungslogik funktioniert in temporären Testumgebungen.

**Nicht nachgewiesen:** regelmäßige externe Sicherung realer Daten, Restore einer tatsächlichen Betriebssicherung, Aufbewahrungsstrategie oder Wiederanlauf auf einer anderen Maschine.

Die vorbereiteten Quellen gehören nicht zum Backup-Paket. Für einen vollständigen Wiederanlauf müssen Repository, Quellen, Assets und passende Laufzeit zusätzlich verfügbar sein. Snapshots auf demselben Datenträger schützen nicht vor dessen Verlust.

## 8. Professional Credibility für SBB-IIIK-1-2026

Die öffentliche Originalausschreibung konnte in der bisherigen Suche nicht unabhängig gefunden werden. Die folgende Zuordnung bezieht sich deshalb auf die im Projekt dokumentierten Anforderungen, nicht auf eine unabhängig verifizierte Ausschreibungsfassung.

| Aufgabenfeld | Glaubwürdiger Projektbeleg |
|---|---|
| Erschließung grafischer Materialien | Bildregionen, Beschreibungen, Suchbegriffe und Klassifikationsentscheidungen |
| Datenqualität und Provenienz | Bestätigungszustände, Quellenbindung, dokumentierte Abweichungen |
| Metadatenmanagement | METS/MODS-Auswertung, Mapping und zeichengenauer Vergleich |
| Forschungsdatenbereitstellung | strukturierte Exporte und nachvollziehbare Bearbeitungsgeschichte |
| OCR-Qualitätssicherung | Bildvergleich und Zweitlesung; begrenzter als ein validierter Benchmark |
| Harvesting | Verständnis gespeicherter OAI-Antworten, aber kein implementierter Harvestingbetrieb |

### Verifizierbare deutsche Projektbeschreibung

> Das Kinderbuch-Bildlabor ist ein lokaler Streamlit-Prototyp zur quellenbezogenen Prüfung historischer Kinderbuchillustrationen. An sechs vorbereiteten Beispielen unterstützt es die Bearbeitung von Bildregionen, Beschreibungen, Suchbegriffen und Transkriptionen sowie den Vergleich gespeicherter METS/MODS-Metadaten. Änderungen, Bestätigungen und begründete Entscheidungen bleiben nachvollziehbar. Strukturierte Exporte dokumentieren den Bearbeitungsstand; eine Endbestätigung wird ausdrücklich nicht als Ground Truth ausgegeben.

**Größtes Glaubwürdigkeitsrisiko:** widersprüchliche Dokumentation.

- `app.py` behauptet weiterhin „kein Netzabruf, keine OCR“.
- `docs/BEZUG_ZUR_STELLE.md` nennt PAGE-Export als mögliche Erweiterung, obwohl er implementiert ist.
- Andere Dokumentationsstellen vermischen fehlende unabhängige Zweitprüfung mit einer durchaus vorhandenen Zweitprüfungsfunktion.

Für die Bewerbung ist präzise Begrenzung überzeugender als eine längere Featureliste.

## 9. Kleinster glaubwürdiger deploybarer MVP und Prioritäten

### Empfohlener Umfang

**Öffentliche Variante:** kuratierte, nur lesbare Demonstration der sechs Beispiele, mit Quellen, Prüfzuständen, einer nachvollziehbaren Entscheidung und bereinigten Ergebnisdateien.

**Interaktive Variante:** zunächst betreut oder zugangsbeschränkt, ein Serverprozess, isoliertes Datenverzeichnis und ausdrücklich temporäre Demo-Bearbeitungen.

Nicht erforderlich für den ersten glaubwürdigen MVP: freie Uploads, beliebige IIIF-URLs, Ollama, Live-GND, öffentliche OCR-Ausführung oder Mehrbenutzerbetrieb.

Diese Varianten sind **Empfehlungen für spätere Umsetzung**, keine bereits vorhandenen sicheren Betriebsmodi.

### Die fünf nächsten Maßnahmen, nach Priorität

1. **P0 — Import-Export-Bruch schließen oder Import aus dem MVP ausschließen.**
   Abnahme: vollständiger UI-Export eines importierten Objekts funktioniert mit definierten Bildreferenzen oder erklärt nicht unterstützte Formate ohne Ausnahme und irreführenden Erfolgsstatus.

2. **P0 — Öffentliche Betriebsgrenze festlegen und technisch nachweisen.**
   Abnahme: öffentliche Besucher können weder fremde Arbeitsstände verändern noch personenbezogene Protokolle oder Sicherungen abrufen; alternativ bleibt die Demo zugangsbeschränkt.

3. **P1 — Den kuratierten Demo-Pfad auf der Zielumgebung abnehmen.**
   Abnahme: sauberer Start mit vollständigen Assets; Sammlung → Quelle → Entscheidung → Ergebnis funktioniert ohne optionale Dienste; Tastaturbedienung und schmale Ansicht werden praktisch geprüft.

4. **P1 — Veröffentlichung fachlich und rechtlich konsistent machen.**
   Abnahme: Dokumentation unterscheidet implementiert, getestet, simuliert und geplant; öffentliche Dateien enthalten passende Rechteangaben und keine unbeabsichtigten personenbezogenen Daten.

5. **P2 — Wiederanlauf und Interoperabilität belastbar belegen.**
   Abnahme: Restore in isolierter Zielumgebung dokumentiert, externe Sicherung vorhanden und behauptete Exportkompatibilität mit Schema beziehungsweise tatsächlichem Zielsystem geprüft.
