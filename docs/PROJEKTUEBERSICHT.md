# Kinderbuch-Bildlabor – Projektübersicht

## Motivation

Ich habe mich auf eine Stelle im Datenmanagement einer Kinder- und Jugendbuchabteilung beworben. Mit
diesem Projekt zeige ich an einer kleinen Stichprobe, wie ich mit Digitalisaten, Katalogdaten und
Bildannotation arbeite, und ich möchte jede Entscheidung darin selbst erläutern und vertreten können.
Es ist ein eigenständiger Prototyp auf Basis öffentlich zugänglicher Quellen. Interne Abläufe,
Probleme oder Bedürfnisse der Bibliothek kenne ich nicht; das Projekt setzt keine voraus.

## Fragestellung

**Wie lassen sich abweichende Bildklassifikationen in digitalisierten Kinderbüchern am Originalbild
prüfen, begründet entscheiden und mit ihrer Herkunft weitergeben?**

Der Colibri-Datensatz der Staatsbibliothek zu Berlin (53.533 Zeilen zu Abbildungen aus Kinder- und
Jugendbüchern) führt zu jeder Abbildung eine automatische Klasse und, wo vorhanden, eine manuelle
(Spalte „groundtruth“). Weichen beide ab, reicht keiner der beiden Werte allein. Jemand muss am
Original nachsehen, entscheiden, die Gründe festhalten und das Ergebnis so weitergeben, dass beide
Ausgangswerte und ihre Herkunft erhalten bleiben. Das Bildlabor zeigt diesen Ablauf an echten Daten.
Es ist ein lokaler Prototyp, kein Produktionssystem, und trifft keine Annahmen über interne Abläufe
der Bibliothek.

## Was die Anwendung umfasst

Die Anwendung arbeitet mit sechs vorbereiteten Beispielen aus zwei Büchern: fünf Illustrationen aus
„Genovefa“ (Augsburg 1810) und einem Bildblatt aus „Die Heimath in Amerika“ (Augsburg 1850). Scans,
IIIF-Bildinformationen, OAI-PMH-Antworten mit METS/MODS und die Colibri-Werte liegen gespeichert im
Projekt und werden lokal ausgewertet. Eigene Bilder oder Metadaten lassen sich nicht importieren; ein
solcher Import ist eine mögliche zukünftige Erweiterung.

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

**Ergebnis für Scan 22:** Am 08.11.2026 geprüft und exportiert von Shota Tsertsvadze: Klassifikation
„Manuelle Klasse trifft zu: Abbildung“ mit Begründung am Bild, Illustrator bleibt unbekannt,
Endbestätigung erteilt. Beide
Colibri-Werte bleiben als Quellenangaben erhalten. Export, Begründungen im Wortlaut und
Einschränkungen: [ergebnis/](ergebnis/README.md).

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
   Rückladeprüfung liest die gespeicherte JSON-Datei erneut ein und vergleicht sie mit dem
   Arbeitsstand; die CSV-Datei wird dabei nicht zurückgelesen.

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

## Drei Stände

| Stand | Wo | Inhalt |
|---|---|---|
| Geprüftes Beispiel | [ergebnis/](ergebnis/README.md) | Genovefa, Scan 22: von mir geprüft, entschieden und endbestätigt; unveränderter Export als JSON und CSV |
| Weitere Beispiele | in der Anwendung; [OFFENE_PUNKTE.md](OFFENE_PUNKTE.md) | Genovefa, Scans 14, 16, 17 und 85 ungeprüft; „Die Heimath in Amerika“: nur der Titelrahmen bestätigt (Pilotexport unter [ergebnis/](ergebnis/README.md)) |
| Frischer Arbeitsstand der App | eigener Datenordner nach dem Start | alle sechs Objekte im Quellstand, alle Prüfbereiche offen |

Die Anwendung zeigt das geprüfte Beispiel auf der Startseite aus den Dateien unter `docs/ergebnis/`.
Eigene Prüfungen in der Anwendung verändern diese Dateien nicht.

## Mein Beitrag

- Fragestellung, fachliche Anforderungen und Auswahl der Quellen.
- Erste Lesung der Bildunterschriften des Pilotobjekts und Prüfung der Region „Bildtitel“ am Scan.
- Prüfung von Genovefa, Scan 22 am Bild: Regionsgrenzen, Beschreibung und Suchbegriffe bestätigt,
  Klassifikation und Illustrator-Hinweis entschieden und begründet, Endbestätigung erteilt und
  exportiert. Die Entscheidungen stehen wörtlich unter [ergebnis/](ergebnis/README.md).
- Durchsicht der Anwendung im Browser und Vorgaben zu Bedienung und Übergabe.

## KI-Unterstützung

- Ein KI-Programmierassistent (Claude) hat Anwendung, Tests und Entwürfe der Dokumentation nach meinen
  Vorgaben umgesetzt.
- Die Beschreibungs- und Suchbegriffsvorschläge zu den Genovefa-Scans stammen vom KI-Assistenten. Sie
  sind in der Anwendung und im Export als „Entwurf des KI-Assistenten“ gekennzeichnet und gelten erst
  nach einer Bestätigung mit Name und Zeitpunkt als geprüft.
- Entscheidungen und Bestätigungen im geprüften Beispiel habe ich selbst in der Anwendung getroffen;
  der Assistent hat keine Prüfung in meinem Namen ausgeführt.

## Grenzen

- Geprüft ist ein Beispiel. Eine Zweitprüfung durch eine andere Person gab es nicht; die
  Endbestätigung ist keine Ground-Truth-Freigabe.
- Sechs vorbereitete Beispiele, kein Import eigener Daten (siehe oben).
- Keine Live-Abfrage von OAI-PMH oder IIIF, keine neue OCR, keine XSD-Validierung, keine
  GND-Anbindung.
- Einzelplatzbetrieb: ein Server, gern mehrere Browserfenster; mehrere Server auf einem Datenordner
  sind nicht abgesichert.
- Getestet unter macOS und auf einem Windows-Server-2025-Runner mit Edge, nicht unter Windows 11
  (Einzelheiten: [ABNAHME_2026-11-07.md](ABNAHME_2026-11-07.md)).

## Quellen

Digitalisate und Metadaten der Staatsbibliothek zu Berlin (Public Domain Mark 1.0); Colibri-Datensatz
von Sebastian Schmideler, Sigrun Putjenter und Jörg Lehmann (CC BY 4.0, DOI 10.5281/zenodo.15535927).
