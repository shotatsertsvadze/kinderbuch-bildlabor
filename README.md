# Kinderbuch-Bildlabor

Lokaler Prototyp zur Erschließung und Qualitätsprüfung von Illustrationen aus digitalisierten
Kinder- und Jugendbüchern des 19. Jahrhunderts (Staatsbibliothek zu Berlin, Colibri-Datensatz).
Stichprobe: sechs Illustrationen aus zwei Büchern, alle mit offenen Prüfständen.

Worum es geht und was fertig ist: [docs/PROJEKTUEBERSICHT.md](docs/PROJEKTUEBERSICHT.md).

## Einrichtung

Voraussetzung: [uv](https://docs.astral.sh/uv/). Python und alle Abhängigkeiten installiert uv selbst
aus der Sperrdatei `uv.lock`.

```bash
uv sync
```

Eingesetzte Versionen (geprüft am 06.11.2026, jeweils aktuelle Version auf PyPI):
Python 3.13.5, Streamlit 1.67.0, Pillow 13.0.0, pytest 9.2.0.

## Nutzung

```bash
uv run streamlit run app.py
```

Die Anwendung öffnet sich unter http://localhost:8501 und arbeitet ohne Internetverbindung.

1. Links unter „Prüfende Person“ den eigenen Namen eintragen. Er wird bei jeder Bestätigung gespeichert.
2. Auf der Startseite ein Objekt öffnen. Der Hinweis „Nächster Schritt“ nennt den nächsten offenen Prüfbereich.
3. Eingaben mit „Speichern“ übernehmen und Prüfungen mit „Bestätigen und speichern“ festhalten.
4. Im Reiter „Export“ JSON und CSV erzeugen und mit der Rückladeprüfung kontrollieren.

Ein Rundgang in drei Minuten: [docs/DEMO.md](docs/DEMO.md).

## Daten

- Quelldateien (werden nie verändert): `Kinderbuch_Bildlabor_Start/`, `sammlung/`
- Arbeitsstände: `data/work/<objekt-id>.json`
- Exporte: `exports/`
- Zurück zum Stand der Quelldatei: die Datei in `data/work/` löschen
- Probelauf mit getrenntem Datenordner, ohne die eigenen Arbeitsstände zu berühren:
  `BILDLABOR_DATA_DIR=/tmp/probe uv run streamlit run app.py`

Beschreibung der Stichprobe, Rechte und Annotationsregeln: [docs/DATENSATZ.md](docs/DATENSATZ.md).

## Tests

```bash
uv run pytest
```

Die Tests arbeiten in temporären Ordnern und berühren `data/work/` und `exports/` nicht.
