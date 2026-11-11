"""AppTest: Inhalte der Reiter an den Presets (Verdikt-Zeilen, Handtabelle, Knopf der Messreihe, Familienwechsel)."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texte(at) -> str:
    teile = [m.value for m in at.markdown] + [s.value for s in at.success] + [i.value for i in at.info] + [w.value for w in at.warning] + [e.value for e in at.error]
    return "\n".join(teile)


def test_standard_zeigt_kernfrage_handtabelle_und_live_verdikt():
    text = _texte(_app())
    assert "Löschen alle 500 Konflikte (Anteil 1/2, LBD-Grenze 2, Regel LBD), 20 Formeln, in 19 davon fiel mindestens eine Klausel" in text    # Kernfrage, Zufalls-3-SAT
    assert "4 Kandidaten; ⌊1/2 · 4⌋ = 2 fallen: Klauseln 8, 5. Von 8 gelernten Klauseln bleiben 6." in text                                       # Reiter 1
    assert "Konflikte bis zur Antwort:" in text and "lebende gelernte Klauseln" in text                                                         # Reiter 2
    assert "Mediane über 20 Formeln bei Löschen alle 500 Konflikte" in text                                                                     # Reiter 4


def test_handtabelle_aendert_sich_mit_sperre_anteil_und_grenze():
    at = _app()
    at.multiselect(key="gesperrt_multi").set_value([]).run()
    assert not at.exception and "6 Kandidaten; ⌊1/2 · 6⌋ = 3 fallen: Klauseln 8, 5, 6." in _texte(at)
    at.multiselect(key="gesperrt_multi").set_value([2, 3, 5, 6, 7]).run()
    assert not at.exception and "1 Kandidat, aber ⌊1/2 · 1⌋ = 0: abgerundet fällt keine Klausel, alle 8 bleiben." in _texte(at)
    at.multiselect(key="gesperrt_multi").set_value([1, 2, 3, 4, 5, 6, 7, 8]).run()
    assert not at.exception and "Keine Klausel ist Kandidat" in _texte(at)


def test_preset_ohne_loeschen_zeigt_zwei_gleiche_laeufe():
    at = _app()
    at.sidebar.button(key="preset_Ohne Löschen (Vergleich)").click().run()
    assert not at.exception
    assert "Ohne Löschen bleiben alle gelernten Klauseln" in _texte(at)


def test_preset_zufallsformel_zeigt_saegezahn_verdikt():
    at = _app()
    at.sidebar.button(key="preset_Zufallsformel mittel").click().run()
    assert not at.exception
    assert "Mit Löschen alle 250 Konflikte:" in _texte(at) and "Basis ohne Löschen" in _texte(at)


def test_preset_faerbung_wechselt_die_eingefrorene_messung():
    at = _app()
    at.sidebar.button(key="preset_Färbung").click().run()
    assert not at.exception
    text = _texte(at)
    assert "3-Färbung (mittlerer Grad 4,5), n = 300" in " ".join(c.value for c in at.caption)
    assert "Summe der Lesezugriffe über die 20 Formeln: 57 542 590 statt 164 589 374" in text


def test_messreihe_auf_knopfdruck_startet_erst_auf_knopfdruck():
    at = _app()
    assert "noch nichts gerechnet" in _texte(at)
    at.slider(key="live_f_slider").set_value(4).run()
    at.slider(key="live_n_slider").set_value(60).run()
    at.button(key="live_rechnen").click().run()
    assert not at.exception
    text = _texte(at)
    assert "noch nichts gerechnet" not in text.split("Messreihe auf Knopfdruck")[-1] and "4 Formeln" in text


def test_regelwechsel_in_der_seitenleiste_aendert_die_handtabelle():
    at = _app()
    at.select_slider(key="anteil_select").set_value(75).run()
    assert not at.exception and "⌊3/4 · 4⌋ = 3 fallen: Klauseln 8, 5, 6." in _texte(at)
    at.slider(key="grenze_slider").set_value(3).run()
    assert not at.exception and "3 Kandidaten; ⌊3/4 · 3⌋ = 2 fallen: Klauseln 8, 5." in _texte(at)
