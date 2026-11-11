"""Live-Läufe der App: dieselbe Aufgabe ohne und mit Löschen (zwei Läufe des Lösers `klo_loeschen.LoeschLoeser`).

Der Kern der Demo steht in `klo_cdcl.py` (CDCL, Kopie aus dem Kern-Paket), `klo_loeschen.py` (Löschrunde und Löser mit einstellbarer Regel)
und `klo_messung.py` (Messreihen). Hier nur die Zusammenstellung eines Vergleichs für die Schritt-Ansicht über die Konflikte."""
from dataclasses import dataclass

import klo_loeschen as L
import klo_messung as M

ABTAST_PUNKTE = 400            # so viele Stützstellen hat der Verlauf höchstens (Abtasten alle budget // 400 Konflikte)


@dataclass(frozen=True)
class LiveVergleich:
    ohne: L.Lauf
    mit: L.Lauf
    abstand: int | None        # None: kein Löschen, beide Läufe sind gleich
    n: int
    klauseln: int              # Zahl der Klauseln der Aufgabe


def abtastabstand(budget: int) -> int:
    return max(1, budget // ABTAST_PUNKTE)


def live_vergleich(familie: str, n: int, seed: int, budget: int, abstand: int | None, anteil=L.STANDARD_ANTEIL, grenze=L.STANDARD_GRENZE,
                   regel=L.STANDARD_REGEL) -> LiveVergleich:
    """Aufgabe der Familie mit dem Zufalls-Seed erzeugen und zweimal lösen: ohne Löschen und mit Löschen alle `abstand` Konflikte.
    Ohne Abstand läuft nur ein Lauf (beide Felder zeigen ihn)."""
    inst = M.aufgabe(familie, n, seed)
    t = abtastabstand(budget)
    ohne = L.lauf(inst.n, inst.klauseln, abstand=None, budget=budget, abtast=t)
    mit = ohne if abstand is None else L.lauf(inst.n, inst.klauseln, abstand=abstand, anteil=anteil, lbd_grenze=grenze, regel=regel, budget=budget, abtast=t)
    return LiveVergleich(ohne, mit, abstand, inst.n, len(inst.klauseln))
