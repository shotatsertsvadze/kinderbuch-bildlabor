# 0007: Lokale Modellvorschläge sind ungeprüfte Entwürfe

Status: angenommen

Auf ausdrücklichen Knopfdruck darf die App ein lokal laufendes Ollama-Modell (`localhost:11434`, Modell über `BILDLABOR_OLLAMA_MODEL`) um einen Rahmen und eine deutsche Beschreibung bitten. Das ist keine Ausnahme von „kein Live-Abruf“: Das Bild verlässt den Rechner nicht, andere Adressen werden nicht angesprochen.

- Der Vorschlag steht nur in Eingabefeldern und in der Anzeige. Er speichert nichts, bestätigt nichts und hebt keine Bestätigung auf.
- Läuft Ollama nicht, bleibt die Funktion verborgen.
- Der Vorschlag ist keine Ground Truth; erst eine ausdrückliche Bestätigung je Bereich (ADR 0002) zählt.
