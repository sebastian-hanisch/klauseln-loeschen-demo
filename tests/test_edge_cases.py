"""Randfälle: keine Kandidaten, genau ein und genau zwei Kandidaten, Löschabstand größer als das Budget, Aufgabe ohne Konflikt, leere Eingaben."""
from fractions import Fraction

import pytest

import klo_algorithm as A
import klo_evaluation as E
import klo_instanzen as I
import klo_loeschen as L
import klo_scenario as S


def test_keine_kandidaten_hat_die_haelfte_von_null():
    """Alle Klauseln gesperrt: kein Kandidat, nichts fällt, alle 8 bleiben."""
    h = S.hand_runde(gesperrt=range(1, 9))
    assert h.kandidaten == [] and h.faellt == [] and h.bleibt == list(range(1, 9))
    art, text = E.verdict_hand(h)
    assert art == "info" and "Keine Klausel ist Kandidat" in text and "alle 8 gelernten Klauseln bleiben" in text


@pytest.mark.parametrize("anteil", [Fraction(1, 4), Fraction(1, 2), Fraction(3, 4)])
def test_genau_ein_kandidat_abgerundet_faellt_keiner(anteil):
    """Nur Klausel 8 ist Kandidat (2, 3, 5, 6, 7 gesperrt; 1 und 4 haben LBD 2): ⌊a · 1⌋ = 0 für a ≤ ¾."""
    h = S.hand_runde(gesperrt=(2, 3, 5, 6, 7), anteil=anteil)
    assert h.kandidaten == [8] and h.faellt == []
    art, text = E.verdict_hand(h, anteil)
    assert art == "info" and "= 0: abgerundet fällt keine Klausel" in text


def test_genau_zwei_kandidaten_haelfte_ist_einer():
    """Kandidaten 6 und 8 (2, 3, 5, 7 gesperrt): Rangfolge 8, 6; bei ½ fällt die 8, bei ¾ ⌊1,5⌋ = 1 ebenfalls nur die 8, bei ¼ keiner."""
    assert S.hand_runde(gesperrt=(2, 3, 5, 7), anteil=Fraction(1, 2)).faellt == [8]
    assert S.hand_runde(gesperrt=(2, 3, 5, 7), anteil=Fraction(3, 4)).faellt == [8]
    assert S.hand_runde(gesperrt=(2, 3, 5, 7), anteil=Fraction(1, 4)).faellt == []


def test_leere_eingaben():
    assert L.waehle_loeschkandidaten([], [], set()) == []
    assert L.waehle_loeschkandidaten({}, {}, set()) == []
    assert L.bestandsverlauf([]) == []
    assert L.loeschrunde([], Fraction(1, 2)) == []


def test_abstand_groesser_als_das_budget_loescht_nie():
    inst = I.rand3(100, 426, 4000)
    r = L.lauf(inst.n, inst.klauseln, abstand=10 ** 6, budget=400)
    assert r.stat["geloescht"] == 0 and r.runden == [] and r.stat["konflikte"] <= 400
    o = L.lauf(inst.n, inst.klauseln, abstand=None, budget=400)
    assert r.stat["konflikte"] == o.stat["konflikte"] and r.stat["lesezugriffe"] == o.stat["lesezugriffe"]


def test_aufgabe_ohne_konflikt():
    """(x1 ∨ x2)(¬x1 ∨ x3): wird ohne Konflikt gelöst; nichts wird gelernt, gelöscht oder gelesen, das Verdikt sagt es."""
    r = L.lauf(3, [(1, 2), (-1, 3)], abstand=1)
    assert r.ergebnis.antwort is True and r.stat["konflikte"] == 0 and r.stat["gelernt"] == 0 and r.stat["geloescht"] == 0 and r.stat["lebend_gelernt"] == 0
    live = A.live_vergleich("zufall", 60, 1, 5000, None)
    assert live.abstand is None


def test_verdikt_bestand_ohne_konflikt_und_ohne_loeschrunde():
    class Fake:
        def __init__(self, stat, antwort=True):
            self.stat = stat
            self.ergebnis = type("E", (), {"antwort": antwort})()

    stat0 = {"konflikte": 0, "lebend_gelernt": 0, "lesezugriffe": 10, "gelernt": 0, "geloescht": 0}
    v = type("V", (), {"ohne": Fake(stat0), "mit": Fake(stat0), "abstand": 250})()
    assert E.verdict_bestand(v) == ("info", "Die Aufgabe ist ohne Konflikt gelöst: es wird nichts gelernt und nichts gelöscht.")
    stat1 = {"konflikte": 100, "lebend_gelernt": 90, "lesezugriffe": 5000, "gelernt": 95, "geloescht": 0}
    v = type("V", (), {"ohne": Fake(stat1), "mit": Fake(stat1), "abstand": 250})()
    art, text = E.verdict_bestand(v)
    assert art == "info" and "keine Löschrunde" in text and "90 lebende gelernte Klauseln" in text


def test_regeln_mit_gleichem_schluessel_hängen_nicht_von_der_eingabereihenfolge_ab():
    lbd_v, laenge = {1: 4, 2: 4, 3: 4}, {1: 5, 2: 5, 3: 5}
    assert L.rangfolge([3, 1, 2], lbd_v, laenge) == [1, 2, 3] == L.rangfolge([2, 3, 1], lbd_v, laenge, "laenge")
