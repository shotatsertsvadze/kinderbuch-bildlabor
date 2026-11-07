# Kinderbuch-Bildlabor

**Wie lassen sich abweichende Bildklassifikationen in digitalisierten Kinderbüchern am Originalbild
prüfen, begründet entscheiden und mit ihrer Herkunft weitergeben?**

Lokaler Prototyp mit echten Daten der Staatsbibliothek zu Berlin (Colibri-Datensatz, METS/MODS,
IIIF-Scans). Fallstudie: fünf Illustrationen aus „Genovefa“ (Augsburg 1810), bei denen die manuelle und
die automatische Colibri-Klasse voneinander abweichen. Zweites Beispiel: „Die Heimath in Amerika“
(Augsburg 1850) mit Verlagsangabe, OCR-Ausgabe und Transkription.

Überblick: [docs/PROJEKTUEBERSICHT.md](docs/PROJEKTUEBERSICHT.md) ·
Rundgang in drei Minuten: [docs/DEMO.md](docs/DEMO.md)

## Installation

1. **uv installieren** (offizielle Anleitung: <https://docs.astral.sh/uv/getting-started/installation/>):
   - macOS und Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - alternativ mit Homebrew: `brew install uv`

   Danach ein neues Terminal öffnen und mit `uv --version` prüfen.
2. **ZIP entpacken** und im Terminal in den Ordner wechseln, zum Beispiel
   `cd ~/Downloads/kinderbuch-bildlabor`.
3. **Einrichten:** `uv sync --locked`. uv lädt dabei Python 3.13 und die Abhängigkeiten in genau den
   Versionen aus `uv.lock` (Streamlit 1.67.0, Pillow 13.0.0). Nur dieser Schritt braucht Internet.

## Starten

```bash
uv run streamlit run app.py
```

Der Browser öffnet <http://localhost:8501>. Die Anwendung arbeitet danach ohne Internetverbindung und
ist nur auf diesem Rechner erreichbar. Beenden mit `Strg+C` im Terminal.

## Wo anfangen

1. Links unter „Prüfende Person“ einen Namen eintragen.
2. Auf der Startseite **„Leitbeispiel öffnen: Genovefa, Scan 22“** wählen. Der Prüfpfad hebt
   den nächsten offenen Schritt hervor. Mit **„Bild prüfen“** öffnen Sie die Regionen, mit
   **„Klassen vergleichen“** die Colibri-Angaben und die Entscheidung mit Begründung.
3. „Zweites Beispiel öffnen“ zeigt Verlagsangabe und OCR bei „Die Heimath in Amerika“.

Begriffe wie *Endbestätigung* und *Ground Truth* erklärt die Startseite und die Stelle, an der sie
vorkommen; ausführlich in [docs/BEGRIFFE.md](docs/BEGRIFFE.md).

Zum Ausprobieren ohne Änderung der mitgelieferten Arbeitsstände einen eigenen Datenordner verwenden:

```bash
BILDLABOR_DATA_DIR=/tmp/bildlabor-probe uv run streamlit run app.py
```

(Windows PowerShell: `$env:BILDLABOR_DATA_DIR="$env:TEMP\bildlabor-probe"; uv run streamlit run app.py`)

## Daten

- Quelldateien (werden nie verändert): `Kinderbuch_Bildlabor_Start/`, `sammlung/`
- Arbeitsstände: `data/work/<objekt-id>.json`; Exporte: `exports/`. Beide entstehen erst beim Speichern.
- Vor jedem Überschreiben wird der bisherige Stand unter `data/work/.history/<objekt-id>/<sha256>.json`
  aufbewahrt. Das ersetzt keine Sicherung auf einem anderen Gerät.
- Zurück zum Quellstand: Server stoppen, die Arbeitsdatei in einen Archivordner verschieben (nicht
  löschen), neu starten.
- Mit `BILDLABOR_DATA_DIR` liegen Arbeitsstände und Exporte im angegebenen Ordner.

Stichprobe, Auswahlkriterien, Rechte und Annotationsregeln: [docs/DATENSATZ.md](docs/DATENSATZ.md).
Entscheidungen zum Aufbau: [docs/adr/](docs/adr/). Bezug zur Stelle: [docs/BEZUG_ZUR_STELLE.md](docs/BEZUG_ZUR_STELLE.md).

## Qualitätsprüfungen

```bash
uv run --locked ruff check --no-cache .
uv run --locked ruff format --check --no-cache .
uv run --locked mypy --cache-dir=/dev/null
uv run --locked python -B -m pytest -p no:cacheprovider -q
```

Die Tests arbeiten in temporären Ordnern und berühren `data/work/` und `exports/` nicht.
