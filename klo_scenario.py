"""Szenario: die Handtabelle (Handbeispiel einer Löschrunde) und die Aufgaben der Läufe (Zufalls-3-SAT, 3-Färbung).

Die Handtabelle ist von Hand gesetzt (Plan, `handbeispiele/hb_05.py` der Planung): ein Trail mit Entscheidungsstufen für zwölf Variablen,
acht gelernte Klauseln (nur die Variablen zählen, Vorzeichen sind für LBD und Länge gleichgültig) und die Klauseln, die gerade Grund eines
Trail-Literals sind (gesperrt)."""
from dataclasses import dataclass

import klo_loeschen as L
import klo_messung as M
from klo_rng import SplitMix64

# Stufe der Variablen auf dem Trail (Variable -> Entscheidungsstufe)
HAND_STUFEN = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 3, 8: 4, 9: 4, 10: 5, 11: 5, 12: 6}
# gelernte Klauseln (Nummer -> Variablen)
HAND_KLAUSELN = {
    1: (1, 3),
    2: (2, 5, 8),
    3: (4, 6, 9, 12),
    4: (1, 2, 4),
    5: (4, 5, 7, 8, 10),
    6: (3, 8, 9, 11, 12),
    7: (2, 4, 10, 12),
    8: (1, 5, 9, 10, 11, 12),
}
HAND_GESPERRT = (3, 7)           # Grund eines Trail-Literals: dürfen nicht fallen


@dataclass(frozen=True)
class HandErgebnis:
    """Eine Löschrunde an der Handtabelle, Schritt für Schritt."""
    lbd: dict            # Nummer -> LBD
    laenge: dict         # Nummer -> Länge
    kandidaten: list     # Nummern, aufsteigend
    rangfolge: list      # Schlechteste zuerst
    faellt: list         # die fallenden Nummern
    bleibt: list         # alle übrigen Nummern, aufsteigend


def hand_runde(gesperrt=HAND_GESPERRT, anteil=L.STANDARD_ANTEIL, grenze=L.STANDARD_GRENZE, regel=L.STANDARD_REGEL, seed=0,
               klauseln=HAND_KLAUSELN, stufen=HAND_STUFEN) -> HandErgebnis:
    """Die Löschrunde der Handtabelle mit den Einheiten aus `klo_loeschen` (Zufallsregel: SplitMix64 mit dem Zufalls-Seed)."""
    lbd_von = {nr: L.lbd(stufen[v] for v in vs) for nr, vs in klauseln.items()}
    laengen = {nr: len(vs) for nr, vs in klauseln.items()}
    rng = SplitMix64(seed) if regel == "zufall" else None
    kand = L.kandidaten(klauseln, lbd_von, gesperrt, grenze)
    reihe = L.rangfolge(kand, lbd_von, laengen, regel, rng)
    weg = L.loeschrunde(reihe, anteil)
    return HandErgebnis(lbd_von, laengen, kand, reihe, weg, sorted(set(klauseln) - set(weg)))


def aufgabe(familie: str, n: int, seed: int):
    """Aufgabe einer Familie (Erzeuger mit SplitMix64, gleiche Eingabe, gleiche Aufgabe)."""
    return M.aufgabe(familie, n, seed)
