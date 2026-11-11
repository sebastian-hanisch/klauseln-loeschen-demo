"""Eigenschaften der Löschrunde, an echten Läufen geprüft: ein Löser, der vor jeder Runde den Zustand festhält und danach vergleicht."""
from fractions import Fraction

import pytest

import klo_instanzen as I
import klo_loeschen as L


class Beobachter(L.LoeschLoeser):
    """Hält je Löschrunde fest, was vorher galt (lebende gelernte Klauseln, Gesperrte, Ausgangsklauseln, LBD, Längen) und was fiel."""

    def __init__(self, *a, **kw):
        self.protokoll = []
        super().__init__(*a, **kw)

    def _reduziere(self):
        gesperrt = {self.grund[abs(l)] for l in self.spur_lit if self.grund[abs(l)] is not None}
        lebend = [i for i in range(len(self.klauseln)) if self.ist_gelernt[i] and not self.geloescht[i]]
        ausgang = {i for i in range(len(self.klauseln)) if not self.ist_gelernt[i]}
        lbd, laenge = list(self.lbd), [len(c) for c in self.klauseln]
        weg = super()._reduziere()
        self.protokoll.append(dict(gesperrt=gesperrt, lebend=lebend, ausgang=ausgang, lbd=lbd, laenge=laenge, weg=weg, grenze=self.lbd_grenze,
                                   anteil=self.anteil, regel=self.regel))
        return weg


def _laeufe():
    for seed, abstand, anteil, grenze, regel in [(4008, 40, Fraction(1, 2), 2, "lbd"), (4004, 25, Fraction(1, 4), 1, "lbd"), (4009, 30, Fraction(3, 4), 3, "laenge"),
                                                 (4006, 20, Fraction(1, 2), 2, "zufall")]:
        inst = I.rand3(110, 469, seed)
        lo = Beobachter(inst.n, inst.klauseln, anteil=anteil, lbd_grenze=grenze, regel=regel, delete=True, delete_every=abstand)
        lo.loese(conflict_budget=3000)
        yield (seed, anteil, grenze, regel), lo


@pytest.fixture(scope="module")
def beobachtet():
    return list(_laeufe())


def test_es_gab_loeschrunden_mit_gefallenen_klauseln(beobachtet):
    for name, lo in beobachtet:
        assert sum(len(p["weg"]) > 0 for p in lo.protokoll) >= 3, name


def test_gesperrte_klauseln_fallen_nie(beobachtet):
    for name, lo in beobachtet:
        assert any(p["gesperrt"] for p in lo.protokoll), f"{name}: nie eine Sperre gesehen, der Test prüft nichts"
        for p in lo.protokoll:
            assert not set(p["weg"]) & p["gesperrt"], name


def test_klauseln_mit_lbd_hoechstens_grenze_fallen_nie(beobachtet):
    for name, lo in beobachtet:
        for p in lo.protokoll:
            assert all(p["lbd"][i] > p["grenze"] for i in p["weg"]), name


def test_urspruengliche_klauseln_fallen_nie(beobachtet):
    for name, lo in beobachtet:
        for p in lo.protokoll:
            assert not set(p["weg"]) & p["ausgang"], name
        assert not any(lo.geloescht[i] for i in range(len(lo.klauseln)) if not lo.ist_gelernt[i])


def test_nur_lebende_gelernte_fallen_und_jede_nur_einmal(beobachtet):
    for name, lo in beobachtet:
        alle = []
        for p in lo.protokoll:
            assert set(p["weg"]) <= set(p["lebend"]), name
            alle += p["weg"]
        assert len(alle) == len(set(alle)) == lo.stat["geloescht"]


def test_zahl_lebender_klauseln_nach_einer_runde_mindestens_gelernt_minus_halbe_kandidaten(beobachtet):
    """Nach einer Runde sind mindestens |lebend| − ⌊a · |Kandidaten|⌋ Klauseln übrig; es fallen nie mehr als der Anteil der Kandidaten."""
    for name, lo in beobachtet:
        for p, (_, kandidaten, weg) in zip(lo.protokoll, lo.runden):
            assert len(p["weg"]) == len(weg) and len(p["weg"]) <= p["anteil"] * kandidaten
            assert len(p["lebend"]) - len(p["weg"]) >= len(p["lebend"]) - p["anteil"] * kandidaten


def test_gefallene_sind_schlechter_als_alle_bleibenden_kandidaten_gleichstand_nach_nummer(beobachtet):
    """Regeln „lbd“ und „laenge“: Jede gefallene Klausel ist nach dem Schlüssel mindestens so schlecht wie jeder bleibende Kandidat; bei gleichem Schlüssel fällt die kleinere Nummer."""
    for name, lo in beobachtet:
        if name[3] == "zufall":
            continue
        for p in lo.protokoll:
            kand = [i for i in p["lebend"] if p["lbd"][i] > p["grenze"] and i not in p["gesperrt"]]
            bleibt = [i for i in kand if i not in p["weg"]]
            schluessel = (lambda i: (p["lbd"][i], p["laenge"][i])) if p["regel"] == "lbd" else (lambda i: (p["laenge"][i], p["lbd"][i]))
            for d in p["weg"]:
                for b in bleibt:
                    assert schluessel(d) > schluessel(b) or (schluessel(d) == schluessel(b) and d < b), (name, d, b)


def test_antwort_haengt_nicht_vom_loeschabstand_ab():
    """Zehn Formeln (n = 50), erfüllbar und unerfüllbar: dieselbe Antwort ohne Löschen und bei jedem Abstand."""
    antworten = set()
    for seed in range(10):
        inst = I.rand3(50, 213, 800 + seed)
        a = {L.lauf(inst.n, inst.klauseln, abstand=ab, budget=50000).ergebnis.antwort for ab in (None, 10, 50, 250)}
        assert len(a) == 1 and None not in a, seed
        antworten |= a
    assert antworten == {True, False}


def test_ohne_loeschen_sind_lebende_gleich_gelernte_der_laenge_mindestens_zwei():
    """Ohne Löschen: lebend_gelernt = gelernt − gelernte Einheitsklauseln (Einheitsklauseln werden nicht gespeichert); die Einheiten zählt das Beweisprotokoll."""
    for seed in range(5):
        inst = I.rand3(80, 341, 40 + seed)
        r = L.lauf(inst.n, inst.klauseln, abstand=None, proof=True)
        einheiten = sum(1 for art, k in r.ergebnis.beweis if art == "a" and len(k) == 1)
        assert r.stat["lebend_gelernt"] == r.stat["gelernt"] - einheiten
