"""Verdikte und Kennzahlen an von Hand gesetzten Zeilen (DEMO-PLAYBOOK §12): jede Schwelle und jede Zahl im Text steht hier. Ein Verdikt ist eine reine Funktion (Art, Text)."""
from fractions import Fraction

import klo_evaluation as E
import klo_scenario as S

BASIS_K = [100, 200, 300]
SEEDS_K = {1: [110, 190, 320], 2: [90, 210, 280], 3: [100, 200, 300], 4: [120, 180, 310], 5: [95, 205, 295]}


def Z(f, abstand, konflikte, lesen, lebend, geloescht=0, regel="lbd", seed=None, antwort="sat"):
    return {"formel": f, "abstand": abstand, "regel": regel if abstand is not None else "lbd", "loeser_seed": seed, "antwort": antwort,
            "konflikte": konflikte, "lesezugriffe": lesen, "lebend": lebend, "gelernt": lebend, "geloescht": geloescht}


def reihe(abstand, konflikte, lesen, lebend, geloescht, regel="lbd", antwort="sat"):
    return [Z(i, abstand, konflikte[i], lesen[i], lebend[i], geloescht[i], regel, None, antwort) for i in range(3)]


def zeilen():
    z = reihe(None, BASIS_K, [1000, 2000, 3000], [90, 190, 290], [0, 0, 0])
    for s, ks in SEEDS_K.items():
        z += [Z(i, None, ks[i], 1000 * (i + 1), 90 + 100 * i, 0, "lbd", s) for i in range(3)]
    z += reihe(250, [100, 190, 250], [1000, 1200, 1500], [90, 60, 80], [0, 1, 2])
    z += reihe(500, [100, 400, 900], [900, 1500, 2000], [90, 100, 120], [0, 2, 3])
    z += reihe(1000, BASIS_K, [1000, 2000, 3000], [90, 190, 290], [0, 0, 0])
    return z


# ---------------------------------------------------------------- Kennzahlen
def test_kennzahlen_median_perzentil_und_zaehlung():
    k = E.kennzahlen(E.waehle(zeilen(), 250))
    assert (k.formeln, k.konflikte_median, k.konflikte_max, k.lesezugriffe_median, k.lesezugriffe_summe, k.lebend_median, k.mit_loeschen) == (3, 190, 250, 1200, 3700, 80, 2)
    assert k.konflikte_p90 == 250                                   # Rang min(2, ⌊0,9 · 3⌋ = 2) der sortierten Liste [100, 190, 250]
    assert E.perzentil(list(range(1, 11)), 0.9) == 10 and E.perzentil(list(range(1, 11)), 0.5) == 6      # Rang-Perzentil wie in der Vormessung
    k2 = E.kennzahlen([Z(0, None, 10, 5, 5), Z(1, None, 20, 5, 5, antwort="abbruch")])
    assert k2.konflikte_median == 15 and k2.abbrueche == 1


def test_streuung_band_und_faktor():
    s = E.streuung(zeilen())
    assert s.mediane == (200, 190, 210, 200, 180, 205) and (s.untere, s.obere) == (180, 210)
    assert round(s.faktor_median, 4) == round(210 / 180, 4)         # Faktoren je Formel: 120/90, 210/180, 320/280; der Median ist der mittlere
    assert E.streuung([z for z in zeilen() if z["loeser_seed"] is None]) is None


def test_aenderung_und_paarvergleich():
    assert E.aenderung(1200, 2000) == -40 and E.aenderung(5, 0) is None
    p = E.paarvergleich(zeilen(), 250)
    # Formel 0 hat nie gelöscht (zählt nicht); Formel 1: 190 gegen 200 Konflikte, Formel 2: 250 gegen 300, beide mit weniger Lesezugriffen
    assert p == {"aktiv": 2, "formeln": 3, "weniger_konflikte": 2, "gleich_konflikte": 0, "mehr_konflikte": 0, "weniger_lesezugriffe": 2}
    q = E.paarvergleich(zeilen(), 500)
    assert q["mehr_konflikte"] == 2 and q["weniger_konflikte"] == 0 and q["weniger_lesezugriffe"] == 2      # 400 gegen 200, 900 gegen 300


# ---------------------------------------------------------------- Verdikt Experiment 3
def test_verdikt_loeschen_innerhalb_der_streubreite():
    art, text = E.verdict_loeschen(zeilen(), 250)
    assert art == "success"
    assert "Löschen alle 250 Konflikte (Anteil 1/2, LBD-Grenze 2, Regel LBD), 3 Formeln, in 2 davon fiel mindestens eine Klausel" in text
    assert "Median der Lesezugriffe 1 200 statt 2 000 (40 % weniger, Basis ohne Löschen)" in text
    assert "Median der lebenden gelernten Klauseln 80 statt 190 (58 % weniger)" in text      # 100 · (80 − 190) / 190 = −57,9
    assert "Median der Konflikte 190 statt 200 (5 % weniger)" in text
    assert "innerhalb der Streubreite der Suche (Mediane von sechs Läufen ohne Löschen: 180 bis 210): in den Konflikten ist kein Unterschied erkennbar" in text
    assert "um den Faktor 1,17 (größte gegen kleinste Konfliktzahl)" in text
    assert "Summe der Lesezugriffe über die 3 Formeln: 3 700 statt 6 000 (38 % weniger)" in text                  # 100 · (3 700 − 6 000) / 6 000 = −38,3
    assert ("In den 2 Formeln mit Löschrunde brauchte der Lauf mit Löschen in 2 weniger, in 0 gleich viele und in 0 mehr Konflikte "
            "als der Lauf ohne Löschen und in 2 weniger Lesezugriffe (je Formel ein Lauf, ohne Streubreite).") in text


def test_verdikt_loeschen_ueber_der_streubreite_ist_eine_warnung():
    art, text = E.verdict_loeschen(zeilen(), 500)
    assert art == "warning" and "Median der Konflikte 400 statt 200 (100 % mehr)" in text and "liegt über der Streubreite der Suche" in text
    assert "Median der Lesezugriffe 1 500 statt 2 000 (25 % weniger" in text


def test_verdikt_loeschen_ohne_gefallene_klausel_und_ohne_abstand():
    art, text = E.verdict_loeschen(zeilen(), 1000)
    assert art == "info" and text == "Bei Löschen alle 1 000 Konflikte fiel in keiner der 3 Formeln eine Klausel: alle Läufe sind gleich dem Lauf ohne Löschen."
    art, text = E.verdict_loeschen(zeilen(), 0)
    assert art == "info" and "Ohne Löschen ist der Vergleichslauf selbst" in text


def test_verdikt_loeschen_unter_der_streubreite_und_ohne_referenzlaeufe_und_abbrueche():
    z = zeilen()
    unten = reihe(2000, [100, 120, 150], [900, 1000, 1100], [50, 60, 70], [0, 1, 1])
    art, text = E.verdict_loeschen(z + unten, 2000)
    assert art == "success" and "liegt unter der Streubreite der Suche" in text and "kein Unterschied" not in text
    ohne_ref = [x for x in z if x["loeser_seed"] is None]
    art, text = E.verdict_loeschen(ohne_ref, 250)
    assert "Die Streubreite der Suche ist in dieser Messung nicht enthalten" in text and "innerhalb" not in text
    mit_abbruch = [dict(x, antwort="abbruch") if (x["abstand"] == 250 and x["formel"] == 2) else x for x in z]
    assert "Abbrüche am Konfliktbudget: 0 ohne Löschen, 1 mit Löschen" in E.verdict_loeschen(mit_abbruch, 250)[1]


def test_verdikt_loeschen_nennt_geaenderte_regel():
    z = zeilen() + reihe(250, [100, 190, 250], [1000, 1200, 1500], [90, 60, 80], [0, 1, 2], regel="laenge")
    z = [x for x in z if not (x["abstand"] == 250 and x["regel"] == "lbd")]
    art, text = E.verdict_loeschen(z, 250, "laenge", 75, 3)
    assert "(Anteil 3/4, LBD-Grenze 3, Regel Länge)" in text


# ---------------------------------------------------------------- Verdikt Experiment 4
def test_verdikt_regeln_alle_im_band_und_eine_ausserhalb():
    z = zeilen()
    z = [x for x in z if x["abstand"] != 500]
    z += reihe(500, [100, 190, 250], [900, 1500, 2000], [90, 100, 120], [0, 2, 3], "lbd")
    z += reihe(500, [100, 200, 300], [1000, 1900, 2800], [90, 150, 200], [0, 2, 3], "laenge")
    z += reihe(500, [100, 205, 310], [950, 1700, 2500], [90, 120, 150], [0, 2, 3], "zufall")
    art, text = E.verdict_regeln(z)
    assert art == "info" and "LBD: Konflikte 190, Lesezugriffe 1 500, lebend 100; Länge: Konflikte 200, Lesezugriffe 1 900, lebend 150; zufällig: Konflikte 205, Lesezugriffe 1 700, lebend 120" in text
    assert "Mediane über 3 Formeln bei Löschen alle 500 Konflikte" in text
    assert "Die Konflikte aller drei Regeln liegen innerhalb der Streubreite der Suche (180 bis 210" in text and "in den Konflikten fällt die Rangordnung nicht auseinander" in text
    z = [x for x in z if not (x["abstand"] == 500 and x["regel"] == "zufall")] + reihe(500, [100, 400, 900], [950, 1700, 2500], [90, 120, 150], [0, 2, 3], "zufall")
    art, text = E.verdict_regeln(z)
    assert art == "warning" and "Außerhalb der Streubreite der Suche (180 bis 210) liegt die Regel zufällig." in text
    z = [x for x in z if not (x["abstand"] == 500 and x["regel"] == "laenge")] + reihe(500, [100, 300, 400], [1000, 1900, 2800], [90, 150, 200], [0, 2, 3], "laenge")
    art, text = E.verdict_regeln(z)
    assert "Außerhalb der Streubreite der Suche (180 bis 210) liegen die Regeln Länge, zufällig." in text


# ---------------------------------------------------------------- Verdikt Handtabelle und Formate
def test_verdikt_hand_handbeispiel_und_anteil_text():
    h = S.hand_runde()
    art, text = E.verdict_hand(h, Fraction(1, 2), 2)
    assert art == "success" and text == "4 Kandidaten; ⌊1/2 · 4⌋ = 2 fallen: Klauseln 8, 5. Von 8 gelernten Klauseln bleiben 6."
    assert E.anteil_text(Fraction(3, 4)) == "3/4" and E.anteil_text(Fraction(25, 100)) == "1/4"


def test_formate():
    assert E.zahl(13234) == "13 234" and E.zahl(9341.5) == "9 341,5" and E.zahl(4.0) == "4"
    assert E.dezimal(1.1667, 2) == "1,17" and E.abstand_text(None) == "nie" and E.abstand_text(0) == "nie" and E.abstand_text(2000) == "alle 2 000 Konflikte"
    assert E.regel_text(25, 1, "zufall") == "Anteil 1/4, LBD-Grenze 1, Regel zufällig"
