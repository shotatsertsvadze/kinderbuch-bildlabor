# Kinderbuch-Bildlabor – Projektübersicht

## Leitfrage

**Wie lassen sich abweichende Bildklassifikationen in digitalisierten Kinderbüchern am Originalbild
prüfen, begründet entscheiden und mit ihrer Herkunft weitergeben?**

Der Colibri-Datensatz der Staatsbibliothek zu Berlin (53.533 Zeilen zu Abbildungen aus Kinder- und
Jugendbüchern) führt zu jeder Abbildung eine automatische Klasse und, wo vorhanden, eine manuelle
(Spalte „groundtruth“). Weichen beide ab, reicht keiner der beiden Werte allein. Jemand muss am
Original nachsehen, entscheiden, die Gründe festhalten und das Ergebnis so weitergeben, dass beide
Ausgangswerte und ihre Herkunft erhalten bleiben. Das Bildlabor zeigt diesen Ablauf an echten Daten.
Es ist ein lokaler Prototyp, kein Produktionssystem, und trifft keine Annahmen über interne Abläufe
der Bibliothek.

## Fallstudie: fünf Abbildungen aus „Genovefa“

Auswahlkriterium: alle Zeilen der Colibri-CSV zu „Genovefa“ (Augsburg 1810, PPN1772789429), die eine
manuelle Klasse tragen. Von 18 Zeilen zu diesem Buch sind es fünf; die übrigen 13 haben den Wert „-0“
statt einer manuellen Klasse. In allen fünf lautet die manuelle Klasse „Abbildung“, die automatische
weicht ab:

| Scan | Seite laut METS | manuell | automatisch |
|---|---|---|---|
| 14 | 8 | Abbildung | Druckermarke |
| 16 | 10 | Abbildung | Druckermarke |
| 17 | 11 | Abbildung | Exlibris |
| 22 | 16 | Abbildung | Karte |
| 85 | 79 | Abbildung | Exlibris |

Die Werte wurden am 07.11.2026 gegen die öffentliche Colibri-CSV geprüft (SHA-256 wie im Manifest).
Alle Aussagen gelten nur für diese fünf Beispiele; sie sagen nichts über die Fehlerquote von Colibri.

**Leitbeispiel Scan 22:** Eine gerahmte Illustration mitten im Fließtext zeigt zwei Figuren in einem
Gewölbe. Die automatische Klasse lautet „Karte“. Der Unterschied ist am Bild leicht nachvollziehbar.
Die Entscheidung trifft trotzdem die prüfende Person, nicht die Anwendung.

**Begründungsvorschlag zur Prüfung am Original:** Der Ausschnitt zeigt zwei Figuren in einem
gewölbten Innenraum mit einer Treppe links. Die szenische Darstellung entspricht der Klasse
„Abbildung“. Für die Klasse „Karte“ fehlen im Ausschnitt kartografische Merkmale. Der Vorschlag
entstand mit KI-Unterstützung und wartet auf die Bestätigung durch die prüfende Person. Die beiden
Colibri-Werte bleiben als Quellenangaben sichtbar.

## Was die prüfende Person sieht

1. **Original und Region:** den Scan in voller Auflösung (IIIF) mit der markierten Region in
   Originalpixeln sowie den Ausschnitt.
2. **Beide Quellangaben:** manuelle und automatische Colibri-Klasse mit Herkunft; keine wird überschrieben.
3. **Belege:** Prüfstand der Regionsgrenzen, Bildbeschreibung, Seitenbezug im METS, Link zur
   Originalansicht der Staatsbibliothek.
4. **Entscheidung:** Auswahl (manuelle Klasse trifft zu, automatische trifft zu, keine von beiden, nicht
   entscheidbar) mit Pflichtbegründung, Name und Zeitpunkt. Ändern sich später die Regionsgrenzen, wird
   die Entscheidung aufgehoben; das Protokoll behält sie.
5. **Weitergabe:** JSON mit vollständigem Arbeitsstand, Entscheidungen, Herkunft, Rechten und
   Protokoll; CSV mit beiden Klassen, Entscheidung, Begründung, Person und Zeitpunkt. Eine
   Rückladeprüfung bestätigt, dass nichts verloren geht.

## Zweites Beispiel: „Die Heimath in Amerika“ (Augsburg 1850)

- **Zwei Kontexte, zwei Felder:** Colibri und MODS nennen als Verlag „J. A. Schlosser's Buch- und
  Kunsthandlung“, Augsburg. Auf dem Bildblatt steht eine Rottweiler Verlagsangabe (vorläufige Lesung
  „Verlag der I.P.Setzer'schen Buchhandlung in Rottweil.“). Beide bleiben in getrennten Feldern; der
  Unterschied ist ein Prüfhinweis, kein nachgewiesener Katalogfehler.
- **Lesung am Bild prüfen:** Die gespeicherte Tesseract-Ausgabe zum Bildtitel lautet
  „‘Die Geimatly „ir Amerika.“ (mit Zeilenumbruch). Daneben stehen der Bildausschnitt und die
  Arbeitstranskription „Die Heimath in Amerika.“ mit historischer Schreibweise. Die OCR wird gezeigt,
  nicht bewertet: Ohne freigegebene Referenz (Ground Truth) gibt es keine CER/WER.

## Grundsätze

- Quellen bleiben unverändert; Bearbeitungen stehen in einer Arbeitskopie mit Prüfsumme der Quelle.
- Jeder Prüfbereich wird einzeln mit Name und Zeitpunkt bestätigt; Änderungen setzen nur ihn zurück.
- Vorschläge (automatisch ermittelte Grenzen, Entwürfe des KI-Assistenten) tragen ihre Herkunft sichtbar.
- Belegte Unterschiede werden begründet entschieden, nicht weggeklickt. Technische Fehler und offene
  Pflichtprüfungen bleiben Sperren.
- Endbestätigung ist keine Ground-Truth-Freigabe.

## Stand und Grenzen

- Die Genovefa-Prüfungen stehen noch aus. Die persönliche Prüfung des Titelrahmens am Pilotobjekt
  ist im separaten Ergebnisexport des Übergabe-ZIP mit Name und Zeitpunkt dokumentiert. Die App
  öffnet für die eigene Prüfung den jeweiligen Quellstand. Siehe [OFFENE_PUNKTE.md](OFFENE_PUNKTE.md).
- Keine Live-Abfrage von OAI-PMH oder IIIF, keine neue OCR, keine XSD-Validierung, keine GND-Anbindung.
- Einzelplatzbetrieb: ein Server, gern mehrere Browserfenster.

## Beitrag

- **Shota Tsertsvadze:** Fragestellung und fachliche Anforderungen, Auswahl der Quellen, erste Lesung
  der Bildunterschriften des Pilotobjekts und Prüfung der Region „Bildtitel“ in der lokalen
  Arbeitskopie. Der separate Pilotexport enthält das zugehörige Prüfprotokoll.
- **KI-Programmierassistent (Claude):** Umsetzung von Anwendung und Tests nach diesen Vorgaben sowie die
  als „Entwurf des KI-Assistenten“ gekennzeichneten Beschreibungs- und Suchbegriffsvorschläge.
- **Quellen:** Digitalisate und Metadaten der Staatsbibliothek zu Berlin (Public Domain Mark 1.0);
  Colibri-Datensatz von Sebastian Schmideler, Sigrun Putjenter und Jörg Lehmann (CC BY 4.0,
  DOI 10.5281/zenodo.15535927).
