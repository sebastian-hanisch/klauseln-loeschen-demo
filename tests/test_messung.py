"""Die eingefrorene Messung `klo_messung.json`: Aufbau, Zweig-Test (jede Variante weicht auf mindestens einer Formel von der Nachbarvariante ab),
Antworten je Formel gleich, und eine kleine Teilmenge wird live nachgerechnet (Zähler sind ganzzahlig und deterministisch)."""
import pytest

import klo_evaluation as E
import klo_messung as M

ABSTAENDE = (250, 500, 1000, 2000, None)
REGELN = ("lbd", "laenge", "zufall")


@pytest.fixture(scope="module")
def messung():
    return M.lade_messung()


def test_aufbau_je_familie_20_formeln_mit_zwoelf_laeufen(messung):
    for fam in M.FAMILIEN:
        zeilen = messung[fam]["zeilen"]
        assert sorted({z["formel"] for z in zeilen}) == list(range(20))
        assert len(zeilen) == 20 * 12
        for a in ABSTAENDE:
            assert len(E.waehle(zeilen, a)) == 20
        for s in E.REFERENZ_SEEDS:
            assert len(E.waehle(zeilen, loeser_seed=s)) == 20
        for r in ("laenge", "zufall"):
            assert len(E.waehle(zeilen, 500, r)) == 20


def test_wiederholung_der_vormessung_n200_acht_formeln_drei_varianten(messung):
    zeilen = messung["vor200"]["zeilen"]
    assert len(zeilen) == 24 and messung["vor200"]["parameter"]["n"] == 200
    for a in (None, 500, 2000):
        assert len(E.waehle(zeilen, a)) == 8


def test_zweig_test_nachbarvarianten_weichen_ab(messung):
    """Sonst wäre eine Variante tot: sie liefe nie anders als ihre Nachbarin. Verglichen werden Konflikte und Lesezugriffe je Formel."""
    def weicht_ab(zeilen, a, b):
        return any((x["konflikte"], x["lesezugriffe"]) != (y["konflikte"], y["lesezugriffe"]) for x, y in zip(a, b))

    for fam in M.FAMILIEN:
        zeilen = messung[fam]["zeilen"]
        for a, b in zip(ABSTAENDE, ABSTAENDE[1:]):
            assert weicht_ab(zeilen, E.waehle(zeilen, a), E.waehle(zeilen, b)), (fam, a, b)
        for r in ("laenge", "zufall"):
            assert weicht_ab(zeilen, E.waehle(zeilen, 500, "lbd"), E.waehle(zeilen, 500, r)), (fam, r)
        assert weicht_ab(zeilen, E.waehle(zeilen, 500, "laenge"), E.waehle(zeilen, 500, "zufall")), fam
        assert weicht_ab(zeilen, E.waehle(zeilen), E.waehle(zeilen, loeser_seed=1)), fam      # die zufällige Anfangsaktivität ändert die Suche
    z = messung["vor200"]["zeilen"]
    assert weicht_ab(z, E.waehle(z), E.waehle(z, 500)) and weicht_ab(z, E.waehle(z, 500), E.waehle(z, 2000))


def test_antwort_je_formel_in_allen_laeufen_ohne_abbruch_gleich(messung):
    for fam in (*M.FAMILIEN, "vor200"):
        je_formel = {}
        for z in messung[fam]["zeilen"]:
            if z["antwort"] != "abbruch":
                je_formel.setdefault(z["formel"], set()).add(z["antwort"])
        assert all(len(a) == 1 for a in je_formel.values()), fam


def test_gelernt_und_lebend_sind_konsistent(messung):
    for fam in (*M.FAMILIEN, "vor200"):
        for z in messung[fam]["zeilen"]:
            assert z["lebend"] <= z["gelernt"] - z["geloescht"]            # Einheitsklauseln zählen bei gelernt, aber nicht beim Bestand
            if z["abstand"] is None:
                assert z["geloescht"] == 0
            assert z["abstand"] is None or z["geloescht"] == 0 or z["konflikte"] >= z["abstand"]


@pytest.mark.parametrize("familie,n,formel", [("zufall", 175, 1), ("zufall", 175, 6), ("zufall", 175, 10), ("faerbung", 300, 3), ("faerbung", 300, 5)])
def test_teilmenge_wird_live_nachgerechnet(messung, familie, n, formel):
    """Dieselben Zahlen wie in der Datei, wenn man die Läufe dieser Formel neu rechnet (feste Seeds, ganzzahliger Zufall)."""
    zeilen = messung[familie]["zeilen"]
    assert messung[familie]["parameter"]["n"] == n
    neu = M.messreihe(familie, n, [formel], (500, None), messung[familie]["parameter"]["budget"], (1,), ("lbd", "zufall"), 500)
    for z in neu:
        alt = [x for x in zeilen if all(x[k] == z[k] for k in ("formel", "abstand", "regel", "loeser_seed"))]
        assert len(alt) == 1 and alt[0] == z
