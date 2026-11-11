"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""
import klo_loeschen as L
import klo_messung as M

FAMILIEN = M.FAMILIEN
FAMILIEN_NAMEN = M.FAMILIEN_NAMEN
DEFAULT_FAMILIE = "zufall"
REGELN = L.REGELN
REGEL_NAMEN = {"lbd": "LBD, dann Länge (Standard)", "laenge": "Länge, dann LBD", "zufall": "zufällig (SplitMix64)"}
REGEL_KURZ = {"lbd": "LBD", "laenge": "Länge", "zufall": "zufällig"}
DEFAULT_REGEL = "lbd"

N_MIN, N_MAX, DEFAULT_N = 60, 200, 120            # Größe der Live-Aufgabe: Variablen (Zufalls-3-SAT) bzw. Knoten (Färbung, 3n Variablen)
SEED_MAX = 999999
DEFAULT_SEED = 4004                              # Zufalls-Seed der Live-Aufgabe (SplitMix64-Erzeuger): Zufallsformel, n = 120
BUDGET_OPTIONEN = (2000, 5000, 10000, 20000)     # Konfliktbudget der Live-Läufe
DEFAULT_BUDGET = 10000
ABSTAND_OPTIONEN = (250, 500, 1000, 2000, 0)     # Löschen alle so viele Konflikte; 0 = nie
DEFAULT_ABSTAND = 500
ANTEIL_OPTIONEN = (25, 50, 75)                   # Prozent der Kandidaten, die fallen (¼, ½, ¾)
DEFAULT_ANTEIL = 50
GRENZE_MIN, GRENZE_MAX, DEFAULT_GRENZE = 1, 3, 2
GESPERRT_OPTIONEN = tuple(range(1, 9))           # Klauseln der Handtabelle
DEFAULT_GESPERRT = (3, 7)
LIVE_N_MIN, LIVE_N_MAX, DEFAULT_LIVE_N = 60, 120, 100      # Messreihe auf Knopfdruck
LIVE_F_MIN, LIVE_F_MAX, DEFAULT_LIVE_F = 4, 10, 6
LIVE_ABSTAENDE = (250, 500, 1000, None)
LIVE_BUDGET = 20000

REGEL_ABSTAND = 500                              # Experiment 4: alle Regeln löschen alle 500 Konflikte (Anteil ½, LBD-Grenze 2)
FORMELN_JE_FAMILIE = 20

COLOR_OHNE = "#9aa0a6"
COLOR_MIT = "#2F6B65"
COLOR_FAELLT = "#d9534f"
COLOR_BLEIBT = "#2F6B65"
COLOR_GESCHUETZT = "#4c78a8"
COLOR_GESPERRT = "#e0a030"
COLOR_BAND = "rgba(76,120,168,0.18)"
REGEL_FARBEN = {"lbd": "#2F6B65", "laenge": "#4c78a8", "zufall": "#c07a2c"}

PRESETS = {
    "Handtabelle (Löschrunde von Hand)": {},
    "Zufallsformel mittel": {"abstand": 250},
    "Färbung": {"familie": "faerbung", "n": 200, "seed": 4003, "abstand": 250},
    "Ohne Löschen (Vergleich)": {"abstand": 0},
}
PRESET_HELP = {
    "Handtabelle (Löschrunde von Hand)": "Reiter „Eine Löschrunde von Hand“: acht gelernte Klauseln, zwei gesperrt. Es fallen die Klauseln 8 und 5, es bleiben 1, 2, 3, 4, 6 und 7. Die Reiter mit Aufgaben rechnen eine Zufallsformel mit 120 Variablen, Löschen alle 500 Konflikte.",
    "Zufallsformel mittel": "Zufalls-3-SAT mit 120 Variablen (Zufalls-Seed 4004), Löschen alle 250 Konflikte; der Reiter „Bestand über die Konflikte“ zeigt die Sägezahnlinie.",
    "Färbung": "3-Färbung eines Zufallsgraphen mit 200 Knoten und mittlerem Grad 4,5 (Zufalls-Seed 4003), Löschen alle 250 Konflikte.",
    "Ohne Löschen (Vergleich)": "Dieselbe Zufallsformel wie im Preset „Zufallsformel mittel“, aber ohne Löschen: der Bestand wächst mit jedem Konflikt, beide Linien fallen zusammen.",
}
