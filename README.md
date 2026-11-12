# Kinderbuch-Bildlabor

**Wie lassen sich abweichende Bildklassifikationen in digitalisierten Kinderbüchern am Originalbild
prüfen, begründet entscheiden und mit ihrer Herkunft weitergeben?**

Lokaler Prototyp mit Daten der Staatsbibliothek zu Berlin (Colibri-Datensatz, METS/MODS, IIIF-Scans).
Die Anwendung arbeitet mit sechs vorbereiteten Beispielen aus zwei Büchern und kann eigene Bücher
importieren (siehe „Eigene Bücher und lokale OCR“).

**[Projektüberblick](docs/PROJEKTUEBERSICHT.md)** · **[Geprüftes Beispiel](docs/ergebnis/README.md)** ·
**[Demo ansehen](docs/DEMO.md)**

## Einrichtung

1. **uv installieren** (offizielle Anleitung: <https://docs.astral.sh/uv/getting-started/installation/>):
   - macOS und Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - alternativ mit Homebrew: `brew install uv`

   Danach ein neues Terminal öffnen und mit `uv --version` prüfen.
2. **Projektordner bereitstellen:** das Repository klonen oder auf GitHub über „Code“ → „Download ZIP“
   herunterladen und entpacken (ein erhaltenes Übergabe-ZIP ebenso), dann im Terminal in den Ordner
   wechseln, zum Beispiel `cd ~/Downloads/kinderbuch-bildlabor`.
3. **Einrichten:** `uv sync --locked`. uv lädt dabei Python 3.13 und die Abhängigkeiten in genau den
   Versionen aus `uv.lock` (Streamlit 1.67.0, Pillow 13.0.0). Nur dieser Schritt braucht Internet.

## Starten

```bash
uv run streamlit run app.py
```

Der Browser öffnet <http://localhost:8501>. Die Anwendung arbeitet danach ohne Internetverbindung und
ist nur auf diesem Rechner erreichbar. Beenden mit `Strg+C` im Terminal.

Für eine eigene Prüfung, die von anderen Arbeitsständen getrennt bleibt, einen eigenen Datenordner
verwenden:

```bash
BILDLABOR_DATA_DIR=/tmp/bildlabor-probe uv run streamlit run app.py
```

(Windows PowerShell: `$env:BILDLABOR_DATA_DIR="$env:TEMP\bildlabor-probe"; uv run streamlit run app.py`)

## Nutzung

1. Auf der Startseite **„Leitbeispiel öffnen: Genovefa, Scan 22“** wählen.
2. Im Prüfpfad unter „Prüfende Person“ einen Namen eintragen. Der Prüfpfad nennt den aktuellen
   Schritt und die nächste Handlung, zählt die Prüfbereiche des Objekts (bestätigt, als Entwurf
   gespeichert, offen) und zeigt den Stand der Endbestätigung. Nach jedem Speichern führt
   **„Weiter“** zum nächsten Schritt; die Reiter bleiben zum Nachsehen erreichbar.
3. „Zweites Beispiel öffnen“ zeigt Verlagsangabe und OCR bei „Die Heimath in Amerika“.

Ein frisch gestarteter Datenordner zeigt alle sechs Beispiele im Quellstand, also ungeprüft. Das
geprüfte Beispiel steht davon getrennt auf der Startseite und unter
[docs/ergebnis/](docs/ergebnis/README.md). Begriffe wie *Endbestätigung* und *Ground Truth* erklärt
[docs/BEGRIFFE.md](docs/BEGRIFFE.md).

## Eigene Bücher und lokale OCR

- **Import:** Startseite → „Eigenes Buch importieren“: JPEG/PNG, PDF oder öffentliche IIIF-Manifest-URL
  (Presentation 2/3; nur einfache Bildseiten, nur auf ausdrücklichen Knopfdruck aus dem Netz). Importierte
  Bücher liegen vollständig unter `data/imports/` und funktionieren danach offline. Unbekannte Angaben
  bleiben unbekannt; OAI/METS-, IIIF-Bildinfo- und Colibri-Prüfungen erscheinen als „nicht ausgeführt“.
- **PDF** braucht lokal Poppler (`pdfinfo`, `pdftoppm`; macOS: `brew install poppler`).
- **Regionen zeichnen:** Reiter „Regionen“ → Rahmen auf dem Scan ziehen, verschieben, mit Umschalt mehrere
  wählen; Pfeiltasten und Zahlenfelder sind gleichwertige Alternativen. Gespeichert wird erst ausdrücklich.
- **Zweite Lesung:** Textregionen können mit lokalem Tesseract (`brew install tesseract`, Modelle nach
  Bedarf; optional `BILDLABOR_TESSERACT`, `BILDLABOR_TESSDATA`) erneut gelesen werden. Das Ergebnis
  ist ein Vergleichstext, keine Bewertung; ohne Tesseract bleibt die manuelle Transkription nutzbar.

**Daten:** Quelldateien in `Kinderbuch_Bildlabor_Start/` und `sammlung/` werden nie verändert.
Arbeitsstände (`data/work/`) und Exporte (`exports/`) entstehen erst beim Speichern, mit
`BILDLABOR_DATA_DIR` im angegebenen Ordner. Vor jedem Überschreiben bleibt der bisherige Stand unter
`data/work/.history/` erhalten; das ersetzt keine Sicherung auf einem anderen Gerät. Zurück zum
Quellstand: Server stoppen, die Arbeitsdatei in einen Archivordner verschieben (nicht löschen), neu
starten.

## Qualitätsprüfungen

```bash
uv run --locked ruff check --no-cache .
uv run --locked ruff format --check --no-cache .
uv run --locked mypy
uv run --locked python -B -m pytest -p no:cacheprovider -q
```

Die Befehle gelten für macOS, Linux und Windows. mypy legt seinen Zwischenspeicher in `.mypy_cache/`
ab; den Ordner markiert mypy selbst als von Git ignoriert, er kann jederzeit gelöscht werden. Die
Tests arbeiten in temporären Ordnern und berühren `data/work/` und `exports/` nicht.

## Weitere Dokumente

[Datensatz und Auswahl](docs/DATENSATZ.md) · [Offene Punkte](docs/OFFENE_PUNKTE.md) ·
[Architekturentscheidungen](docs/adr/) · [Abnahmebericht](docs/ABNAHME_2026-11-07.md) ·
[Bezug zur Stelle](docs/BEZUG_ZUR_STELLE.md)
