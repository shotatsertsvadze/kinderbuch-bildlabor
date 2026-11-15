# 0008: GND-Suche nur auf Knopfdruck

Status: angenommen

Die App darf auf ausdrücklichen Knopfdruck lobid-gnd (`https://lobid.org/gnd/search`) nach Kandidaten fragen. Gesendet wird nur der eingetippte Suchbegriff; Antworten liegen im Zwischenspeicher unter `<Datenordner>/authority/`.

- Treffer sind Vorschläge. Sie verändern keinen Datensatz, bestätigen nichts und verknüpfen nichts.
- Der Prüfpunkt `GND_LINKING` bleibt „nicht ausgeführt“, solange keine bestätigte Verknüpfung existiert.
- Ohne Klick findet kein Netzwerkzugriff statt (siehe ADR 0007 für den lokalen Modellaufruf).
