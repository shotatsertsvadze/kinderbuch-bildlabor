# Begriffe

Oberfläche und Dokumentation sind deutsch, der Code ist englisch. Pro Konzept gilt genau ein Wort je Schicht.

| Begriff (Oberfläche, Doku) | Im Code | Bedeutung |
|---|---|---|
| Objekt | `ObjectSource`, `record["id"]` | Eine Illustration mit Scan, Metadaten und Quelldateien, zum Beispiel `pilot-001`. |
| Quelle, Quelldateien | `ObjectSource` | Unveränderte Dateien aus dem Datensatz. Sie werden nie geschrieben. |
| Katalog | `sammlung/katalog.json` | Legt fest, welche Quelldateien zu welchem Objekt gehören. |
| Arbeitskopie | `data/work/<id>.json` | Datei mit allen Bearbeitungen eines Objekts; verweist mit Prüfsumme auf die Quelle. |
| Arbeitsstand | `working`, `record` | Der gespeicherte Inhalt der Arbeitskopie zu einem Zeitpunkt. Die Datei heißt immer Arbeitskopie. |
| Region | `regions` | Rechteck `[x, y, Breite, Höhe]` in Pixeln des Originalbildes. Für einen Teil des Bildes ohne Region: Bildausschnitt. |
| Beschreibung | `image_description` | Sichtbarer Bildinhalt ohne Deutung. |
| Suchbegriffe | `keywords_de` | Projektlokale Begriffe je Region; keine GND-Verknüpfung. |
| Transkription | `transcription` | Zeichengetreuer Text je Feld. Die OCR-Ausgabe steht getrennt daneben. |
| Prüfbereich (kurz: Bereich) | `review_areas` | Einheit, die einzeln bestätigt wird: Regionsgrenzen, Beschreibung, Suchbegriffe, jede Transkription. |
| Bestätigung | `confirm_*`, `review_log` | Ausdrückliche Bestätigung eines Prüfbereichs mit Name und Zeitpunkt. |
| Endbestätigung | `final_approval`, `FINAL_APPROVED`, Protokollart `final_review` | Bestätigung des ganzen Objekts. Zustände: Offen, Bereit zur Endbestätigung, Endbestätigt. |
| Ground Truth | | Geprüfte Referenz zur Bewertung. Wird hier nicht vergeben; auch die Endbestätigung ist keine. |
| Reiter „Prüfung“ | `check_view` | Zeigt die Validierung und die Endbestätigung. Das Wort „Prüfung“ allein meint nichts anderes. |
| Validierung, Befund | `validate`, `Finding` | Automatische Prüfung. Kategorien: technischer Fehler, fachlicher Hinweis, nicht ausgeführt. |
| Blocker | `approval_blockers` | Befunde, die die Endbestätigung sperren: technische Fehler und fachliche Hinweise. |
| Bibliotheksdaten | `library_view`, `oai` | METS/MODS aus der gespeicherten OAI-PMH-Antwort der Staatsbibliothek. |
| Colibri-Metadaten | `source` | Bibliografische Zeile aus dem Colibri-Datensatz. |
| Änderungsprotokoll, Prüfprotokoll | `change_log`, `review_log` | Jede Speicherung beziehungsweise jede Bestätigung. |
| Export, aktuell / veraltet / fremd | `export` | JSON und CSV. Aktuell: keine späteren Änderungen. Veraltet: spätere Änderungen. Fremd: andere Änderungsgeschichte. |
