"""Jede Zahl der README (und der Texte der App) wird hier nachgerechnet. Zahl -> Test steht in der Tabelle „Befunde“ der README.

Quelle der Messzahlen ist die eingefrorene Messung `klo_messung.json` (Messung dieses Repos mit `tools/messung_klo.py`, Zufalls-Seeds 4000 bis 4019 des SplitMix64-Erzeugers,
ein Lauf je Formel und Variante). Die Tests rechnen die Kennzahlen aus den Zeilen der Datei nach; eine Teilmenge der Läufe wird in `tests/test_messung.py` live neu gerechnet.
Zeiten kommen nirgends vor."""
import pytest

import klo_constants as C
import klo_evaluation as E
import klo_messung as M
import klo_scenario as S


@pytest.fixture(scope="module")
def d():
    return M.lade_messung()


def _k(z, a=None, regel="lbd"):
    return E.kennzahlen(E.waehle(z, a, regel))


def _pct(neu, basis):
    return round(abs(E.aenderung(neu, basis)))


# ---------------------------------------------------------------- Handtabelle
def test_claim_handtabelle():
    h = S.hand_runde()
    assert list(h.lbd.values()) == [2, 3, 4, 2, 4, 4, 4, 5] and list(h.laenge.values()) == [2, 3, 4, 3, 5, 5, 4, 6]
    assert h.kandidaten == [2, 5, 6, 8] and h.rangfolge == [8, 5, 6, 2] and h.faellt == [8, 5] and h.bleibt == [1, 2, 3, 4, 6, 7]
    assert len(S.HAND_KLAUSELN) == 8 and len(h.bleibt) == 6


# ---------------------------------------------------------------- Zufalls-3-SAT n = 175
def test_claim_zufall_aufbau(d):
    p = d["zufall"]["parameter"]
    assert (p["n"], p["budget"], len(p["formeln"]), p["regel_abstand"]) == (175, 60000, 20, 500) and M.M_PRO_N == 4.26 and round(4.26 * 175) == 746
    base = E.waehle(d["zufall"]["zeilen"])
    assert sum(z["antwort"] == "sat" for z in base) == 10 and sum(z["antwort"] == "unsat" for z in base) == 10 and not any(z["antwort"] == "abbruch" for z in d["zufall"]["zeilen"])


def test_claim_zufall_bestand_und_lesezugriffe(d):
    z = d["zufall"]["zeilen"]
    ohne = _k(z)
    assert (ohne.lebend_median, ohne.lesezugriffe_summe) == (5586, 157495526)
    erwartet = {250: (449, 92, 77707239, 51), 500: (822, 85, 72336432, 54), 1000: (1374, 75, 72209617, 54), 2000: (2464, 56, 97474904, 38)}
    for a, (lebend, lebend_pct, lesen, lesen_pct) in erwartet.items():
        k = _k(z, a)
        assert k.lebend_median == lebend and _pct(k.lebend_median, ohne.lebend_median) == lebend_pct, a
        assert k.lesezugriffe_summe == lesen and _pct(k.lesezugriffe_summe, ohne.lesezugriffe_summe) == lesen_pct, a
        assert k.lesezugriffe_summe < ohne.lesezugriffe_summe and k.mit_loeschen == {250: 20, 500: 19, 1000: 18, 2000: 17}[a]


def test_claim_zufall_konflikte_gegen_die_streubreite(d):
    z = d["zufall"]["zeilen"]
    s = E.streuung(z)
    assert s.mediane == (5588, 6576.5, 5098, 5618, 6240.5, 4848.5) and (s.untere, s.obere) == (4848.5, 6576.5) and round(s.faktor_median, 2) == 1.94
    med = {a: _k(z, a).konflikte_median for a in (250, 500, 1000, 2000)}
    assert med == {250: 12253.5, 500: 6383, 1000: 5213, 2000: 6079.5} and _k(z).konflikte_median == 5588
    assert [s.untere <= med[a] <= s.obere for a in (250, 500, 1000, 2000)] == [False, True, True, True]
    assert med[250] > s.obere and round(E.aenderung(med[250], 5588)) == 119
    summen = {a: sum(x["konflikte"] for x in E.waehle(z, a)) for a in (250, 500, 1000, 2000, None)}
    assert summen == {250: 215785, 500: 161035, 1000: 123515, 2000: 125832, None: 124643}
    assert _k(z).konflikte_max == 12419 and _k(z, 250).konflikte_max == 30921 and _k(z, 500).konflikte_max == 21908


def test_claim_zufall_paarvergleich(d):
    z = d["zufall"]["zeilen"]
    assert E.paarvergleich(z, 500) == {"aktiv": 19, "formeln": 20, "weniger_konflikte": 5, "gleich_konflikte": 0, "mehr_konflikte": 14, "weniger_lesezugriffe": 16}
    assert E.paarvergleich(z, 250)["mehr_konflikte"] == 13 and E.paarvergleich(z, 250)["weniger_konflikte"] == 6


def test_claim_zufall_regeln(d):
    z = d["zufall"]["zeilen"]
    s = E.streuung(z)
    k = {r: _k(z, 500, r) for r in C.REGELN}
    assert [k[r].konflikte_median for r in C.REGELN] == [6383, 6955.5, 10419]
    assert [k[r].lesezugriffe_summe for r in C.REGELN] == [72336432, 67533510, 129845877]
    assert [k[r].lebend_median for r in C.REGELN] == [822, 741.5, 729]
    assert s.untere <= k["lbd"].konflikte_median <= s.obere and k["laenge"].konflikte_median > s.obere and k["zufall"].konflikte_median > s.obere
    assert 6955.5 - 6576.5 == 379 and round(E.aenderung(k["zufall"].konflikte_median, _k(z).konflikte_median)) == 86
    # LBD und Länge sind in den Konflikten nicht trennbar: Länge liegt 5,8 % über der Bandobergrenze, 9 % über LBD; das Band ist 31 % des Medians ohne Löschen breit
    assert round(E.aenderung(6955.5, s.obere), 1) == 5.8 and round(E.aenderung(6955.5, 6383)) == 9 and round(100 * (s.obere - s.untere) / 5588) == 31
    assert k["laenge"].lesezugriffe_summe < k["lbd"].lesezugriffe_summe
    # Abstand 500 insgesamt: Median 14 % über dem Wert ohne Löschen
    assert round(E.aenderung(_k(z, 500).konflikte_median, 5588)) == 14


# ---------------------------------------------------------------- 3-Färbung n = 300 Knoten
def test_claim_faerbung(d):
    z = d["faerbung"]["zeilen"]
    p = d["faerbung"]["parameter"]
    assert (p["n"], p["budget"], len(p["formeln"])) == (300, 30000, 20) and M.FAERBUNG_GRAD == 4.5
    ohne = _k(z)
    assert ohne.lesezugriffe_summe == 164589374 and ohne.konflikte_median == 262 and ohne.abbrueche == 0 and ohne.konflikte_max == 20222
    erwartet = {250: (57542590, 65, 10, 2), 500: (69626411, 58, 7, 1), 1000: (73942416, 55, 5, 1), 2000: (109030893, 34, 4, 1)}
    for a, (lesen, pct, loeschen, abbr) in erwartet.items():
        k = _k(z, a)
        assert (k.lesezugriffe_summe, _pct(k.lesezugriffe_summe, ohne.lesezugriffe_summe), k.mit_loeschen, k.abbrueche) == (lesen, pct, loeschen, abbr), a
        assert sum(x["konflikte"] >= a for x in E.waehle(z)) == loeschen            # nur Formeln mit mindestens so vielen Konflikten ohne Löschen erreichen eine Runde
    assert [_k(z, a).konflikte_median for a in (500, 1000, 2000)] == [262, 262, 262]
    assert sum(x["antwort"] == "sat" for x in E.waehle(z)) == 18 and sum(x["antwort"] == "unsat" for x in E.waehle(z)) == 2
    assert round(E.streuung(z).faktor_median, 1) == 10.1 and (E.streuung(z).untere, E.streuung(z).obere) == (226.5, 532)


def test_claim_faerbung_summe_ist_ein_abbruch_vor_dem_ergebnis(d):
    """Auf eine Formel (Formel 7) entfallen 75 % der Summe ohne Löschen und bricht mit Löschen bei jedem Abstand am Budget ab; ohne sie ändert sich die Summe um -22 / -11 / -34 / -6 %."""
    z = d["faerbung"]["zeilen"]
    ohne = {x["formel"]: x for x in E.waehle(z)}
    gesamt = sum(x["lesezugriffe"] for x in ohne.values())
    gross = ohne[7]
    assert (gross["konflikte"], gross["lesezugriffe"], round(100 * gross["lesezugriffe"] / gesamt)) == (20222, 122674465, 75)
    erwartet_mit = {250: 25018805, 500: 32146838, 1000: 46253774, 2000: 69764445}
    erwartet_pct = {250: -22, 500: -11, 1000: -34, 2000: -6}
    for a in (250, 500, 1000, 2000):
        mit = {x["formel"]: x for x in E.waehle(z, a)}
        assert (mit[7]["lesezugriffe"], mit[7]["konflikte"]) == (erwartet_mit[a], 30000), a
        rest_ohne = gesamt - gross["lesezugriffe"]
        rest_mit = sum(x["lesezugriffe"] for f, x in mit.items() if f != 7)
        assert round(E.aenderung(rest_mit, rest_ohne)) == erwartet_pct[a], a
    assert E.paarvergleich(z, 500)["aktiv"] == 7 and E.paarvergleich(z, 500)["weniger_lesezugriffe"] == 4


def test_claim_faerbung_regeln(d):
    z = d["faerbung"]["zeilen"]
    assert [_k(z, 500, r).lesezugriffe_summe for r in C.REGELN] == [69626411, 58665173, 76597627]
    assert [_k(z, 500, r).abbrueche for r in C.REGELN] == [1, 1, 2]
    assert [_k(z, 500, r).konflikte_median for r in C.REGELN] == [262, 262, 262]


# ---------------------------------------------------------------- Wiederholung der Vormessung (n = 200)
def test_claim_wiederholung_der_vormessung_n200(d):
    z = d["vor200"]["zeilen"]
    p = d["vor200"]["parameter"]
    assert (p["n"], p["budget"], len(p["formeln"])) == (200, 200000, 8) and round(4.26 * 200) == 852
    ohne, k500, k2000 = _k(z), _k(z, 500), _k(z, 2000)
    assert (ohne.konflikte_median, k500.konflikte_median, k2000.konflikte_median) == (7252.5, 8975, 7519.5)
    assert (ohne.konflikte_max, k500.konflikte_max, k2000.konflikte_max) == (34457, 103730, 45779) and round(103730 / 34457, 1) == 3.0
    assert (ohne.lesezugriffe_summe, k500.lesezugriffe_summe, k2000.lesezugriffe_summe) == (332517480, 80263971, 102999066)
    assert (_pct(k500.lesezugriffe_summe, ohne.lesezugriffe_summe), _pct(k2000.lesezugriffe_summe, ohne.lesezugriffe_summe)) == (76, 69)
    assert (ohne.lebend_median, k500.lebend_median, k2000.lebend_median) == (7252.5, 769.5, 2923.5)
    assert (_pct(k500.lebend_median, ohne.lebend_median), _pct(k2000.lebend_median, ohne.lebend_median)) == (89, 60)
    assert (ohne.abbrueche, k500.abbrueche, k2000.abbrueche) == (0, 0, 0)


def test_claim_plan_zahlen_der_vormessung_sind_nicht_im_repo_reproduziert(d):
    """Die Planzahlen (Median 13 234, 205 662 615 Lesezugriffe; Python-`random`-Formeln) gehören zu anderen Formeln; die Wiederholung mit SplitMix64 liefert andere Werte."""
    z = d["vor200"]["zeilen"]
    assert _k(z).konflikte_median != 13234 and _k(z).lesezugriffe_summe != 205662615


# ---------------------------------------------------------------- Texte der App
def test_claim_texte_der_app_nennen_nur_gemessene_zahlen():
    assert C.DEFAULT_N == 120 and C.DEFAULT_SEED == 4004 and "4004" in C.PRESET_HELP["Zufallsformel mittel"] and "4003" in C.PRESET_HELP["Färbung"]
    assert C.PRESETS["Färbung"]["n"] == 200 and C.PRESETS["Färbung"]["seed"] == 4003 and C.PRESETS["Zufallsformel mittel"] == {"abstand": 250} and C.PRESETS["Ohne Löschen (Vergleich)"] == {"abstand": 0}
    assert M.SEED_BASIS == 4000 and C.FORMELN_JE_FAMILIE == 20 and C.REGEL_ABSTAND == 500 and C.LIVE_ABSTAENDE == (250, 500, 1000, None)


def test_claim_live_preset_faerbung_und_zufall():
    """README: Preset „Färbung“ (200 Knoten, Zufalls-Seed 4003) braucht ohne Löschen 1 558 Konflikte."""
    import klo_algorithm as A
    v = A.live_vergleich("faerbung", 200, 4003, 10000, 250)
    assert v.ohne.stat["konflikte"] == 1558 and v.ohne.ergebnis.antwort is False
    z = A.live_vergleich("zufall", 120, 4004, 10000, 250)
    assert z.ohne.stat["konflikte"] == 1650 and z.mit.stat["lebend_gelernt"] < z.ohne.stat["lebend_gelernt"]
