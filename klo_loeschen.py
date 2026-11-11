"""Löschen gelernter Klauseln: reine Funktionen der Löschrunde und ein Löser mit einstellbarer Löschregel.

Der Kern (`klo_cdcl.py`) löscht fest: gelernte Klauseln mit LBD > 2, die nicht gerade Grund eines Trail-Literals sind, die schlechtere
Hälfte nach (LBD, Länge). Diese Demo braucht Anteil, LBD-Grenze und Regel als Einstellungen, einen Bestandszähler und einen Verlauf
über die Konflikte. Der Kern ist ein Vertragsbaustein und wird nicht geändert (Entscheidung Z5 des Plans, Alternative): `LoeschLoeser`
ist eine Unterklasse von `Loeser` und überschreibt nur die Löschrunde (`_reduziere`) und fügt Zähler hinzu.

Einheiten (jede einzeln testbar, die Handtabelle des Plans ist ihre Mini-Instanz):
  `lbd`                       Zahl verschiedener Entscheidungsstufen einer Klausel
  `kandidaten`                gelernt, LBD über der Grenze, nicht gesperrt, nicht schon gelöscht
  `rangfolge`                 Schlechteste zuerst; Gleichstand: die ältere Klausel (kleinere Nummer) fällt zuerst
  `loeschrunde`               die ersten ⌊Anteil · Zahl⌋ der Rangfolge fallen
  `waehle_loeschkandidaten`   alle drei hintereinander (reine Funktion auf Listen)
  `bestandsverlauf`           lebende gelernte Klauseln je Konflikt aus den Ereignissen `lerne` und `loesche` einer Spur
"""
import math
from dataclasses import dataclass, field
from fractions import Fraction

from klo_cdcl import Ergebnis, Loeser
from klo_rng import SplitMix64

REGELN = ("lbd", "laenge", "zufall")
ANTEILE = (Fraction(1, 4), Fraction(1, 2), Fraction(3, 4))
STANDARD_ANTEIL, STANDARD_GRENZE, STANDARD_REGEL = Fraction(1, 2), 2, "lbd"
LOESCH_SEED_VERSATZ = 0x4C6F657363685F31          # trennt den Strom der Zufallsregel vom Strom des Lösers


def lbd(stufen) -> int:
    """LBD (Literal Block Distance): Zahl der verschiedenen Entscheidungsstufen der Literale einer Klausel."""
    return len(set(stufen))


def kandidaten(nummern, lbd_von, gesperrt, grenze=STANDARD_GRENZE, geloescht=()) -> list:
    """Nummern der gelernten, lebenden Klauseln, die fallen dürfen: LBD über der Grenze und nicht gesperrt (Grund eines Trail-Literals).
    `nummern`: die gelernten Klauseln; `lbd_von[nr]`: ihr LBD. Ergebnis aufsteigend nach Nummer."""
    gesperrt, geloescht = set(gesperrt), set(geloescht)
    return sorted(nr for nr in nummern if nr not in geloescht and nr not in gesperrt and lbd_von[nr] > grenze)


def rangfolge(kand, lbd_von, laengen, regel=STANDARD_REGEL, rng=None) -> list:
    """Kandidaten, die zuerst fallen sollen, vorn. Regel „lbd“: absteigend nach (LBD, Länge); „laenge“: absteigend nach (Länge, LBD);
    „zufall“: Fisher-Yates mit SplitMix64 (`rng`). Bei Gleichstand fällt die ältere Klausel (kleinere Nummer) zuerst: der Schlüssel
    enthält −Nummer ausdrücklich, das Ergebnis hängt nicht von der Stabilität des Sortierens oder von der Eingabereihenfolge ab."""
    if regel not in REGELN:
        raise ValueError(f"Regel muss eine von {REGELN} sein")
    if regel == "zufall":
        if rng is None:
            raise ValueError("die Zufallsregel braucht einen SplitMix64-Strom")
        reihe = sorted(kand)
        rng.shuffle(reihe)
        return reihe
    if regel == "lbd":
        return sorted(kand, key=lambda nr: (lbd_von[nr], laengen[nr], -nr), reverse=True)
    return sorted(kand, key=lambda nr: (laengen[nr], lbd_von[nr], -nr), reverse=True)


def loeschrunde(reihenfolge, anteil=STANDARD_ANTEIL) -> list:
    """Die ersten ⌊Anteil · Zahl⌋ der Rangfolge fallen (abgerundet: bei einem Kandidaten und Anteil ½ fällt keiner)."""
    zahl = math.floor(Fraction(anteil).limit_denominator(1000) * len(reihenfolge))
    return list(reihenfolge[:zahl])


def waehle_loeschkandidaten(lbd_von, laengen, gesperrt, anteil=STANDARD_ANTEIL, grenze=STANDARD_GRENZE, regel=STANDARD_REGEL,
                            nummern=None, geloescht=(), rng=None) -> list:
    """Nummern der Klauseln, die diese Runde fallen. Eingabe: LBD und Länge je Nummer (Liste oder Dictionary), Menge der gesperrten Nummern.
    Reine Funktion: dieselbe Rechnung führt der Löser in `LoeschLoeser._reduziere` aus."""
    if nummern is None:
        nummern = lbd_von.keys() if hasattr(lbd_von, "keys") else range(len(lbd_von))
    kand = kandidaten(nummern, lbd_von, gesperrt, grenze, geloescht)
    return loeschrunde(rangfolge(kand, lbd_von, laengen, regel, rng), anteil)


def bestandsverlauf(spur) -> list:
    """Lebende gelernte Klauseln (Länge ≥ 2) nach jedem Konflikt, aus den Ereignissen einer Spur: `lerne` +1 (Einheitsklauseln werden
    nicht gespeichert), `loesche` −Zahl. Ergebnis: [(Konfliktnummer ab 1, lebende Klauseln nach diesem Konflikt)]. Die Spur ist auf 5 000
    Ereignisse begrenzt; für längere Läufe gibt `LoeschLoeser` abgetastete Werte (`Lauf.verlauf`)."""
    punkte, lebend, nr = [], 0, 0
    for e in spur:
        if e[0] == "konflikt":
            nr += 1
            punkte.append([nr, lebend])
        elif e[0] == "lerne" and len(e[1]) >= 2:
            lebend += 1
            punkte[-1][1] = lebend
        elif e[0] == "loesche":
            lebend -= e[1]
            punkte[-1][1] = lebend
    return [tuple(p) for p in punkte]


class LoeschLoeser(Loeser):
    """`Loeser` mit einstellbarer Löschrunde. Mit `anteil=½`, `grenze=2`, `regel="lbd"` löscht er genau wie der Kern (Test).

    Zusätze: `lebend` (gelernte Klauseln der Länge ≥ 2, nicht gelöscht), `runden` (je Löschrunde: Konflikte, Kandidaten, gefallene Nummern),
    `verlauf` (alle `abtast` Konflikte: Konflikte, lebende Klauseln, Lesezugriffe, gelernte Klauseln)."""

    def __init__(self, n, klauseln, *, anteil=STANDARD_ANTEIL, lbd_grenze=STANDARD_GRENZE, regel=STANDARD_REGEL, abtast=0, **optionen):
        if regel not in REGELN:
            raise ValueError(f"Regel muss eine von {REGELN} sein")
        self.anteil, self.lbd_grenze, self.regel, self.abtast = anteil, lbd_grenze, regel, abtast
        self.lebend = 0
        self.runden = []
        self.verlauf = []
        self._zuletzt = -1
        self.loesch_rng = SplitMix64(optionen.get("seed", 0) + LOESCH_SEED_VERSATZ)
        super().__init__(n, klauseln, **optionen)

    def _fuege_hinzu(self, klausel, gelernt, lbd=0):
        vorher = len(self.klauseln)
        ok = super()._fuege_hinzu(klausel, gelernt, lbd)
        if gelernt and len(self.klauseln) > vorher:
            self.lebend += 1
        return ok

    def _reduziere(self):
        gesperrt = {self.grund[abs(l)] for l in self.spur_lit if self.grund[abs(l)] is not None}
        nummern = [i for i in range(len(self.klauseln)) if self.ist_gelernt[i] and not self.geloescht[i]]
        laengen = [len(c) for c in self.klauseln]
        kand = kandidaten(nummern, self.lbd, gesperrt, self.lbd_grenze)
        weg = loeschrunde(rangfolge(kand, self.lbd, laengen, self.regel, self.loesch_rng), self.anteil)
        for i in weg:
            self.geloescht[i] = True
            self.stat["geloescht"] += 1
            self.lebend -= 1
            if self.beweis is not None:
                self.beweis.append(("d", list(self.klauseln[i])))
        self.runden.append((self.stat["konflikte"], len(kand), tuple(weg)))
        if weg:
            self._ereignis("loesche", len(weg))
        return weg

    def propagiere(self):
        k = self.stat["konflikte"]
        if self.abtast and k != self._zuletzt and k % self.abtast == 0:
            self._zuletzt = k
            self.verlauf.append((k, self.lebend, self.stat["lesezugriffe"], self.stat["gelernt"]))
        return super().propagiere()

    def _ergebnis(self, antwort):
        erg = super()._ergebnis(antwort)
        erg.stat["lebend_gelernt"] = self.lebend
        if self.abtast:
            k = self.stat["konflikte"]
            if not self.verlauf or self.verlauf[-1][0] != k:
                self.verlauf.append((k, self.lebend, self.stat["lesezugriffe"], self.stat["gelernt"]))
        return erg


@dataclass
class Lauf:
    ergebnis: Ergebnis
    verlauf: list = field(default_factory=list)
    runden: list = field(default_factory=list)

    @property
    def stat(self) -> dict:
        return self.ergebnis.stat


def lauf(n, klauseln, *, abstand=None, anteil=STANDARD_ANTEIL, lbd_grenze=STANDARD_GRENZE, regel=STANDARD_REGEL, budget=None,
         loeser_seed=None, abtast=0, trace=False, proof=False) -> Lauf:
    """Ein Lauf des Lösers: `abstand` = Löschen alle so viele Konflikte, `None` = nie. `loeser_seed` (ganze Zahl) schaltet eine zufällige
    Anfangsaktivität an (SplitMix64); `None` heißt: feste Reihenfolge der Gleichstände, der Standard der Vormessung."""
    optionen = dict(delete=abstand is not None, delete_every=abstand or 1)
    if loeser_seed is not None:
        optionen.update(noise=True, seed=int(loeser_seed))
    loeser = LoeschLoeser(n, klauseln, anteil=anteil, lbd_grenze=lbd_grenze, regel=regel, abtast=abtast, trace=trace, proof=proof, **optionen)
    erg = loeser.loese((), budget)
    return Lauf(erg, loeser.verlauf, loeser.runden)
