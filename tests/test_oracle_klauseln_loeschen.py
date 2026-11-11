"""Orakel-Tests (DEMO-PLAYBOOK §12): jede Kernroutine gegen einen anderen Rechenweg.

1. LBD gegen die Definition „Zahl verschiedener Stufen“ (Neuimplementierung mit Schleifen) an 200 zufälligen Klauseln mit Stufen.
2. Die Löschrunde gegen eine Referenz ohne `sorted` (Paarvergleich wie im Handbeispiel) an 200 zufälligen Tabellen, alle drei Regeln außer „zufall“.
3. Antwort mit und ohne Löschen gegen OR-Tools CP-SAT und Modellprüfung (kleine Fassung; im Scratch-Lauf der Bauphase an mehr als 200 Formeln).
4. Der Beweis eines Laufs mit Löschzeilen wird von einem unabhängigen, einfachen RUP-Prüfer (Zählen statt Beobachten, nur in diesem Test) akzeptiert.
5. Der Bestandszähler `lebend_gelernt` gegen ein Nachzählen am Löser."""
import pytest

import klo_instanzen as I
import klo_loeschen as L
from klo_rng import SplitMix64

cp_model = pytest.importorskip("ortools.sat.python.cp_model")


# ---------------------------------------------------------------- 1. LBD gegen die Definition
def test_lbd_gegen_definition_an_200_zufallsklauseln():
    rng = SplitMix64(11)
    for _ in range(200):
        stufen = {v: 1 + rng.below(8) for v in range(1, 31)}
        klausel = rng.sample(range(1, 31), 2 + rng.below(9))
        verschieden = []
        for v in klausel:
            if stufen[v] not in verschieden:
                verschieden.append(stufen[v])
        assert L.lbd(stufen[v] for v in klausel) == len(verschieden)


# ---------------------------------------------------------------- 2. Löschrunde gegen Paarvergleich
def _referenz(lbd_v, laenge, gesperrt, anteil_zaehler, anteil_nenner, grenze, regel):
    """Ohne `sorted`: Kandidaten sammeln, dann wiederholt den schlechtesten per Paarvergleich herausnehmen; fallen die ersten ⌊a · k⌋."""
    kand = [i for i in range(len(lbd_v)) if lbd_v[i] > grenze and i not in gesperrt]

    def vor(a, b):                       # fällt a vor b?
        ka = (lbd_v[a], laenge[a]) if regel == "lbd" else (laenge[a], lbd_v[a])
        kb = (lbd_v[b], laenge[b]) if regel == "lbd" else (laenge[b], lbd_v[b])
        if ka != kb:
            return ka > kb
        return a < b

    reihenfolge, rest = [], list(kand)
    while rest:
        erster = rest[0]
        for c in rest[1:]:
            if vor(c, erster):
                erster = c
        reihenfolge.append(erster)
        rest.remove(erster)
    zahl = (anteil_zaehler * len(kand)) // anteil_nenner
    return reihenfolge[:zahl]


def test_loeschrunde_gegen_paarvergleich_an_200_tabellen():
    rng = SplitMix64(5)
    from fractions import Fraction
    for _ in range(200):
        k = 1 + rng.below(25)
        lbd_v = [1 + rng.below(7) for _ in range(k)]
        laenge = [lbd_v[i] + rng.below(6) for i in range(k)]      # Länge ≥ LBD, viele Gleichstände
        gesperrt = {i for i in range(k) if rng.below(5) == 0}
        zaehler = 1 + rng.below(3)
        regel = "lbd" if rng.coin() else "laenge"
        grenze = 1 + rng.below(3)
        mein = L.waehle_loeschkandidaten(lbd_v, laenge, gesperrt, Fraction(zaehler, 4), grenze, regel)
        assert mein == _referenz(lbd_v, laenge, gesperrt, zaehler, 4, grenze, regel)


# ---------------------------------------------------------------- 3. Antwort gegen CP-SAT
def _cpsat(n, klauseln):
    m = cp_model.CpModel()
    x = [None] + [m.NewBoolVar(f"x{i}") for i in range(1, n + 1)]
    for c in klauseln:
        m.AddBoolOr([x[l] if l > 0 else x[-l].Not() for l in c])
    s = cp_model.CpSolver()
    s.parameters.num_workers = 1
    s.parameters.max_time_in_seconds = 60
    return {cp_model.OPTIMAL: True, cp_model.INFEASIBLE: False}[s.Solve(m)]


def _aufgaben():
    for seed in range(8):
        n = 40 + 5 * (seed % 4)
        yield f"zufall{seed}", I.rand3(n, round(4.26 * n), 300 + seed)
    yield "faerbung0", I.flat_graph(60, 4.7, 7, 3)
    yield "faerbung1", I.flat_graph(70, 4.7, 8, 3)
    yield "schubfach5", I.pigeonhole(5)


@pytest.mark.parametrize("name,inst", list(_aufgaben()))
def test_antwort_mit_und_ohne_loeschen_gleich_cpsat(name, inst):
    referenz = _cpsat(inst.n, inst.klauseln)
    for abstand in (None, 20, 50):
        for regel in L.REGELN:
            r = L.lauf(inst.n, inst.klauseln, abstand=abstand, regel=regel, budget=200000)
            assert r.ergebnis.antwort is referenz, (name, abstand, regel)
            if referenz:
                assert I.pruefe_modell(inst.klauseln, r.ergebnis.modell), (name, abstand, regel)


# ---------------------------------------------------------------- 4. Beweis mit Löschzeilen gegen einen einfachen RUP-Prüfer
def _unit_konflikt(klauseln, annahmen):
    """Einheitspropagation durch wiederholtes Durchlesen aller Klauseln; True, wenn ein Konflikt entsteht (Zählen statt Beobachten)."""
    wert = {}
    for a in annahmen:
        if wert.get(abs(a), a > 0) != (a > 0):
            return True
        wert[abs(a)] = a > 0
    geaendert = True
    while geaendert:
        geaendert = False
        for c in klauseln:
            offen, erfuellt = [], False
            for l in c:
                w = wert.get(abs(l))
                if w is None:
                    offen.append(l)
                elif w == (l > 0):
                    erfuellt = True
                    break
            if erfuellt:
                continue
            if not offen:
                return True
            if len(offen) == 1:
                wert[abs(offen[0])] = offen[0] > 0
                geaendert = True
    return False


def _pruefe_drup(formel, beweis):
    """DRUP: jede hinzugefügte Klausel muss durch Einheitspropagation aus ihrer Verneinung widerlegbar sein; Löschzeilen entfernen eine Klausel (als Menge)."""
    db = [frozenset(c) for c in formel]
    abgeleitet = geloescht = 0
    for art, klausel in beweis:
        k = frozenset(klausel)
        if art == "a":
            if not _unit_konflikt(db, [-l for l in k]):
                return False, abgeleitet, geloescht
            db.append(k)
            abgeleitet += 1
        else:
            assert k in db, "gelöschte Klausel ist nicht in der Datenbank"
            db.remove(k)
            geloescht += 1
    return _unit_konflikt(db, []), abgeleitet, geloescht


def test_beweis_mit_loeschzeilen_wird_vom_unabhaengigen_pruefer_akzeptiert():
    gefunden = 0
    for seed in range(40):
        inst = I.rand3(40, 182, 900 + seed)
        r = L.lauf(inst.n, inst.klauseln, abstand=15, proof=True, budget=20000)
        if r.ergebnis.antwort is not False:
            continue
        ok, abgeleitet, geloescht = _pruefe_drup(inst.klauseln, r.ergebnis.beweis)
        assert ok, f"Beweis abgelehnt bei Seed {900 + seed}"
        if geloescht:
            gefunden += 1
        assert geloescht == r.stat["geloescht"]
    assert gefunden >= 3, "zu wenige unerfüllbare Formeln mit Löschzeilen: der Test prüft nichts"


def test_pruefer_lehnt_nicht_gefolgerte_klauseln_ab():
    """Solidität an erfüllbaren Formeln: eine Klausel, die das Modell verletzt, folgt nicht aus der Formel und darf nicht als RUP durchgehen."""
    rng = SplitMix64(17)
    geprueft = 0
    for seed in range(10):
        inst = I.rand3(30, 100, 500 + seed)
        r = L.lauf(inst.n, inst.klauseln, budget=50000)
        assert r.ergebnis.antwort is True
        modell = r.ergebnis.modell
        db = [frozenset(c) for c in inst.klauseln]
        for _ in range(10):
            variablen = rng.sample(range(1, 31), 3 + rng.below(4))
            verletzt = [(-v if modell[v] else v) for v in variablen]          # jedes Literal ist unter dem Modell falsch
            assert not _unit_konflikt(db, [-l for l in verletzt])
            geprueft += 1
    assert geprueft == 100


# ---------------------------------------------------------------- 5. Bestandszähler
def test_bestandszaehler_gegen_nachzaehlen():
    for seed in range(6):
        inst = I.rand3(80, 341, 70 + seed)
        for abstand in (None, 30):
            lo = L.LoeschLoeser(inst.n, inst.klauseln, delete=abstand is not None, delete_every=abstand or 1)
            erg = lo.loese()
            nachgezaehlt = sum(1 for i in range(len(lo.klauseln)) if lo.ist_gelernt[i] and not lo.geloescht[i])
            assert erg.stat["lebend_gelernt"] == nachgezaehlt
            assert erg.stat["gelernt"] - erg.stat["geloescht"] >= nachgezaehlt        # Einheitsklauseln sind mitgezählt, aber nicht gespeichert
