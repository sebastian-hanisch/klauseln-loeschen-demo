"""Messskript: erzeugt die eingefrorene Messung `klo_messung.json` (Stand des Baus).

Aufruf (Wurzelordner des Repos):
    python tools/messung_klo.py teil zufall    --out DIR     # 20 Formeln Zufalls-3-SAT, n = 175
    python tools/messung_klo.py teil faerbung  --out DIR     # 20 Formeln 3-Färbung, n = 300 Knoten
    python tools/messung_klo.py teil vor200    --out DIR     # Wiederholung der Vormessung: 8 Formeln, n = 200, ohne / alle 500 / alle 2 000
    python tools/messung_klo.py zusammenfuegen --out DIR     # liest die drei Teile aus DIR und schreibt klo_messung.json
Die Teile sind unabhängig und dürfen nacheinander oder in getrennten Prozessen laufen.

Je Formel (Zufalls-Seed 4000 + Nummer, SplitMix64-Erzeuger `klo_instanzen`):
  Abstände 250, 500, 1 000, 2 000 und nie (Regel „lbd“, Anteil ½, LBD-Grenze 2),
  fünf Läufe ohne Löschen mit zufälliger Anfangsaktivität (Löser-Seeds 1 bis 5): die Streuung der Suche,
  zwei weitere Regeln („laenge“, „zufall“) bei Abstand 500.
Gespeichert werden nur Zähler (Konflikte, Lesezugriffe, Klauseln), keine Sekunden. Die Antwort jedes Laufs wird im Test gegen OR-Tools geprüft
(tests/test_oracle_klauseln_loeschen.py, kleine Fassung) und im Scratch-Lauf der Bauphase an allen Formeln (Befund in der README).
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import klo_messung as M  # noqa: E402

ABSTAENDE = (250, 500, 1000, 2000, None)
LOESER_SEEDS = (1, 2, 3, 4, 5)
REGELN = ("lbd", "laenge", "zufall")
REGEL_ABSTAND = 500
FORMELN = tuple(range(20))
TEILE = {
    "zufall": dict(familie="zufall", n=175, formeln=FORMELN, abstaende=ABSTAENDE, budget=60000, loeser_seeds=LOESER_SEEDS, regeln=REGELN, regel_abstand=REGEL_ABSTAND),
    "faerbung": dict(familie="faerbung", n=300, formeln=FORMELN, abstaende=ABSTAENDE, budget=30000, loeser_seeds=LOESER_SEEDS, regeln=REGELN, regel_abstand=REGEL_ABSTAND),
    "vor200": dict(familie="zufall", n=200, formeln=tuple(range(8)), abstaende=(None, 500, 2000), budget=200000, loeser_seeds=(), regeln=("lbd",), regel_abstand=None),
}


def teil(name, out):
    p = dict(TEILE[name])
    t0 = time.time()
    zeilen = M.messreihe(p["familie"], p["n"], p["formeln"], p["abstaende"], p["budget"], p["loeser_seeds"], p["regeln"], p["regel_abstand"],
                         fortschritt=lambda f: print(f"{name}: Formel {f} fertig, {time.time() - t0:.0f} s", flush=True))
    daten = {"parameter": {k: list(v) if isinstance(v, tuple) else v for k, v in p.items()}, "zeilen": zeilen}
    Path(out).mkdir(parents=True, exist_ok=True)
    (Path(out) / f"teil_{name}.json").write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
    print(f"{name}: {len(zeilen)} Läufe geschrieben, {time.time() - t0:.0f} s Rechenzeit (nur Protokoll, kein Befund)")


def zusammenfuegen(out):
    ergebnis = {"meta": {"skript": "tools/messung_klo.py", "seed_basis": M.SEED_BASIS, "erzeuger": "klo_instanzen (SplitMix64)",
                         "regel": "Anteil 1/2, LBD-Grenze 2, Regel lbd, wenn nicht anders genannt",
                         "streuung": "fünf Läufe ohne Löschen mit zufälliger Anfangsaktivität (Löser-Seeds 1 bis 5)",
                         "einheit": "Zähler (Konflikte, Lesezugriffe, Klauseln), keine Sekunden"}}
    for name in TEILE:
        ergebnis[name] = json.loads((Path(out) / f"teil_{name}.json").read_text(encoding="utf-8"))
    M.schreibe_messung(ergebnis)
    print("klo_messung.json geschrieben")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("befehl", choices=("teil", "zusammenfuegen"))
    ap.add_argument("name", nargs="?", choices=tuple(TEILE))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.befehl == "teil":
        if not a.name:
            ap.error("teil braucht einen Namen")
        teil(a.name, a.out)
    else:
        zusammenfuegen(a.out)
