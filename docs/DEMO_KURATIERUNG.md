# Demonstrationsstand für die öffentliche Demo anlegen

Die öffentliche Demo (`BILDLABOR_DEMO=1`) zeigt den Ordner `demo/`. Er entsteht aus einer eigenen
Prüfsitzung. Jede Bestätigung und Entscheidung darin trifft die prüfende Person selbst am Bild;
das Werkzeug kopiert und prüft nur, es erzeugt keine Prüfungen.

## 1. Frische Prüfsitzung starten

```bash
BILDLABOR_DATA_DIR=/tmp/bildlabor-demo-build uv run streamlit run app.py
```

Der Ordner muss neu und leer sein. So gelangen weder ältere Testeinträge noch private Arbeitsstände
in die Demo. Nichts importieren: Importe werden nicht übernommen.

## 2. Selbst prüfen

- Im Prüfpfad unter „Prüfende Person“ genau `Shota Tsertsvadze` eintragen. Andere Schreibweisen
  werden beim Anlegen abgelehnt.
- Nur prüfen, was Sie tatsächlich am Bild und an den Quellen geprüft haben. Was offen bleibt, bleibt
  offen; auch das ist ein ehrlicher Demonstrationsstand.
- Der Prüfpfad führt je Objekt durch die Schritte: Rahmen prüfen, Klassen vergleichen, Beschreibung
  prüfen, Prüfung abschließen, exportieren. Begründungen in eigenen Worten schreiben; sie werden
  wörtlich veröffentlicht.
- Lokale OCR, Modellvorschläge und GND-Suche sind freiwillig. Gespeicherte Ergebnisse daraus werden
  mit veröffentlicht.
- Objekte, die Sie nicht anfassen, erscheinen in der Demo im Quellstand.

## 3. Jedes bearbeitete Objekt exportieren

Nach der letzten Änderung im Reiter „Export“ auf „JSON und CSV exportieren“ klicken. Der Reiter muss
„Export aktuell“ zeigen. Jede spätere Änderung verlangt einen neuen Export.

## 4. Demonstrationsstand anlegen

Streamlit beenden, dann im Projektordner:

```bash
uv run python -m kinderbuch_bildlabor.demo_data build /tmp/bildlabor-demo-build --bestaetigt-von "Shota Tsertsvadze"
```

Mit dem Namen bestätigen Sie, dass die Prüfungen von Ihnen stammen. Das Werkzeug bricht ab und
übernimmt nichts, wenn:

- ein Objekt keinen Export hat oder der Export nicht dem letzten Stand entspricht;
- die vier Exportdateien (JSON, CSV, Annotationen, PAGE-XML) nicht genau zusammenpassen;
- ein anderer Name als der zugelassene vorkommt;
- eine Arbeitskopie nicht auf der aktuellen Quelldatei beruht oder ein älteres Format hat;
- `demo/` schon besteht.

Übernommen werden nur Arbeitskopien und Exportsätze, kein Verlauf (`.history`), keine
Zwischenspeicher, keine Sicherungen. Dazu entstehen `README.md`, `LICENSES.md` (Rechte und
Namensnennung je Objekt), `PROVENANCE.md` (alle Bestätigungen und Entscheidungen mit Zeitpunkt) und
`MANIFEST.json` (Prüfsummen).

## 5. Offene Angaben ergänzen und prüfen

In `demo/LICENSES.md` die mit `OFFEN:` markierten Zeilen selbst ausfüllen (Lizenz der METS/MODS-Daten
nach den Bedingungen der Staatsbibliothek, Lizenz der eigenen Prüfangaben). Dann:

```bash
uv run python -m kinderbuch_bildlabor.demo_data check
BILDLABOR_DEMO=1 uv run streamlit run app.py
```

`check` muss „Geprüft: veröffentlichbar.“ melden. Danach die Demo im Browser durchsehen.

## Neu anlegen

`demo/` wird nie überschrieben. Für einen neuen Stand den alten Ordner wegsichern, dann ab Schritt 1.
