# 0006 Zweitprüfung durch eine zweite Person

Status: gültig

Kontext: Die Endbestätigung (0003) ist keine unabhängige Prüfung. Es fehlt eine zweite Sicht auf die einzelnen Prüfbereiche.

Entscheidung: Nach der Endbestätigung kann eine Person mit anderem Namen (ohne Beachtung der Groß- und Kleinschreibung) je Prüfbereich zustimmen oder mit Begründung abweichen. Das Feld `second_review` im Datensatz hält je Bereich den letzten Eintrag mit Person, Zeit, Ergebnis und Inhaltsprüfsumme; der Verlauf steht im `review_log` unter `second_review/<Bereich>`. Der Namensvergleich geschieht beim Speichern unter der Speichersperre. Ein Eintrag gilt nur, solange die Prüfsumme dem aktuellen Inhalt des Bereichs entspricht und die Endbestätigung nicht von derselben Person stammt; sonst gilt er als veraltet (wie 0002, ohne den Eintrag zu löschen). Ein unveränderter Eintrag schreibt nichts. Ältere Arbeitskopien erhalten das leere Feld über die Umstellung mit Sicherung in `.history`.

Folgen: Der Name ist nur eine Konvention ohne Anmeldung; die Oberfläche sagt das. Die Zweitprüfung hebt die Endbestätigung nicht auf und vergibt keine Ground Truth. JSON enthält das Feld, die CSV Person und Stand je Zeile.
