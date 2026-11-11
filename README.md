# Klauseln löschen – Gedächtnis kostet Zugriffe – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-klauseln-loeschen-demo.streamlit.app/)** -->

Stück 5 der Linie **„SAT und Constraint Programming“** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Vorgänger ist das Lernen von Konfliktklauseln (Stück 1, `konfliktlernen-demo`); die Kante ist ein **Fix**: Jeder Konflikt, der nicht auf Stufe 0 liegt, liefert eine gelernte Klausel (Einheitsklauseln werden als Belegung statt als Klausel gespeichert); ohne Löschen wächst der Bestand mit den Konflikten, und die Propagation besucht mehr Klauseln. Das Stück zeigt, was Löschen am Bestand und an den Lesezugriffen spart und was es kosten kann (Information: eine gelöschte Klausel kann ein zweites Mal gelernt werden, gezählt wird das nicht). Vehikel sind Zufalls-3-SAT und die 3-Färbung eines Zufallsgraphen (Aufträge auf drei Rampen); verwandt: `watched-literals-demo` (Lesezugriffe), `beweise-pruefen-demo` (Löschzeilen im Beweis), `neustarts-sat-demo`.

## Warum dieses Problem

Ein Löser, der aus jedem Konflikt lernt, ertrinkt irgendwann in den eigenen Klauseln. Nicht jede gelernte Klausel wird wieder gebraucht, aber jede kann bei einer Propagation besucht werden, sobald eines ihrer beiden beobachteten Literale falsch wird; je größer der Bestand, desto mehr Besuche und gelesene Literale. Die Kernfrage der Demo: **Was spart das Löschen der schlechteren Hälfte, und was kostet es?** Gemessen wird nur in Zählern (Konflikte, Klauseln, Lesezugriffe), nie in Sekunden; und über die Konfliktzahl urteilt die Demo nur gegen die **Streubreite der Suche**, denn die Konfliktzahl einer Formel schwankt auch ohne Löschen um Faktoren.

## Modell

Ein CDCL-Löser (`klo_cdcl.py`, Kopie aus dem Kern-Paket der Linie) lernt aus jedem Konflikt eine Klausel (1-UIP) und bestimmt ihre **LBD** (Literal Block Distance: Zahl der verschiedenen Entscheidungsstufen ihrer Variablen). Alle `d` Konflikte hält er eine **Löschrunde** ab (`klo_loeschen.py`):

- **Kandidaten:** gelernte, noch lebende Klauseln mit LBD über der LBD-Grenze (Standard 2) und **nicht gesperrt** (gesperrt = gerade Grund eines Literals auf dem Trail). Ursprüngliche Klauseln der Aufgabe sind nie Kandidaten.
- **Rangordnung:** absteigend nach (LBD, Länge, −Nummer); bei Gleichstand fällt die **ältere** Klausel (kleinere Nummer) zuerst. Alternativen: (Länge, LBD, −Nummer) und eine zufällige Reihenfolge (SplitMix64).
- **Löschrunde:** die ersten ⌊Anteil · Zahl der Kandidaten⌋ fallen (**abgerundet**; Standard Anteil ½, wählbar ¼ und ¾).
- **Lesezugriff:** ein gelesenes Literal einer besuchten Klausel bei der Propagation (Zählgröße dieses Python-Lösers; keine Laufzeit, keine Byte).
- **Lebende gelernte Klauseln:** gelernte Klauseln der Länge ≥ 2, die nicht gelöscht sind (gelernte Einheitsklauseln werden nicht als Klausel gespeichert).

Die Formeln stehen im 📐-Expander der App. Der Kern der Löschrunde sind reine Funktionen (`lbd`, `kandidaten`, `rangfolge`, `loeschrunde`, `waehle_loeschkandidaten`, `bestandsverlauf` in `klo_loeschen.py`); der Löser `LoeschLoeser` ist eine Unterklasse des Kern-Lösers und überschreibt nur die Löschrunde.

**Handtabelle (Handbeispiel, Experiment 1).** Zwölf Variablen auf sechs Entscheidungsstufen, acht gelernte Klauseln (LBD 2, 3, 4, 2, 4, 4, 4, 5; Längen 2, 3, 4, 3, 5, 5, 4, 6), gesperrt sind die Klauseln 3 und 7. Kandidaten sind 2, 5, 6 und 8; Rangfolge 8, 5, 6, 2 (5 und 6 haben beide (LBD 4, Länge 5), die ältere fällt zuerst); die Hälfte von vier Kandidaten, also zwei, fällt: die Klauseln 8 und 5. Es bleiben 1, 2, 3, 4, 6 und 7 (vorher acht gelernte Klauseln, nachher sechs).

## Methodik

- **Vier Experimente** (Reiter): (1) die Löschrunde an der Handtabelle von Hand, mit wählbaren gesperrten Klauseln, Anteil, LBD-Grenze und Rangordnung; (2) eine Live-Aufgabe zweimal gelöst, ohne und mit Löschen, mit der Sägezahnlinie des Bestands und den kumulierten Lesezugriffen; (3) die Messreihe über Löschabstände 250, 500, 1 000, 2 000 und nie; (4) der Vergleich dreier Rangordnungen bei gleichem Anteil und gleichem Abstand.
- **Eingefrorene Messung** `klo_messung.json` (vorgerechnet, nicht live; erzeugt von `tools/messung_klo.py`): je Familie 20 Formeln (Zufalls-Seeds 4000 bis 4019 des SplitMix64-Erzeugers), ein Lauf je Formel und Variante. Familien: Zufalls-3-SAT mit 175 Variablen und 746 Klauseln (m/n = 4,26, Konfliktbudget 60 000) und 3-Färbung eines Zufallsgraphen mit 300 Knoten und mittlerem Grad 4,5 (Konfliktbudget 30 000). Je Formel: fünf Löschabstände (Anteil ½, LBD-Grenze 2, Regel LBD), fünf weitere Läufe ohne Löschen mit zufälliger Anfangsaktivität (Löser-Seeds 1 bis 5) und zwei weitere Rangordnungen bei Abstand 500. Dazu die Wiederholung der Vormessung der Planung: Zufalls-3-SAT mit 200 Variablen, 8 Formeln, ohne Löschen sowie alle 500 und alle 2 000 Konflikte (Budget 200 000).
- **Streubreite der Suche:** Der Median der Konflikte über die 20 Formeln wird für sechs Läufe ohne Löschen bestimmt (fester Start und fünf Löser-Seeds); das Band reicht vom kleinsten bis zum größten dieser sechs Mediane. Ein Konfliktvergleich mit Löschen gilt nur, wenn er aus dem Band herausführt; sonst steht „in den Konflikten ist kein Unterschied erkennbar“.
- **Messreihe auf Knopfdruck** (Experiment 3): dieselbe Rechnung kleiner und live (n bis 120, bis 10 Formeln), mit den Einstellungen der Seitenleiste.
- **Gegenproben:** Antworten und Modelle gegen OR-Tools CP-SAT (nur in `requirements-dev.txt`, nie in der App); der Beweis eines Laufs mit Löschzeilen gegen einen unabhängigen einfachen RUP-Prüfer.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen: Messung `klo_messung.json`, ein Lauf je Formel und Variante, 20 Formeln je Familie. „Basis ohne Löschen“ heißt: die Prozentzahl ist die Änderung gegenüber dem Lauf ohne Löschen, bezogen auf diesen.

| Frage | Befund | Test |
|---|---|---|
| Wie viel spart das Löschen am Bestand? (Zufalls-3-SAT, n = 175, Median der lebenden gelernten Klauseln über 20 Formeln) | Ohne Löschen 5 586; Löschen alle 250 / 500 / 1 000 / 2 000 Konflikte: 449 / 822 / 1 374 / 2 464 (92 / 85 / 75 / 56 % weniger, Basis ohne Löschen). | `test_claim_zufall_bestand_und_lesezugriffe` |
| … und an den Lesezugriffen? (Summe über die 20 Formeln) | Ohne Löschen 157 495 526; alle 250: 77 707 239 (51 % weniger), alle 500: 72 336 432 (54 %), alle 1 000: 72 209 617 (54 %), alle 2 000: 97 474 904 (38 %). In 16 von 19 Formeln mit Löschrunde (Abstand 500) weniger Lesezugriffe. | `test_claim_zufall_bestand_und_lesezugriffe`, `test_claim_zufall_paarvergleich` |
| Ändert das Löschen die Konfliktzahl? (Median über 20 Formeln, Streuband 4 848,5 bis 6 576,5) | Ohne Löschen 5 588. Alle 500: 6 383, alle 1 000: 5 213, alle 2 000: 6 079,5: nicht aus dem Band der sechs Läufe ohne Löschen herausgeführt (bei Abstand 500 liegt der Median 14 % über dem Wert ohne Löschen, die Summe der Konflikte 29 % darüber: 161 035 gegen 124 643); ein Nutzen für die Konfliktzahl ist nicht erkennbar, ein Schaden ebenso wenig sicher ausgeschlossen. Alle 250: 12 253,5, **über** dem Band (119 % mehr, Basis ohne Löschen); Summe der Konflikte 215 785 gegen 124 643 ohne Löschen. | `test_claim_zufall_konflikte_gegen_die_streubreite` |
| Wie stark schwankt die Suche ohne Löschen? | Je Formel liegt die größte Konfliktzahl der sechs Läufe ohne Löschen im Median das 1,94-Fache über der kleinsten. | `test_claim_zufall_konflikte_gegen_die_streubreite` |
| Einzelvergleich je Formel (Abstand 500, 19 Formeln mit Löschrunde) | 5 Formeln brauchten weniger, 14 mehr Konflikte als ohne Löschen. | `test_claim_zufall_paarvergleich` |
| Welche Rangordnung löscht gut? (Abstand 500, Median der Konflikte) | LBD 6 383 (im Band), Länge 6 955,5 (379 über der Obergrenze des Bandes, nur 5,8 % darüber), zufällig 10 419 (86 % über dem Median ohne Löschen, außerhalb). LBD und Länge sind in den Konflikten nicht trennbar (Länge 9 % über LBD, das Band ist 31 % des Medians ohne Löschen breit, und Länge braucht weniger Lesezugriffe); die zufällige Rangordnung ist deutlich schlechter. Lesezugriffe (Summe): 72 336 432 / 67 533 510 / 129 845 877; lebende gelernte Klauseln (Median): 822 / 741,5 / 729. | `test_claim_zufall_regeln` |
| 3-Färbung, 300 Knoten (Lesezugriffe, Summe über 20 Formeln) | Ohne Löschen 164 589 374; alle 250: 57 542 590 (65 % weniger), alle 500: 69 626 411 (58 %), alle 1 000: 73 942 416 (55 %), alle 2 000: 109 030 893 (34 %). Das ist überwiegend ein Abbruch vor dem Ergebnis: 75 % der Summe ohne Löschen stammen von einer Formel (Formel 7: 20 222 Konflikte, 122 674 465 Lesezugriffe), die mit Löschen bei jedem Abstand am Budget von 30 000 Konflikten abbricht (ungelöst, 25 018 805 / 32 146 838 / 46 253 774 / 69 764 445 Lesezugriffe). Ohne diese Formel ändert sich die Summe um −22 / −11 / −34 / −6 % (bei Abstand 250 ist darin ein weiterer Abbruch enthalten); bei Abstand 500 haben nur 4 von 7 Formeln mit Löschrunde weniger Lesezugriffe. | `test_claim_faerbung` |
| 3-Färbung: Konflikte und Abbrüche | Der Median der Konflikte bleibt bei 262 (Abstand 500, 1 000, 2 000), weil nur 7, 5 und 4 Formeln überhaupt so viele Konflikte brauchen, dass eine Löschrunde stattfindet; beim Abstand 250 sind es 10. Am Konfliktbudget 30 000 brachen mit Löschen 2 Läufe (Abstand 250) beziehungsweise 1 Lauf (Abstand 500, 1 000, 2 000) ab, ohne Löschen keiner. | `test_claim_faerbung` |
| Wiederholung der Vormessung (Zufalls-3-SAT n = 200, 8 Formeln, SplitMix64) | Median der Konflikte ohne Löschen 7 252,5, alle 500: 8 975, alle 2 000: 7 519,5; Maximum 34 457 / 103 730 / 45 779 (bei Abstand 500 das 3,0-Fache). Lesezugriffe (Summe) 332 517 480 → 80 263 971 (76 % weniger) und 102 999 066 (69 % weniger); lebende gelernte Klauseln (Median) 7 252,5 → 769,5 (89 % weniger) und 2 923,5 (60 % weniger). | `test_claim_wiederholung_der_vormessung_n200` |
| Handtabelle | Kandidaten 2, 5, 6, 8; Rangfolge 8, 5, 6, 2; es fallen 8 und 5, es bleiben 1, 2, 3, 4, 6, 7. | `test_claim_handtabelle`, `tests/test_algorithm.py` |

Jede Zahl dieser Tabelle steht als Test in `tests/test_claims.py`; eine Teilmenge der Läufe rechnet `tests/test_messung.py` live nach. **Nicht im Test, sondern Messung dieser README (Scratch-Lauf der Bauphase; Zufalls-Seeds und Skript liegen nicht im Repo, die Zahlen sind daher nicht nachrechenbar):** Die Antworten aller 210 Zufallsformeln (n = 40 bis 70; 124 erfüllbar, 86 unerfüllbar) stimmen in 1 470 Läufen (ohne Löschen sowie bei Abstand 15 und 40, je alle drei Rangordnungen) mit OR-Tools CP-SAT überein, und die Modelle bestehen die Prüfung; ebenso alle 496 Läufe der eingefrorenen Messung, die eine Antwort liefern (Läufe mit Abbruch am Budget ausgenommen). Im Repo läuft davon eine kleine Fassung (`tests/test_oracle_klauseln_loeschen.py`). Eine unabhängige Stichprobe gegen CP-SAT bestätigte die Antwort ohne Löschen für alle 48 Formeln der eingefrorenen Messung (20 Zufall, 20 Färbung, 8 mit n = 200); in der Messdatei ist die Antwort mit Löschen je Formel gleich der ohne Löschen, außer bei den 8 Abbrüchen.

## Befunde und Korrekturen gegenüber dem Plan

- **Die Zahlen der Vormessung sind nicht reproduziert, ihr Muster schon.** Der Plan nannte für Zufalls-3-SAT n = 200 (Formeln aus Python-`random`) Median 13 234 Konflikte, 94 % weniger lebende Klauseln und rund 61 % weniger Lesezugriffe. Mit den SplitMix64-Formeln des Repos (8 Formeln, n = 200) sind es 7 252,5 Konflikte, 89 % und 76 % (alle 500 Konflikte). Die Planzahlen gelten als überholt; die Richtung (Bestand und Lesezugriffe sinken stark, die Konfliktzahl nicht verlässlich) bleibt.
- **Die Vermutung „Streuung der Suche“ ist gemessen.** Ohne Löschen schwankt die Konfliktzahl je Formel im Median um den Faktor 1,94 (Zufalls-3-SAT n = 175) beziehungsweise 10,1 (3-Färbung, 300 Knoten). Bei Abstand 500, 1 000 und 2 000 liegt der Median der Konflikte innerhalb der Streubreite; das Band ist grob (Spanne von nur sechs Medianen, kein Test), und „innerhalb“ heißt nicht „gleich“. Ein Nutzen des Löschens für die Konfliktzahl ist damit **nicht** belegt. Bei Abstand 250 steigt der Median über das Band (Zufalls-3-SAT n = 175; Konflikte je Formel: 13 von 20 Formeln mehr, 6 weniger). Als Erklärung kommt in Frage, dass gelöschte Klauseln erneut gelernt werden; das wird nicht gezählt, und auch der Suchverlauf ändert sich durch das Löschen.
- **Färbung mit 300 statt 120 Knoten.** Bei 120 Knoten brauchte der Löser in einer Stichprobe der Bauphase (Zufalls-Seeds 4000 bis 4002, Scratch-Lauf, nicht im Test) 386, 463 und 55 Konflikte; eine Löschrunde alle 250 Konflikte findet dann kaum statt. Die eingefrorene Messung nutzt 300 Knoten (900 Variablen), das Preset „Färbung“ 200 Knoten (Zufalls-Seed 4003, 1 558 Konflikte ohne Löschen). Der Median der Konflikte der Färbungsmessung ist von den vielen leichten Formeln bestimmt; deshalb zeigt die App dort zusätzlich die Summe der Lesezugriffe und den Einzelvergleich je Formel.
- **Kern-Wünsche 1 bis 4 nicht im Kern:** Der Kern-Löser löscht fest mit Anteil ½, Grenze 2 und Regel LBD. Stück 5 baut die Parametrisierung als Unterklasse `LoeschLoeser` in `klo_loeschen.py` (Alternative Z5 des Plans); `klo_cdcl.py` bleibt wörtlich die Kern-Kopie. Mit den Standardwerten löscht die Unterklasse gleich wie der Kern (Test).
- **Funktionsnamen** der Einheiten ohne Präfix (`lbd`, `kandidaten`, `rangfolge`, `loeschrunde`, `bestandsverlauf`, `messreihe`) statt `klo_lbd` usw.; `messreihe` liegt in `klo_messung.py`.
- **Experiment 4 gebaut** (Plan Z3, Empfehlung): LBD liegt im Median der Konflikte im Band, Länge liegt mit 6 955,5 um 379 über dessen Obergrenze (knapp außerhalb, aber nur rund 9 % über LBD, also nicht von LBD trennbar), die zufällige Rangordnung ist deutlich schlechter (10 419). Bei der Färbung bleibt der Median für alle drei Regeln bei 262.
- **Preset „Ohne Löschen (Vergleich)“** ist der Löschabstand „nie“ (beide Linien fallen zusammen). Anteil, LBD-Grenze und Rangordnung stehen als Löschregel in der Seitenleiste und gelten für Handtabelle, Live-Aufgabe und die Messreihe auf Knopfdruck; die eingefrorene Messung gilt nur für Anteil ½, Grenze 2, Regel LBD.

## Ehrliche Grenzen

- Zwei Familien sind gemessen (Zufalls-3-SAT n = 175 und 3-Färbung mit 300 Knoten), je 20 Formeln und ein Lauf je Formel und Variante; die Aussagen gelten für diese Läufe, nicht für Industrieformeln und nicht für andere Größen.
- Die Konfliktzahl schwankt je Formel um Faktoren. Der Konfliktvergleich benutzt ein Band aus Medianen von sechs Läufen; das ist ein grobes Maß (fünf Löser-Seeds, ein Median je Seed), kein Test mit Irrtumswahrscheinlichkeit.
- Die Lesezugriffe sind eine Zählgröße des eigenen Python-Lösers, keine Laufzeit und keine Speichergröße in Byte. Die Aussage „Propagation ist der Zeitfresser (etwa 80 %)“ steht im Chaff-Papier für dessen Löser, nicht für diesen.
- Der Löschzeitpunkt (alle 250 bis 2 000 Konflikte) weicht von Glucose ab (alle 20 000 + 500 · x Konflikte, nach Audemard/Simon 2009; Klauseln mit LBD 2 bleiben nach der Glucose-Implementierung, im Paper steht „asserting clauses are kept“), weil die Aufgaben klein sind; die Wirkung auf große Formeln ist unbekannt. Ein bester Löschabstand wird nicht behauptet.
- Die Median-Vergleiche der Färbung sind durch viele leichte Formeln geprägt (in 10 von 20 Formeln kommt es nicht einmal zu 250 Konflikten).
- Die Zufallsregel nutzt einen eigenen SplitMix64-Strom (Zufalls-Seed des Lösers plus Versatz); die Streumessung ändert dagegen die Anfangsaktivität der Variablen. Beides sind Zufall, aber nicht dasselbe.
- Die Spur eines Laufs ist im Kern auf 5 000 Ereignisse begrenzt; der Verlauf der App wird deshalb abgetastet (alle Konflikte des Budgets durch 400), nicht aus der Spur gelesen.
- Echter Mausklick im Browser: die Demo wurde per AppTest und mit einem kurzen Start der App auf Skriptfehler geprüft, nicht klickweise im Browser.

## Verifikation

- **Einheiten gegen die Handtabelle:** LBD, Kandidaten, Rangfolge (Gleichstand: ältere zuerst, unabhängig von der Eingabereihenfolge), Löschrunde für Anteil ¼, ½, ¾ und LBD-Grenze 1, 2, 3, Sägezahn von Hand (`tests/test_algorithm.py`).
- **Orakel (`tests/test_oracle_klauseln_loeschen.py`):** (1) LBD gegen die Definition „Zahl verschiedener Stufen“ an 200 Zufallsklauseln; (2) die Löschrunde gegen eine Referenz ohne `sorted` (Paarvergleich) an 200 Zufallstabellen; (3) Antwort und Modell mit und ohne Löschen gegen OR-Tools CP-SAT; (4) Beweis mit Löschzeilen gegen einen unabhängigen einfachen RUP-Prüfer, dazu Solidität an erfüllbaren Formeln; (5) der Bestandszähler gegen Nachzählen am Löser.
- **Eigenschaften an echten Läufen (`tests/test_properties.py`):** gesperrte, ursprüngliche und Klauseln mit LBD ≤ Grenze fallen nie; nur lebende gelernte fallen, jede einmal; es fällt höchstens der Anteil der Kandidaten; gefallene sind nach dem Schlüssel mindestens so schlecht wie jeder bleibende Kandidat (Gleichstand: kleinere Nummer); die Antwort hängt nicht vom Löschabstand ab; ohne Löschen sind lebende gleich gelernte minus Einheitsklauseln.
- **Messung (`tests/test_messung.py`):** Aufbau, Zweig-Test (jede Variante weicht auf mindestens einer Formel von der Nachbarvariante ab), gleiche Antwort je Formel in allen Läufen ohne Abbruch, Teilmenge live nachgerechnet.
- **Verdikte** als reine Funktionen an handgesetzten Zeilen, inklusive „innerhalb der Streubreite“, „über“, „unter“, ohne Referenzläufe und mit Abbrüchen (`tests/test_verdicts.py`); Randfälle: keine Kandidaten, genau ein und genau zwei Kandidaten, Abstand größer als das Budget, Aufgabe ohne Konflikt (`tests/test_edge_cases.py`).
- **Kopien des Kerns:** `klo_rng.py`, `klo_instanzen.py`, `klo_cdcl.py` sind bis auf zwei Kopfzeilen und die Importe wörtlich gleich dem Kern (Kern-Version im Modulkopf); Regressionswerte: SplitMix64, Schubfach h = 4, 5, 6 mit 28 / 159 / 1 004 Konflikten (`tests/test_kern_kopien.py`). Eine Löschrunde mit den Standardwerten gleicht dem Kern-Löser.
- **Claims:** jede Zahl der Tabelle „Befunde“ in `tests/test_claims.py`.
- **Presets, Layout, Oberfläche:** vollständig und innerhalb der Reglergrenzen; Schnellstart oben in der Seitenleiste, fester Kopf, aktives Preset hervorgehoben, jede Änderung eines Reglers hebt die Markierung auf; AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Footer, Laufzeit-Importe.
- **Testzahl:** 142 Tests (`pytest --collect-only -q tests`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Kernfrage, Live-Aufgabe, vier Reiter, Grenzen, 📐-Expander |
| `klo_cdcl.py`, `klo_instanzen.py`, `klo_rng.py` | wörtliche Kopien aus dem Kern-Paket der Linie (CDCL, Aufgabenerzeuger, SplitMix64) |
| `klo_loeschen.py` | Löschrunde als reine Funktionen und der Löser `LoeschLoeser` (Anteil, LBD-Grenze, Regel, Bestandszähler, Verlauf) |
| `klo_algorithm.py` | Live-Vergleich einer Aufgabe ohne und mit Löschen |
| `klo_messung.py`, `klo_messung.json` | Messreihen und die eingefrorene Messung (Erzeugung: `tools/messung_klo.py`) |
| `klo_scenario.py` | Handtabelle, Aufgaben |
| `klo_evaluation.py` | Kennzahlen, Streubreite, Verdikte (reine Funktionen) |
| `klo_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `klo_layout.py` | Fester Kopf (Stylesheet) |
| `klo_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `klo_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest und OR-Tools (nur Gegenprobe in Tests und Messskript) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt: Streamlit, Pandas, Plotly) |
| `tools/messung_klo.py` | Messskript der eingefrorenen Messung |
| `tests/` | Einheiten, Orakel, Eigenschaften, Messung, Claims, Verdikte, Randfälle, Presets, Layout, AppTest, Footer, Kern-Kopien |

## Bewusst nicht umgesetzt

Aktivitätsbasiertes Löschen (MiniSat) und der Zeitplan von Glucose mit wachsendem Abstand; Speichergrößen in Byte und Zeitmessungen; Löschen ursprünglicher Klauseln; Industrieformeln; Vorverarbeitung (eigenes Stück der Linie); Prüfen der Löschzeilen im Beweisprotokoll (eigenes Stück: `beweise-pruefen-demo`; hier nur gezählt und im Test gegen einen einfachen Prüfer geprüft).

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und Pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html).
