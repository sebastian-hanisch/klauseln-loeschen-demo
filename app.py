"""Klauseln löschen – Gedächtnis kostet Zugriffe - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Ein CDCL-Löser lernt aus jedem Konflikt eine Klausel; die Demo zeigt, was das Gedächtnis kostet (Lesezugriffe), was Löschen spart und was es an Information kostet.
Aufwand wird in Konflikten, Klauseln und Lesezugriffen gezählt, nie in Sekunden.

Lauffähig mit: streamlit run app.py
"""

from fractions import Fraction

import pandas as pd
import streamlit as st

import klo_algorithm as A
import klo_constants as C
import klo_evaluation as E
import klo_messung as M
import klo_scenario as S
import klo_visualization as V
from klo_layout import dunkles_design, kopf_css
from klo_presets import (
    SETTING_SPECS,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)

st.set_page_config(page_title="Klauseln löschen – Sebastian Hanisch", layout="wide")

ANTEIL_ZEICHEN = {25: "¼", 50: "½", 75: "¾"}


@st.cache_data(show_spinner=False)
def _messung():
    return M.lade_messung()


@st.cache_data(show_spinner=False)
def _live(familie, n, seed, budget, abstand, anteil_prozent, grenze, regel):
    return A.live_vergleich(familie, n, seed, budget, abstand or None, Fraction(anteil_prozent, 100), grenze, regel)


@st.cache_data(show_spinner=False)
def _live_messreihe(familie, n, formeln, budget, anteil_prozent, grenze, regel):
    return M.messreihe(familie, n, range(formeln), C.LIVE_ABSTAENDE, budget, E.REFERENZ_SEEDS, haupt_regel=regel, anteil=Fraction(anteil_prozent, 100), grenze=grenze)


def _tabelle(daten, spalten):
    st.dataframe(pd.DataFrame(daten, columns=spalten), hide_index=True, width="stretch")


def _delta(mein, referenz):
    """Delta „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (weniger ist besser), bei Gleichstand grau ohne Pfeil."""
    if mein == referenz:
        return dict(delta="gleich", delta_color="off")
    unterschied = mein - referenz
    return dict(delta=f"{'+' if unterschied > 0 else '-'}{E.zahl(abs(unterschied))}", delta_color="inverse")


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in klo_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🗑️ Klauseln löschen – Gedächtnis kostet Zugriffe")
st.markdown(
    """
**Ein Löser, der aus jedem Konflikt lernt, ertrinkt irgendwann in den eigenen Klauseln:** jede gelernte Klausel kann bei einer Propagation besucht werden, sobald eines ihrer beiden beobachteten Literale falsch wird, auch wenn sie nie wieder gebraucht wird; je größer der Bestand, desto mehr Besuche und gelesene Literale.
Löschen der schlechteren Hälfte verkleinert den Bestand und senkt die Lesezugriffe (Zufalls-3-SAT n = 175: 56 bis 92 % weniger lebende Klauseln, 38 bis 54 % weniger Lesezugriffe), kann aber Information kosten: eine gelöschte Klausel kann der Löser ein zweites Mal lernen (gezählt wird das nicht).
Die Demo zeigt eine **Löschrunde von Hand** (Handtabelle), den **Bestand über die Konflikte** an einer Aufgabe, eine **Messreihe über Löschabstände** an je 20 Formeln und den Vergleich dreier **Löschregeln**.
Aufwand wird in **Konflikten, Klauseln und Lesezugriffen** gezählt, nie in Sekunden.

Weiter unten: vier Experimente (Reiter), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert das Löschen gelernter Klauseln", expanded=True):
    st.markdown(
        """
Nach jedem Konflikt lernt der Löser eine **Klausel**. Alle `Abstand` Konflikte hält er eine **Löschrunde** ab: Aus den gelernten Klauseln wählt er die **Kandidaten**, ordnet sie nach Güte und löscht die schlechtere Hälfte.

| Begriff | Bedeutung |
|---|---|
| **Entscheidungsstufe** | Nummer der Entscheidung, unter der eine Variable belegt wurde (Stufe 1 = erste Entscheidung). |
| **LBD** (Literal Block Distance) | Zahl der **verschiedenen Entscheidungsstufen** der Variablen einer Klausel. Klein = die Klausel verbindet wenige Entscheidungsblöcke; Glucose (Audemard/Simon 2009) nutzt das als Qualitätsmaß. |
| **gesperrt** | Die Klausel ist gerade **Grund** (Reason) eines Literals auf dem Trail; sie darf nicht fallen, sonst fehlt die Begründung einer Belegung. |
| **Kandidat** | gelernte Klausel, **nicht gesperrt**, mit **LBD über der LBD-Grenze** (Standard 2: Klauseln mit LBD ≤ 2 bleiben immer). Ursprüngliche Klauseln der Aufgabe sind nie Kandidaten. |
| **Löschrunde** | Kandidaten nach (LBD, Länge) absteigend ordnen (bei Gleichstand fällt die **ältere** Klausel zuerst) und die ersten ⌊Anteil · Zahl⌋ löschen (**abgerundet**; Standard Anteil ½). |
| **Lesezugriff** | ein gelesenes Literal bei der Propagation; die Zählgröße dieser Demo (keine Laufzeit, keine Byte). |
| **lebende gelernte Klauseln** | gelernte Klauseln der Länge ≥ 2, die nicht gelöscht sind (gelernte Einheitsklauseln werden nicht als Klausel gespeichert, sie belegen eine Variable auf Stufe 0). |
        """
    )

load_permalink_settings()
init_session_state_defaults()
st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Aufgabe (Live-Läufe)**")
    familie = st.selectbox("Familie", C.FAMILIEN, format_func=C.FAMILIEN_NAMEN.get, key="familie_select",
                           help="Gilt für den Live-Lauf, die Messreihe auf Knopfdruck und für die Wahl der eingefrorenen Messung (Zufall: n = 175 Variablen, Färbung: 300 Knoten).")
    n = st.slider("Größe n", *bounds("n_slider"), key="n_slider",
                  help="Variablen (Zufalls-3-SAT, m = ⌊4,26 · n⌉ Klauseln) beziehungsweise Knoten (3-Färbung, mittlerer Grad 4,5; 3n Variablen). Gilt für den Live-Lauf.")
    seed = st.number_input("Zufalls-Seed der Aufgabe", *bounds("seed_input"), key="seed_input", step=1,
                           help="Bestimmt die Aufgabe (SplitMix64-Erzeuger) und die Zufallsregel der Handtabelle.")
    st.button("🎲 Neuer Zufalls-Seed", width="stretch", on_click=randomize_seed)
    budget = st.select_slider("Konfliktbudget des Live-Laufs", options=C.BUDGET_OPTIONEN, key="budget_select",
                              help="Nach so vielen Konflikten bricht ein Lauf ab; sein Ergebnis heißt dann „Budget erreicht“ und seine Zahlen sind Untergrenzen.")
    st.markdown("**Löschregel**")
    abstand = st.selectbox("Löschabstand", C.ABSTAND_OPTIONEN, format_func=lambda a: "nie" if not a else f"alle {a} Konflikte", key="abstand_select",
                           help="Alle so viele Konflikte hält der Löser eine Löschrunde ab; „nie“ ist der Lauf ohne Löschen. Gilt für Live-Lauf und Messreihe auf Knopfdruck, die eingefrorene Messung zeigt alle Abstände.")
    anteil = st.select_slider("Anteil der Kandidaten, der fällt", options=C.ANTEIL_OPTIONEN, format_func=ANTEIL_ZEICHEN.get, key="anteil_select",
                              help="Die ersten ⌊Anteil · Zahl der Kandidaten⌋ der Rangfolge fallen. Gilt für Handtabelle, Live-Lauf und Messreihe auf Knopfdruck; die eingefrorene Messung gilt für ½.")
    grenze = st.slider("LBD-Grenze", *bounds("grenze_slider"), key="grenze_slider",
                       help="Klauseln mit LBD höchstens so groß bleiben immer. Gilt wie der Anteil; die eingefrorene Messung gilt für Grenze 2.")
    regel = st.selectbox("Rangordnung der Kandidaten", C.REGELN, format_func=C.REGEL_NAMEN.get, key="regel_select",
                         help="Welche Kandidaten zuerst fallen. Gilt wie der Anteil; Experiment 4 vergleicht alle drei an der eingefrorenen Messung.")

anteil_bruch = Fraction(anteil, 100)
messung = _messung()
fam = messung[familie]
zeilen = fam["zeilen"]
fam_n = fam["parameter"]["n"]

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Was spart das Löschen, und was kostet es?")
st.caption(f"Eingefrorene Messung (`klo_messung.json`, vorgerechnet, nicht live): {M.FAMILIEN_NAMEN[familie]}, n = {fam_n}, {C.FORMELN_JE_FAMILIE} Formeln, "
           f"Löschen alle {C.REGEL_ABSTAND} Konflikte (Anteil ½, LBD-Grenze 2, Regel LBD), Median über die Formeln; der Pfeil ist die Differenz zum Lauf ohne Löschen.")
ohne_k, mit_k = E.kennzahlen(E.waehle(zeilen)), E.kennzahlen(E.waehle(zeilen, C.REGEL_ABSTAND))
c1, c2, c3 = st.columns(3)
c1.metric("lebende gelernte Klauseln (Median)", E.zahl(mit_k.lebend_median), **_delta(mit_k.lebend_median, ohne_k.lebend_median))
c2.metric("Lesezugriffe (Median)", E.zahl(mit_k.lesezugriffe_median), **_delta(mit_k.lesezugriffe_median, ohne_k.lesezugriffe_median))
c3.metric("Konflikte bis zur Antwort (Median)", E.zahl(mit_k.konflikte_median), **_delta(mit_k.konflikte_median, ohne_k.konflikte_median))
kind, text = E.verdict_loeschen(zeilen, C.REGEL_ABSTAND)
getattr(st, kind)(text)

# --- Live-Lauf, immer sichtbar -------------------------------------------------------------------------------------------------------------

st.markdown("## 🧮 Live-Aufgabe")
with st.spinner("Löse die Aufgabe ohne und mit Löschen (bei großen Aufgaben dauert das einige Sekunden) …"):
    live = _live(familie, int(n), int(seed), int(budget), int(abstand), int(anteil), int(grenze), regel)
o, m = live.ohne.stat, live.mit.stat
antwort = {True: "erfüllbar", False: "unerfüllbar", None: "Budget erreicht"}
st.caption(f"{M.FAMILIEN_NAMEN[familie]}, n = {live.n} (Zufalls-Seed {int(seed)}), {live.klauseln} Klauseln; Löschen {E.abstand_text(abstand)} ({E.regel_text(int(anteil), int(grenze), regel)}); Zahlen des Laufs mit Löschen; der Pfeil darunter ist die Differenz zum Lauf ohne Löschen.")
a1, a2, a3, a4, a5, a6 = st.columns([1.7, 1, 1, 1.1, 1, 1.3])
a1.metric("Antwort", antwort[live.mit.ergebnis.antwort])
a2.metric("Konflikte", E.zahl(m["konflikte"]), **_delta(m["konflikte"], o["konflikte"]))
a3.metric("gelernte Klauseln", E.zahl(m["gelernt"]))
a4.metric("lebende gelernte", E.zahl(m["lebend_gelernt"]), **_delta(m["lebend_gelernt"], o["lebend_gelernt"]))
a5.metric("gelöschte", E.zahl(m["geloescht"]))
a6.metric("Lesezugriffe", E.zahl(m["lesezugriffe"]), **_delta(m["lesezugriffe"], o["lesezugriffe"]))

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["🔬 Eine Löschrunde von Hand", "🔬 Bestand über die Konflikte", "🔬 Löschrate gegen Konflikte und Zugriffe", "🔬 Welche Regel löscht gut?"])

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

with tab1:
    st.subheader("🔬 Eine Löschrunde von Hand: die Handtabelle")
    st.caption("Zwölf Variablen auf sechs Entscheidungsstufen, acht gelernte Klauseln. Anteil, LBD-Grenze und Rangordnung stehen in der Seitenleiste; hier wird gewählt, welche Klauseln gerade Grund eines Trail-Literals (gesperrt) sind.")
    gesperrt = st.multiselect("Gesperrte Klauseln (Grund eines Trail-Literals)", C.GESPERRT_OPTIONEN, key="gesperrt_multi",
                              help="Gesperrte Klauseln dürfen nicht fallen. Im Handbeispiel sind es die Klauseln 3 und 7.")
    h = S.hand_runde(gesperrt, anteil_bruch, int(grenze), regel, int(seed))
    kind, text = E.verdict_hand(h, anteil_bruch, int(grenze))
    getattr(st, kind)(text)
    zeilen_h = []
    for nr in sorted(S.HAND_KLAUSELN):
        vs = S.HAND_KLAUSELN[nr]
        status = V.klausel_status(nr, h, gesperrt, int(grenze))
        zeilen_h.append([nr, " ".join(f"x{v}" for v in vs), "{" + ", ".join(str(s) for s in sorted({S.HAND_STUFEN[v] for v in vs})) + "}", h.lbd[nr], h.laenge[nr],
                         "ja" if nr in gesperrt else "nein", "ja" if nr in h.kandidaten else "nein", str(h.rangfolge.index(nr) + 1) if nr in h.rangfolge else "–",
                         V.STATUS_TEXT[status]])
    links, rechts = st.columns([3, 2])
    with links:
        _tabelle(zeilen_h, ["Nr", "Variablen", "Stufen", "LBD", "Länge", "gesperrt", "Kandidat", "Rang", "Schicksal"])
    with rechts:
        st.plotly_chart(V.build_hand(h, gesperrt, int(grenze)), width="stretch", key="hand_chart")
    st.markdown(
        f"**Rechnung.** Kandidaten: {h.kandidaten or 'keine'}. Rangfolge (schlechteste zuerst): {h.rangfolge or 'leer'}. Es fallen die ersten ⌊{E.anteil_text(anteil_bruch)} · {len(h.kandidaten)}⌋ = {len(h.faellt)}: "
        f"{h.faellt or 'keine'}. Es bleiben {h.bleibt}."
    )
    st.caption("Stufen der Variablen: x1, x2 auf Stufe 1; x3, x4 auf 2; x5, x6, x7 auf 3; x8, x9 auf 4; x10, x11 auf 5; x12 auf 6. Bei Gleichstand in (LBD, Länge) fällt die ältere Klausel (kleinere Nummer) zuerst; "
               "die Zufallsregel mischt die Kandidaten mit dem SplitMix64 des Zufalls-Seeds. Die Tabelle ist von Hand gesetzt und in tests/test_algorithm.py nachgerechnet.")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

with tab2:
    st.subheader("🔬 Bestand über die Konflikte: der Sägezahn")
    st.caption("Dieselbe Aufgabe zweimal gelöst: ohne Löschen wächst der Bestand mit jeder gelernten Klausel der Länge ≥ 2, mit Löschen fällt er in jeder Löschrunde um die gefallenen Klauseln (Sägezahn). "
               "Aufgabe, Löschabstand und Regel stehen in der Seitenleiste.")
    kind, text = E.verdict_bestand(live)
    getattr(st, kind)(text)
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(V.build_bestand(live), width="stretch", key="bestand_chart")
    with col_b:
        st.plotly_chart(V.build_lesen(live), width="stretch", key="lesen_chart")
    st.caption(f"Der Verlauf ist alle {A.abtastabstand(int(budget))} Konflikte abgetastet. Lesezugriffe sind gelesene Literale bei der Propagation (Zählgröße dieses Lösers, keine Laufzeit). "
               "Gelernte Einheitsklauseln stehen nicht im Bestand.")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

with tab3:
    st.subheader("🔬 Löschrate gegen Konflikte und Zugriffe")
    st.caption(f"Eingefrorene Messung (vorgerechnet mit `tools/messung_klo.py`, nicht live): {M.FAMILIEN_NAMEN[familie]}, n = {fam_n}, {C.FORMELN_JE_FAMILIE} Formeln "
               f"(Zufalls-Seeds {M.SEED_BASIS} bis {M.SEED_BASIS + C.FORMELN_JE_FAMILIE - 1}), Konfliktbudget {E.zahl(fam['parameter']['budget'])}; Anteil ½, LBD-Grenze 2, Regel LBD. "
               "Die Reglereinstellungen der Seitenleiste zu Anteil, Grenze und Rangordnung wirken hier nicht.")
    kind, text = E.verdict_loeschen(zeilen, int(abstand))
    getattr(st, kind)(text)
    tab_rows = []
    for e in E.zusammenfassung_tabelle(zeilen):
        k = e["k"]
        tab_rows.append(["nie" if e["abstand"] is None else str(e["abstand"]), E.zahl(k.konflikte_median), E.zahl(k.konflikte_p90), E.zahl(k.konflikte_max), f"{k.abbrueche} von {k.formeln}",
                         E.zahl(k.lesezugriffe_median), E.zahl(k.lebend_median), f"{k.mit_loeschen} von {k.formeln}"])
    _tabelle(tab_rows, ["Löschabstand", "Konflikte Median", "90-Prozent-Rang", "Maximum", "Abbrüche am Budget", "Lesezugriffe Median", "lebende gelernte Klauseln Median", "Formeln mit Löschrunde"])
    s = E.streuung(zeilen)
    if s is not None:
        st.caption("Streubreite der Suche: Mediane der Konflikte von sechs Läufen ohne Löschen (fester Start und Löser-Seeds 1 bis 5 mit zufälliger Anfangsaktivität): "
                   + ", ".join(E.zahl(x) for x in s.mediane) + ".")
    cx, cy, cz = st.columns(3)
    with cx:
        st.plotly_chart(V.build_konflikte(zeilen), width="stretch", key="konflikte_chart")
    with cy:
        st.plotly_chart(V.build_median_balken(zeilen, "lesezugriffe_median", "Lesezugriffe (Median)"), width="stretch", key="lesen_balken")
    with cz:
        st.plotly_chart(V.build_median_balken(zeilen, "lebend_median", "lebende gelernte Klauseln (Median)"), width="stretch", key="lebend_balken")
    st.caption("Links: je Punkt eine Formel, logarithmische Achse; das blaue Band reicht vom kleinsten bis zum größten Median der sechs Läufe ohne Löschen. Verglichen werden Mediane je Abstand; das Verhältnis der Mediane ist nicht der Median der Verhältnisse.")

    st.markdown("**Messreihe auf Knopfdruck (live, kleiner)**")
    cl1, cl2 = st.columns(2)
    live_n = cl1.slider("Größe n der Messreihe", *bounds("live_n_slider"), key="live_n_slider", help="Variablen beziehungsweise Knoten; kleiner als die eingefrorene Messung, damit sie in der App rechenbar bleibt.")
    live_f = cl2.slider("Formeln der Messreihe", *bounds("live_f_slider"), key="live_f_slider", help="Je Formel werden vier Abstände und fünf Läufe ohne Löschen mit anderen Löser-Seeds gerechnet.")
    schluessel = (familie, int(live_n), int(live_f), int(anteil), int(grenze), regel)
    if st.button("▶ Messreihe rechnen", key="live_rechnen"):
        with st.spinner(f"Rechne {live_f} Formeln mit n = {live_n}, je Formel neun Läufe; das kann einige Sekunden bis Minuten dauern …"):
            st.session_state["live_ergebnis"] = (schluessel, _live_messreihe(familie, int(live_n), int(live_f), C.LIVE_BUDGET, int(anteil), int(grenze), regel))
    erg = st.session_state.get("live_ergebnis")
    if erg is None or erg[0] != schluessel:
        st.info("Für diese Einstellung ist noch nichts gerechnet. Mit „Messreihe rechnen“ starten.")
    else:
        zl = erg[1]
        a_live = next((a for a in C.LIVE_ABSTAENDE if a == int(abstand)), 500)
        kind, text = E.verdict_loeschen(zl, a_live, regel, int(anteil), int(grenze))
        getattr(st, kind)(text)
        rows_l = []
        for a in C.LIVE_ABSTAENDE:
            k = E.kennzahlen(E.waehle(zl, a, regel))
            rows_l.append(["nie" if a is None else str(a), E.zahl(k.konflikte_median), E.zahl(k.konflikte_max), E.zahl(k.lesezugriffe_median), E.zahl(k.lebend_median), f"{k.mit_loeschen} von {k.formeln}"])
        _tabelle(rows_l, ["Löschabstand", "Konflikte Median", "Maximum", "Lesezugriffe Median", "lebende gelernte Klauseln Median", "Formeln mit Löschrunde"])
        st.caption(f"Live gerechnet mit den Zufalls-Seeds {M.SEED_BASIS} bis {M.SEED_BASIS + int(live_f) - 1}, Konfliktbudget {E.zahl(C.LIVE_BUDGET)}; das Urteil gilt für den gewählten Löschabstand der Seitenleiste (ohne Löschen: 500).")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

with tab4:
    st.subheader("🔬 Welche Regel löscht gut?")
    st.caption(f"Eingefrorene Messung (vorgerechnet, nicht live): dieselben {C.FORMELN_JE_FAMILIE} Formeln wie in Experiment 3 ({M.FAMILIEN_NAMEN[familie]}, n = {fam_n}), Löschen alle {C.REGEL_ABSTAND} Konflikte, Anteil ½, LBD-Grenze 2. "
               "Nur die Rangordnung der Kandidaten ändert sich: LBD dann Länge, Länge dann LBD, zufällig.")
    kind, text = E.verdict_regeln(zeilen)
    getattr(st, kind)(text)
    reg_rows = []
    for r in C.REGELN:
        k = E.kennzahlen(E.waehle(zeilen, C.REGEL_ABSTAND, r))
        reg_rows.append([C.REGEL_NAMEN[r], E.zahl(k.konflikte_median), E.zahl(k.konflikte_p90), E.zahl(k.konflikte_max), E.zahl(k.lesezugriffe_median), E.zahl(k.lebend_median), f"{k.abbrueche} von {k.formeln}"])
    _tabelle(reg_rows, ["Rangordnung", "Konflikte Median", "90-Prozent-Rang", "Maximum", "Lesezugriffe Median", "lebende gelernte Klauseln Median", "Abbrüche am Budget"])
    st.plotly_chart(V.build_regeln(zeilen), width="stretch", key="regeln_chart")
    st.caption("Je Punkt eine Formel (logarithmische Achse); das blaue Band ist die Streubreite der Suche (Mediane von sechs Läufen ohne Löschen). Ein Unterschied zwischen den Regeln zählt hier nur, wenn er aus diesem Band herausführt.")

sync_query_params({k: st.session_state.get(k, spec.default) for k, spec in SETTING_SPECS.items()})

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist |
|---|---|
| **Zwei Aufgabenfamilien, je 20 Formeln, ein Lauf je Formel und Variante** | Zufalls-3-SAT (n = 175) und 3-Färbung (300 Knoten, mittlerer Grad 4,5) sind gemessen, andere Familien und Industrieformeln nicht; die Aussagen gelten für diese Läufe. |
| **Die Konfliktzahl schwankt je Formel um Faktoren** | Ohne die Streumessung (sechs Läufe ohne Löschen) wäre „Löschen spart Konflikte“ nicht behauptbar; die App urteilt über Konflikte nur gegen dieses Band. |
| **Lesezugriffe sind eine Zählgröße dieses Python-Lösers** | Sie sind keine Laufzeit und keine Byte; die Aussage „Propagation ist der Zeitfresser (etwa 80 %)“ steht im Chaff-Papier für dessen Löser, nicht für diesen. |
| **Der Löschzeitpunkt ist alle 250 bis 2 000 Konflikte** | Glucose löscht nach 20 000 + 500 · x Konflikten; die Aufgaben dieser Demo sind klein, deshalb früher. Die Wirkung auf große Formeln ist unbekannt. |
| **Eine feste Löschregel (Kern des Lösers)** | Aktivitätsbasiertes Löschen (MiniSat) und der Zeitplan von Glucose sind nicht umgesetzt. |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben und gesucht.** Gegeben ist eine Formel in konjunktiver Normalform und ein Löser, der aus jedem Konflikt eine Klausel $C_i$ lernt. Gesucht ist, welche der gelernten Klauseln nach einer Konfliktzahl, die ein Vielfaches des Abstands $d$ ist, gelöscht werden.

| Symbol | Bedeutung |
|---|---|
| $C_i$ | gelernte Klausel Nr. $i$ (ältere Klauseln haben die kleinere Nummer) |
| $\ell(x)$ | Entscheidungsstufe der Variablen $x$ auf dem Trail |
| $L$ | LBD-Grenze (Standard 2) |
| $a$ | Anteil der Kandidaten, der fällt (Standard $\tfrac12$) |
| $G$ | Menge der gesperrten Klauseln (Grund eines Trail-Literals) |
| $d$ | Löschabstand in Konflikten |

**LBD.** Die Literal Block Distance einer Klausel ist die Zahl der verschiedenen Entscheidungsstufen ihrer Variablen:

$$\operatorname{lbd}(C) = \bigl|\{\, \ell(x) : x \text{ kommt in } C \text{ vor} \,\}\bigr|.$$

**Kandidaten.** Gelernte, noch lebende Klauseln über der Grenze und nicht gesperrt:

$$K = \{\, i : C_i \text{ gelernt und lebend},\ \operatorname{lbd}(C_i) > L,\ i \notin G \,\}.$$

**Rangordnung und Löschrunde.** Die Kandidaten werden nach dem Schlüssel $(\operatorname{lbd}(C_i), |C_i|, -i)$ absteigend geordnet; der dritte Bestandteil $-i$ macht die Ordnung eindeutig: bei Gleichstand in LBD und Länge fällt die ältere Klausel zuerst. Es fallen die ersten

$$\lfloor a \cdot |K| \rfloor$$

Kandidaten dieser Rangfolge (abgerundet: bei einem Kandidaten und $a = \tfrac12$ fällt keiner). Alle $d$ Konflikte wird diese Runde ausgeführt; der Bestand ist also ein Sägezahn.

**Bestand und Lesezugriffe.** Der Bestand nach $c$ Konflikten ist die Zahl der gelernten Klauseln der Länge $\ge 2$, die nicht gelöscht sind (Einheitsklauseln werden nicht gespeichert). Ein Lesezugriff ist ein gelesenes Literal einer besuchten Klausel bei der Propagation; die Summe über alle Propagationen ist die Zählgröße der Demo.

**Literatur.** G. Audemard, L. Simon: Predicting learnt clauses quality in modern SAT solvers. IJCAI 2009 (Volltext gelesen): LBD als Qualitätsmaß, Löschen der Hälfte der gelernten Klauseln alle 20 000 + 500 · x Konflikte; Klauseln mit LBD 2 („glue“) bleiben nach der Glucose-Implementierung (im Paper: „asserting clauses are kept“); diese Demo löscht früher und in kleineren Abständen, weil die Aufgaben klein sind. M. Moskewicz u. a.: Chaff. DAC 2001 (Volltext gelesen): Propagation als Zeitfresser (laut Quelle etwa 80 % der Rechenzeit ihres Lösers).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html)."
)
