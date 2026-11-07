# 0001 Quellen bleiben unveränderlich

Status: gültig

Kontext: Die Beispieldaten sind Belege. Wer sie bearbeitet, kann nicht mehr zeigen, was ursprünglich vorlag.

Entscheidung: Quelldateien werden nie geschrieben. Bearbeitungen stehen in einer Arbeitskopie je Objekt mit Dateiname und Prüfsumme der Quelle und mit Änderungsprotokoll. Der Katalog legt die Quellen fest.

Folgen: Ändert sich eine Quelle, meldet die Validierung es. Tests und Vorführungen nutzen einen eigenen Datenordner (`BILDLABOR_DATA_DIR`).
