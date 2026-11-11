"""Live-Aufgabe und Live-Messreihe mit Fortschrittsanzeige und Zwischenspeicher (nur Bedienung, keine Rechnung).

Aufgaben sind hier die Läufe des Lösers: Der Lauf ohne Löschen (`lauf_ohne`) hängt nicht vom Löschabstand und den Regeln ab und wird deshalb allein
zwischengespeichert; ändert jemand in der Seitenleiste nur das Löschen, rechnet die App nur den Lauf mit Löschen (`lauf_mit`) neu. Die Messreihe auf Knopfdruck
rechnet je Formel (`messreihe_formel`: vier Abstände und fünf Läufe ohne Löschen, gleiche Aufrufe wie `klo_messung.messreihe`) und speichert jede Formel
einzeln (`st.cache_data`, höchstens 40 Einträge je Funktion). Der Fortschrittsbalken zählt die fertigen Läufe bzw. Formeln. Die Ergebnisse sind gleich denen
von `klo_algorithm.live_vergleich` und `klo_messung.messreihe` (`tests/test_fortschritt.py`)."""

from contextlib import contextmanager
from fractions import Fraction

import streamlit as st

import klo_algorithm as A
import klo_constants as C
import klo_evaluation as E
import klo_loeschen as L
import klo_messung as M

_ZAEHLER = {"gerechnet": 0}


def gerechnet() -> int:
    """Wie viele Läufe bzw. Formeln in diesem Prozess tatsächlich gerechnet (nicht aus dem Zwischenspeicher geholt) wurden; dient dem Test."""
    return _ZAEHLER["gerechnet"]


@st.cache_data(show_spinner=False, max_entries=40)
def lauf_ohne(familie: str, n: int, seed: int, budget: int):
    """Der Lauf ohne Löschen, gleich dem ersten Lauf in `A.live_vergleich`."""
    _ZAEHLER["gerechnet"] += 1
    inst = M.aufgabe(familie, n, seed)
    return L.lauf(inst.n, inst.klauseln, abstand=None, budget=budget, abtast=A.abtastabstand(budget))


@st.cache_data(show_spinner=False, max_entries=40)
def lauf_mit(familie: str, n: int, seed: int, budget: int, abstand: int, anteil_prozent: int, grenze: int, regel: str):
    """Der Lauf mit Löschen alle `abstand` Konflikte, gleich dem zweiten Lauf in `A.live_vergleich`."""
    _ZAEHLER["gerechnet"] += 1
    inst = M.aufgabe(familie, n, seed)
    return L.lauf(inst.n, inst.klauseln, abstand=abstand, anteil=Fraction(anteil_prozent, 100), lbd_grenze=grenze, regel=regel, budget=budget,
                  abtast=A.abtastabstand(budget))


def live_vergleich(familie: str, n: int, seed: int, budget: int, abstand: int, anteil_prozent: int, grenze: int, regel: str, melde=None) -> A.LiveVergleich:
    """Wie `A.live_vergleich(familie, n, seed, budget, abstand or None, Fraction(anteil_prozent, 100), grenze, regel)`; `melde(fertig, gesamt)` nach jedem Lauf."""
    inst = M.aufgabe(familie, n, seed)
    gesamt = 1 if not abstand else 2
    ohne = lauf_ohne(familie, n, seed, budget)
    if melde:
        melde(1, gesamt)
    if not abstand:
        return A.LiveVergleich(ohne, ohne, None, inst.n, len(inst.klauseln))
    mit = lauf_mit(familie, n, seed, budget, abstand, anteil_prozent, grenze, regel)
    if melde:
        melde(2, gesamt)
    return A.LiveVergleich(ohne, mit, abstand, inst.n, len(inst.klauseln))


@st.cache_data(show_spinner=False, max_entries=40)
def messreihe_formel(familie: str, n: int, formel: int, budget: int, anteil_prozent: int, grenze: int, regel: str) -> list:
    """Die Zeilen einer Formel der Messreihe: gleich `M.messreihe(familie, n, [formel], ...)` mit den Abständen und Löser-Seeds der App."""
    _ZAEHLER["gerechnet"] += 1
    return M.messreihe(familie, n, [formel], C.LIVE_ABSTAENDE, budget, E.REFERENZ_SEEDS, haupt_regel=regel, anteil=Fraction(anteil_prozent, 100), grenze=grenze)


def messreihe(familie: str, n: int, formeln: int, budget: int, anteil_prozent: int, grenze: int, regel: str, melde=None) -> list:
    """Die Messreihe wie `M.messreihe(familie, n, range(formeln), ...)`; `melde(fertig, gesamt)` wird nach jeder Formel aufgerufen."""
    zeilen = []
    for f in range(formeln):
        zeilen += messreihe_formel(familie, n, f, budget, anteil_prozent, grenze, regel)
        if melde:
            melde(f + 1, formeln)
    return zeilen


@contextmanager
def fortschrittsbalken(text: str):
    """Fortschrittsbalken mit Beschriftung; liefert `melde(fertig, gesamt)` und räumt den Balken am Ende weg."""
    balken = st.progress(0.0, text=text)

    def melde(fertig: int, gesamt: int) -> None:
        balken.progress(fertig / gesamt, text=f"{text}: {fertig} von {gesamt}")

    try:
        yield melde
    finally:
        balken.empty()
