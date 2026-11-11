"""Einheiten der Löschrunde, jede einzeln an der Handtabelle (Plan Stück 5; Sollwerte aus `handbeispiele/hb_05.py` der Planung, von Hand gerechnet)
und am Kern: `LoeschLoeser` mit den Standardeinstellungen löscht genau wie `Loeser(delete=True)` des Kerns."""

from fractions import Fraction

import pytest

import klo_cdcl as K
import klo_instanzen as I
import klo_loeschen as L
import klo_scenario as S
from klo_rng import SplitMix64


# ---------------------------------------------------------------- Handtabelle
def test_lbd_der_handtabelle():
    """LBD = Zahl verschiedener Stufen. Klausel 4 = {x1, x2, x4} liegt auf den Stufen {1, 1, 2} = {1, 2}: LBD 2, Länge 3."""
    assert [L.lbd(S.HAND_STUFEN[v] for v in S.HAND_KLAUSELN[nr]) for nr in range(1, 9)] == [2, 3, 4, 2, 4, 4, 4, 5]
    assert [len(S.HAND_KLAUSELN[nr]) for nr in range(1, 9)] == [2, 3, 4, 3, 5, 5, 4, 6]


def test_kandidaten_der_handtabelle(hand):
    """Klauseln 1 und 4 haben LBD 2 (bleiben immer), 3 und 7 sind gesperrt: Kandidaten sind 2, 5, 6, 8."""
    assert hand.kandidaten == [2, 5, 6, 8]


def test_rangfolge_gleichstand_aelter_faellt_zuerst(hand):
    """8 hat (5, 6), 5 und 6 haben beide (4, 5), 2 hat (3, 3): Reihenfolge 8, dann 5 vor 6 (Gleichstand, ältere zuerst), zuletzt 2."""
    assert hand.rangfolge == [8, 5, 6, 2]


def test_rangfolge_hängt_nicht_von_der_eingabereihenfolge_ab(hand):
    for kand in ([8, 6, 5, 2], [6, 5, 8, 2], [2, 8, 6, 5]):
        assert L.rangfolge(kand, hand.lbd, hand.laenge) == [8, 5, 6, 2]


def test_loeschrunde_der_haelfte_abgerundet(hand):
    """Vier Kandidaten, Anteil ½: zwei fallen, die Klauseln 8 und 5; es bleiben 1, 2, 3, 4, 6, 7 (vorher 8 gelernte, nachher 6)."""
    assert hand.faellt == [8, 5] and hand.bleibt == [1, 2, 3, 4, 6, 7]


@pytest.mark.parametrize("anteil,erwartet", [(Fraction(1, 4), [8]), (Fraction(1, 2), [8, 5]), (Fraction(3, 4), [8, 5, 6])])
def test_anteil_viertel_haelfte_dreiviertel(anteil, erwartet):
    """4 Kandidaten: ¼ → 1, ½ → 2, ¾ → 3 fallen."""
    assert S.hand_runde(anteil=anteil).faellt == erwartet


@pytest.mark.parametrize("grenze,erwartet", [(1, [1, 2, 4, 5, 6, 8]), (2, [2, 5, 6, 8]), (3, [5, 6, 8])])
def test_lbd_grenze(grenze, erwartet):
    """Grenze 1: LBD > 1 gilt auch für die Klauseln 1 und 4 (LBD 2): Kandidaten 1, 2, 4, 5, 6, 8; Grenze 2: 2, 5, 6, 8; Grenze 3: nur LBD ≥ 4, also 5, 6, 8
    (3 und 7 sind gesperrt)."""
    assert S.hand_runde(grenze=grenze).kandidaten == erwartet


def test_gesperrt_schalter():
    """Ohne Sperren sind 3 und 7 Kandidaten (LBD 4): Kandidaten 2, 3, 5, 6, 7, 8; Rangfolge nach (LBD, Länge, Nummer)."""
    h = S.hand_runde(gesperrt=())
    assert h.kandidaten == [2, 3, 5, 6, 7, 8]
    assert h.rangfolge == [8, 5, 6, 3, 7, 2]          # 8 (5,6); 5, 6 (4,5); 3, 7 (4,4) mit 3 vor 7; 2 (3,3)
    assert h.faellt == [8, 5, 6]


def test_regel_laenge_und_zufall_an_der_handtabelle():
    """Länge zuerst: 8 (6), 5 und 6 (5, älter zuerst), 2 (3) → 8, 5, 6, 2. Zufall: eine Permutation derselben Kandidaten, gleicher Seed gleiche Folge."""
    assert S.hand_runde(regel="laenge").rangfolge == [8, 5, 6, 2]
    a, b = S.hand_runde(regel="zufall", seed=3), S.hand_runde(regel="zufall", seed=3)
    assert sorted(a.rangfolge) == [2, 5, 6, 8] and a.rangfolge == b.rangfolge and len(a.faellt) == 2
    assert any(S.hand_runde(regel="zufall", seed=s).rangfolge != [8, 5, 6, 2] for s in range(10))


def test_waehle_loeschkandidaten_auf_listen():
    """Dieselbe Rechnung auf Listen (Nummer = Index): Nummern 0 bis 7 = Klauseln 1 bis 8, gesperrt {2, 6}."""
    lbd_v = [2, 3, 4, 2, 4, 4, 4, 5]
    laenge = [2, 3, 4, 3, 5, 5, 4, 6]
    assert L.waehle_loeschkandidaten(lbd_v, laenge, {2, 6}) == [7, 4]


def test_unbekannte_regel_wird_abgelehnt():
    with pytest.raises(ValueError):
        L.rangfolge([1], {1: 3}, {1: 3}, "unsinn")
    with pytest.raises(ValueError):
        L.rangfolge([1], {1: 3}, {1: 3}, "zufall")          # ohne Strom
    with pytest.raises(ValueError):
        L.LoeschLoeser(3, [(1, 2)], regel="unsinn")


# ---------------------------------------------------------------- Bestandsverlauf (Sägezahn von Hand)
def test_bestandsverlauf_saegezahn_von_hand():
    """Spur von Hand: sechs Konflikte, je eine gelernte Klausel der Länge 2 (eine Einheitsklausel in Konflikt 4 wird nicht gespeichert);
    nach Konflikt 3 und 6 fällt je eine Klausel. Lebend nach jedem Konflikt: 1, 2, 2 (3 gelernt, 1 gelöscht), 2 (Einheit), 3, 3."""
    spur = [("konflikt", [1], 1, 0), ("lerne", [1, 2], 0, 2),
            ("konflikt", [1], 1, 0), ("lerne", [3, 4], 0, 2),
            ("konflikt", [1], 1, 0), ("lerne", [5, 6], 0, 2), ("loesche", 1),
            ("konflikt", [1], 1, 0), ("lerne", [7], 0, 1),
            ("konflikt", [1], 1, 0), ("lerne", [8, 9], 0, 2),
            ("konflikt", [1], 1, 0), ("lerne", [3, 8], 0, 2), ("loesche", 1)]
    assert L.bestandsverlauf(spur) == [(1, 1), (2, 2), (3, 2), (4, 2), (5, 3), (6, 3)]


# ---------------------------------------------------------------- Löser
def test_loeser_mit_standardregel_loescht_wie_der_kern():
    """Gleiche Konflikte, gleiche gelöschte Klauseln, gleiche Lesezugriffe wie `Loeser(delete=True)` des Kerns (Formel n = 120)."""
    inst = I.rand3(120, 511, 4000)
    kern = K.solve(inst.n, inst.klauseln, delete=True, delete_every=100)
    mein = L.lauf(inst.n, inst.klauseln, abstand=100)
    for schluessel in ("konflikte", "lesezugriffe", "gelernt", "geloescht", "besuche", "propagationen"):
        assert mein.stat[schluessel] == kern.stat[schluessel], schluessel
    assert mein.ergebnis.antwort == kern.antwort and kern.stat["geloescht"] > 0


def test_ohne_loeschen_loesche_nie():
    inst = I.rand3(100, 426, 4000)
    r = L.lauf(inst.n, inst.klauseln, abstand=None)
    assert r.stat["geloescht"] == 0 and r.runden == []


def test_abtastung_enthaelt_start_und_ende():
    inst = I.rand3(100, 426, 4000)
    r = L.lauf(inst.n, inst.klauseln, abstand=50, abtast=10)
    assert r.verlauf[0] == (0, 0, 0, 0)
    assert r.verlauf[-1][0] == r.stat["konflikte"] and r.verlauf[-1][1] == r.stat["lebend_gelernt"]
    assert [p[0] for p in r.verlauf] == sorted(set(p[0] for p in r.verlauf))
