"""Messreihen: Aufgaben erzeugen, je Formel und Variante einen Lauf messen, Ergebnisse lesen und schreiben.

Eine Zeile einer Messreihe ist ein Dictionary mit den Schlüsseln `formel` (Nummer ab 0), `abstand` (Löschen alle so viele Konflikte, `None` = nie),
`regel` („lbd“, „laenge“, „zufall“; bei `abstand=None` ohne Bedeutung), `loeser_seed` (`None` = feste Reihenfolge der Gleichstände, ganze Zahl =
zufällige Anfangsaktivität), `antwort` („sat“, „unsat“, „abbruch“), `konflikte`, `lesezugriffe`, `lebend` (gelernte Klauseln der Länge ≥ 2 am Ende
des Laufs), `gelernt`, `geloescht`. Gemessen wird nur in Zählern: Konflikte, Lesezugriffe, Klauseln, nie in Sekunden.

Die eingefrorene Messung `klo_messung.json` erzeugt `tools/messung_klo.py` mit diesen Funktionen; die App und die Tests lesen sie und rechnen
kleine Teilmengen live nach.
"""
import json
from pathlib import Path

import klo_instanzen as I
import klo_loeschen as L

MESSDATEI = Path(__file__).resolve().parent / "klo_messung.json"
SEED_BASIS = 4000                      # Formel i hat den Zufalls-Seed SEED_BASIS + i (SplitMix64 des Erzeugers)
FAMILIEN = ("zufall", "faerbung")
FAMILIEN_NAMEN = {"zufall": "Zufalls-3-SAT (m/n = 4,26)", "faerbung": "3-Färbung (mittlerer Grad 4,5)"}
M_PRO_N = 4.26
FAERBUNG_GRAD = 4.5


def aufgabe(familie: str, n: int, seed: int):
    """Eine Aufgabe der Familie. Zufall: n Variablen, m = round(4,26 · n) Klauseln. Färbung: n Knoten, mittlerer Grad 4,5, drei Farben (3n Variablen)."""
    if familie == "zufall":
        return I.rand3(n, round(M_PRO_N * n), seed)
    if familie == "faerbung":
        return I.flat_graph(n, FAERBUNG_GRAD, seed, 3)
    raise ValueError(f"Familie muss eine von {FAMILIEN} sein")


def antwort_text(antwort) -> str:
    return {True: "sat", False: "unsat", None: "abbruch"}[antwort]


def messe(inst, abstand, regel, loeser_seed, budget, formel, anteil=L.STANDARD_ANTEIL, grenze=L.STANDARD_GRENZE) -> dict:
    """Ein Lauf als Zeile der Messreihe."""
    r = L.lauf(inst.n, inst.klauseln, abstand=abstand, anteil=anteil, lbd_grenze=grenze, regel=regel, budget=budget, loeser_seed=loeser_seed)
    s = r.stat
    return {"formel": formel, "abstand": abstand, "regel": regel if abstand is not None else "lbd", "loeser_seed": loeser_seed,
            "antwort": antwort_text(r.ergebnis.antwort), "konflikte": s["konflikte"], "lesezugriffe": s["lesezugriffe"],
            "lebend": s["lebend_gelernt"], "gelernt": s["gelernt"], "geloescht": s["geloescht"]}


def messreihe(familie, n, formeln, abstaende, budget, loeser_seeds=(), regeln=("lbd",), regel_abstand=None, fortschritt=None,
              haupt_regel="lbd", anteil=L.STANDARD_ANTEIL, grenze=L.STANDARD_GRENZE) -> list:
    """Je Formel: jeder Abstand mit der Regel `haupt_regel` (None = nie); je Löser-Seed ein Lauf ohne Löschen mit zufälliger Anfangsaktivität;
    je weitere Regel (außer `haupt_regel`) ein Lauf mit Löschen alle `regel_abstand` Konflikte. `formeln`: Nummern der Formeln (Seed = SEED_BASIS + Nummer)."""
    zeilen = []
    for f in formeln:
        inst = aufgabe(familie, n, SEED_BASIS + f)
        for abstand in abstaende:
            zeilen.append(messe(inst, abstand, haupt_regel, None, budget, f, anteil, grenze))
        for s in loeser_seeds:
            zeilen.append(messe(inst, None, haupt_regel, s, budget, f, anteil, grenze))
        for regel in regeln:
            if regel != haupt_regel:
                zeilen.append(messe(inst, regel_abstand, regel, None, budget, f, anteil, grenze))
        if fortschritt:
            fortschritt(f)
    return zeilen


def lade_messung(pfad=MESSDATEI) -> dict:
    return json.loads(Path(pfad).read_text(encoding="utf-8"))


def schreibe_messung(daten: dict, pfad=MESSDATEI) -> None:
    Path(pfad).write_text(json.dumps(daten, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
