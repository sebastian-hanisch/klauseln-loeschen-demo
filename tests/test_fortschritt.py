"""Live-Aufgabe und Live-Messreihe mit Fortschrittsanzeige und Zwischenspeicher: das Ergebnis ist gleich dem ungepufferten, ein anderer Parameter kommt nicht aus dem Speicher."""

import os
from fractions import Fraction

from streamlit.testing.v1 import AppTest

import klo_algorithm as A
import klo_constants as C
import klo_evaluation as E
import klo_fortschritt as F
import klo_messung as M

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _leeren():
    F.lauf_ohne.clear()
    F.lauf_mit.clear()
    F.messreihe_formel.clear()


def test_zwischengespeicherter_vergleich_ist_gleich_dem_ungepufferten():
    _leeren()
    for familie, n, seed, budget, abstand in (("zufall", 60, 3, 2000, 500), ("faerbung", 60, 3, 2000, 250), ("zufall", 60, 3, 2000, 0)):
        direkt = A.live_vergleich(familie, n, seed, budget, abstand or None, Fraction(50, 100), 2, "lbd")
        assert F.live_vergleich(familie, n, seed, budget, abstand, 50, 2, "lbd") == direkt, (familie, abstand)
        assert F.live_vergleich(familie, n, seed, budget, abstand, 50, 2, "lbd") == direkt, (familie, abstand, "zweiter Aufruf aus dem Zwischenspeicher")


def test_anderer_abstand_rechnet_nur_den_lauf_mit_loeschen_neu():
    _leeren()
    v0 = F.gerechnet()
    erste = F.live_vergleich("zufall", 60, 3, 2000, 500, 50, 2, "lbd")
    v1 = F.gerechnet()
    assert v1 - v0 == 2
    assert F.live_vergleich("zufall", 60, 3, 2000, 500, 50, 2, "lbd") == erste and F.gerechnet() == v1
    anderer = F.live_vergleich("zufall", 60, 3, 2000, 250, 50, 2, "lbd")
    assert F.gerechnet() - v1 == 1, "nur der Lauf mit Löschen hängt vom Abstand ab"
    assert anderer.ohne == erste.ohne
    assert anderer == A.live_vergleich("zufall", 60, 3, 2000, 250, Fraction(50, 100), 2, "lbd")
    v2 = F.gerechnet()
    F.live_vergleich("zufall", 60, 3, 2000, 250, 75, 2, "lbd")
    assert F.gerechnet() - v2 == 1, "ein anderer Anteil rechnet den Lauf mit Löschen neu"
    F.live_vergleich("zufall", 60, 4, 2000, 250, 75, 2, "lbd")
    assert F.gerechnet() - v2 == 3, "ein anderer Zufalls-Seed rechnet beide Läufe neu"
    F.live_vergleich("zufall", 60, 4, 5000, 250, 75, 2, "lbd")
    assert F.gerechnet() - v2 == 5, "ein anderes Budget rechnet beide Läufe neu"


def test_zwischengespeicherte_messreihe_ist_gleich_der_ungepufferten():
    _leeren()
    for familie in ("zufall", "faerbung"):
        direkt = M.messreihe(familie, 60, range(3), C.LIVE_ABSTAENDE, 2000, E.REFERENZ_SEEDS, haupt_regel="lbd", anteil=Fraction(50, 100), grenze=2)
        assert F.messreihe(familie, 60, 3, 2000, 50, 2, "lbd") == direkt, familie
        assert F.messreihe(familie, 60, 3, 2000, 50, 2, "lbd") == direkt, (familie, "zweiter Aufruf aus dem Zwischenspeicher")


def test_messreihe_zweiter_aufruf_rechnet_nichts_neu_ein_anderer_parameter_schon():
    _leeren()
    v0 = F.gerechnet()
    erste = F.messreihe("zufall", 60, 3, 2000, 50, 2, "lbd")
    assert F.gerechnet() - v0 == 3
    v1 = F.gerechnet()
    assert F.messreihe("zufall", 60, 3, 2000, 50, 2, "lbd") == erste and F.gerechnet() == v1
    mehr = F.messreihe("zufall", 60, 4, 2000, 50, 2, "lbd")
    assert F.gerechnet() - v1 == 1, "nur die neue Formel wird gerechnet"
    assert mehr[: len(erste)] == erste
    v2 = F.gerechnet()
    andere = F.messreihe("zufall", 60, 3, 2000, 50, 1, "lbd")
    assert F.gerechnet() - v2 == 3, "eine andere LBD-Grenze darf nicht aus dem Zwischenspeicher kommen"
    assert andere == M.messreihe("zufall", 60, range(3), C.LIVE_ABSTAENDE, 2000, E.REFERENZ_SEEDS, haupt_regel="lbd", anteil=Fraction(50, 100), grenze=1)
    v3 = F.gerechnet()
    F.messreihe("zufall", 70, 3, 2000, 50, 2, "lbd")
    assert F.gerechnet() - v3 == 3, "ein anderes n darf nicht aus dem Zwischenspeicher kommen"


def test_fortschritt_meldet_jeden_schritt_in_ordnung():
    _leeren()
    meldungen = []
    F.messreihe("zufall", 60, 3, 1000, 50, 2, "lbd", lambda fertig, gesamt: meldungen.append((fertig, gesamt)))
    assert meldungen == [(1, 3), (2, 3), (3, 3)]
    meldungen.clear()
    F.live_vergleich("zufall", 60, 3, 1000, 500, 50, 2, "lbd", lambda fertig, gesamt: meldungen.append((fertig, gesamt)))
    assert meldungen == [(1, 2), (2, 2)]
    meldungen.clear()
    F.live_vergleich("zufall", 60, 3, 1000, 0, 50, 2, "lbd", lambda fertig, gesamt: meldungen.append((fertig, gesamt)))
    assert meldungen == [(1, 1)]


def test_app_zweiter_klick_kommt_aus_dem_zwischenspeicher_und_zeigt_dasselbe():
    _leeren()
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    at.slider(key="live_n_slider").set_value(60).run(timeout=TIMEOUT)
    at.slider(key="live_f_slider").set_value(4).run(timeout=TIMEOUT)
    at.button(key="live_rechnen").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    erste = [d.value.to_dict("records") for d in at.dataframe]
    v = F.gerechnet()
    at.button(key="live_rechnen").click().run(timeout=TIMEOUT)
    assert not at.exception and F.gerechnet() == v
    assert [d.value.to_dict("records") for d in at.dataframe] == erste
