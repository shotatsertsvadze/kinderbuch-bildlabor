# 0004 Aktualität eines Exports folgt der Änderungsgeschichte

Status: gültig

Kontext: Zeitstempel sagen nicht, ob ein Export aus derselben Arbeitskopie stammt, etwa nach einem Zurücksetzen oder einer kopierten Datei.

Entscheidung: Das Änderungsprotokoll des Exports muss ein Anfang des Änderungsprotokolls der Arbeitskopie sein. Bleibt nichts übrig, ist der Export aktuell. Bleibt ein Rest, ist er veraltet. Gibt es keinen gemeinsamen Anfang, ist er fremd. Die Rückladeprüfung beschreibt nur aktuelle Exporte.

Folgen: Ein Export wird nie nach Dateizeit beurteilt. Eine gekürzte oder neu begonnene Historie fällt als fremd auf.
