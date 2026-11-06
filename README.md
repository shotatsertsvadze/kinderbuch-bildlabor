# Kinderbuch-Bildlabor

Lokaler Prototyp zur Erschließung und Qualitätsprüfung historischer Kinderbuch-Illustrationen.
Derzeit ein Pilotobjekt (PPN1814684999, Scan 6) mit offenen Prüfständen.

## Einrichtung

Voraussetzung: [uv](https://docs.astral.sh/uv/). Python 3.13 und die Abhängigkeiten installiert uv selbst.

```bash
uv sync
```

Eingesetzte Versionen (Stand 2026-11-06): Python 3.13.3, Streamlit 1.67.0, Pillow 13.0.0, pytest 9.2.0 (Oberflächentests mit Streamlit AppTest).

## Nutzung

```bash
uv run streamlit run app.py
```

Die Anwendung öffnet sich unter http://localhost:8501. Sie liest nur die Dateien in
`Kinderbuch_Bildlabor_Start/` (ohne Netzabruf und ohne neue OCR) und verändert diese nicht.

- Bearbeitungen und Bestätigungen: `data/work/<objekt-id>.json`
- Exporte (JSON und CSV): `exports/`
- Zurück zum Stand der Quelldatei: `data/work/<objekt-id>.json` löschen
- Probelauf mit getrenntem Datenordner: `BILDLABOR_DATA_DIR=/pfad/zum/ordner uv run streamlit run app.py`
- Nach einer Codeänderung die Anwendung neu starten

## Tests

```bash
uv run pytest
```
