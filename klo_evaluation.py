"""Kennzahlen aus Messreihen und die Verdikte der App (reine Funktionen: `verdict_*(…) -> (Art, Text)`, die App ruft `getattr(st, Art)(Text)`).

Jede Zahl im Text stammt aus den Zeilen einer Messreihe (`klo_messung`) oder einem Live-Lauf; die Tests prüfen Schwellen und Texte an handgesetzten Zeilen.
Vergleiche von Konfliktzahlen stehen immer neben der Streubreite der Suche: dem Band der Mediane von sechs Läufen ohne Löschen (feste Reihenfolge der
Gleichstände und fünf zufällige Anfangsaktivitäten). Prozentangaben nennen ihre Basis."""
import statistics
from dataclasses import dataclass
from fractions import Fraction

import klo_constants as C
import klo_loeschen as L

REFERENZ_SEEDS = (1, 2, 3, 4, 5)


# ---------------------------------------------------------------- Formate
def zahl(x) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner; Halbe (Median einer geraden Anzahl) mit Dezimalkomma."""
    if float(x).is_integer():
        return f"{int(x):,}".replace(",", " ")
    return dezimal(x, 1)


def dezimal(x: float, stellen: int = 1) -> str:
    return f"{x:,.{stellen}f}".replace(",", " ").replace(".", ",")


def prozent(x: float, stellen: int = 0) -> str:
    return dezimal(x, stellen)


def abstand_text(abstand) -> str:
    return "nie" if not abstand else f"alle {zahl(abstand)} Konflikte"


# ---------------------------------------------------------------- Auswahl und Kennzahlen
def waehle(zeilen, abstand=None, regel="lbd", loeser_seed=None) -> list:
    """Zeilen einer Variante, nach Formel sortiert. `abstand=None, loeser_seed=None` ist der Lauf ohne Löschen mit fester Reihenfolge der Gleichstände."""
    if abstand is None:
        regel = "lbd"
    return sorted((z for z in zeilen if z["abstand"] == abstand and z["regel"] == regel and z["loeser_seed"] == loeser_seed), key=lambda z: z["formel"])


def perzentil(werte, q: float):
    """Rang-Perzentil wie in der Vormessung: das Element an Stelle min(n − 1, ⌊q · n⌋) der sortierten Liste."""
    w = sorted(werte)
    return w[min(len(w) - 1, int(q * len(w)))]


@dataclass(frozen=True)
class Kennzahlen:
    formeln: int
    konflikte_median: float
    konflikte_p90: float
    konflikte_max: float
    abbrueche: int
    lesezugriffe_median: float
    lesezugriffe_summe: int
    lebend_median: float
    mit_loeschen: int            # Formeln, in denen mindestens eine Klausel fiel


def kennzahlen(zeilen) -> Kennzahlen:
    if not zeilen:
        raise ValueError("keine Zeilen")
    return Kennzahlen(
        len(zeilen), statistics.median(z["konflikte"] for z in zeilen), perzentil([z["konflikte"] for z in zeilen], 0.9), max(z["konflikte"] for z in zeilen),
        sum(z["antwort"] == "abbruch" for z in zeilen), statistics.median(z["lesezugriffe"] for z in zeilen), sum(z["lesezugriffe"] for z in zeilen),
        statistics.median(z["lebend"] for z in zeilen), sum(z["geloescht"] > 0 for z in zeilen))


@dataclass(frozen=True)
class Streuung:
    mediane: tuple        # Median der Konflikte je Referenzlauf (fester Start, dann Löser-Seeds 1 bis 5)
    untere: float
    obere: float
    faktor_median: float  # Median über die Formeln von (größte / kleinste Konfliktzahl der Referenzläufe)


def streuung(zeilen, seeds=REFERENZ_SEEDS) -> Streuung | None:
    """Streubreite der Suche ohne Löschen: Mediane über die Formeln für den festen Start und jeden Löser-Seed. None, wenn die Referenzläufe fehlen."""
    laeufe = [waehle(zeilen)] + [waehle(zeilen, loeser_seed=s) for s in seeds]
    if any(len(l) != len(laeufe[0]) or not l for l in laeufe):
        return None
    mediane = tuple(statistics.median(z["konflikte"] for z in l) for l in laeufe)
    faktoren = []
    for i in range(len(laeufe[0])):
        werte = [max(1, l[i]["konflikte"]) for l in laeufe]
        faktoren.append(max(werte) / min(werte))
    return Streuung(mediane, min(mediane), max(mediane), statistics.median(faktoren))


def aenderung(neu: float, basis: float) -> float | None:
    """Änderung in Prozent der Basis (positiv = mehr); None bei Basis 0."""
    return None if basis == 0 else 100.0 * (neu - basis) / basis


def paarvergleich(zeilen, abstand, regel="lbd") -> dict:
    """Je Formel, in der gelöscht wurde: weniger / gleich / mehr Konflikte und weniger Lesezugriffe als im Lauf ohne Löschen."""
    ohne = {z["formel"]: z for z in waehle(zeilen)}
    mit = waehle(zeilen, abstand, regel)
    aktiv = [z for z in mit if z["geloescht"] > 0]
    return {"aktiv": len(aktiv), "formeln": len(mit),
            "weniger_konflikte": sum(z["konflikte"] < ohne[z["formel"]]["konflikte"] for z in aktiv),
            "gleich_konflikte": sum(z["konflikte"] == ohne[z["formel"]]["konflikte"] for z in aktiv),
            "mehr_konflikte": sum(z["konflikte"] > ohne[z["formel"]]["konflikte"] for z in aktiv),
            "weniger_lesezugriffe": sum(z["lesezugriffe"] < ohne[z["formel"]]["lesezugriffe"] for z in aktiv)}


def zusammenfassung_tabelle(zeilen, abstaende=(250, 500, 1000, 2000, None)) -> list:
    """Zeilen für die Tabelle von Experiment 3: je Abstand die Kennzahlen."""
    ausgabe = []
    for a in abstaende:
        k = kennzahlen(waehle(zeilen, a))
        ausgabe.append({"abstand": a, "k": k})
    return ausgabe


# ---------------------------------------------------------------- Verdikte
def verdict_hand(h, anteil=L.STANDARD_ANTEIL, grenze=L.STANDARD_GRENZE) -> tuple:
    """Verdikt der Löschrunde von Hand (Handtabelle): Kandidaten, fallende und bleibende Klauseln."""
    k = len(h.kandidaten)
    gesamt = len(h.lbd)
    if k == 0:
        return "info", (f"Keine Klausel ist Kandidat (LBD über {grenze} und nicht gesperrt): es fällt keine, alle {gesamt} gelernten Klauseln bleiben.")
    if not h.faellt:
        return "info", (f"{k} {'Kandidat' if k == 1 else 'Kandidaten'}, aber ⌊{anteil_text(anteil)} · {k}⌋ = 0: abgerundet fällt keine Klausel, alle {gesamt} bleiben.")
    nummern = ", ".join(str(n) for n in h.faellt)
    return "success", (f"{k} {'Kandidat' if k == 1 else 'Kandidaten'}; ⌊{anteil_text(anteil)} · {k}⌋ = {len(h.faellt)} fallen: {'Klausel' if len(h.faellt) == 1 else 'Klauseln'} {nummern}. "
                       f"Von {gesamt} gelernten Klauseln bleiben {len(h.bleibt)}.")


def anteil_text(anteil) -> str:
    a = Fraction(anteil)
    return f"{a.numerator}/{a.denominator}"


def verdict_bestand(v) -> tuple:
    """Verdikt des Live-Vergleichs (Reiter „Bestand über die Konflikte“). `v`: `klo_algorithm.LiveVergleich`."""
    o, m = v.ohne.stat, v.mit.stat
    if o["konflikte"] == 0:
        return "info", "Die Aufgabe ist ohne Konflikt gelöst: es wird nichts gelernt und nichts gelöscht."
    if v.abstand is None:
        return "info", (f"Ohne Löschen bleiben alle gelernten Klauseln: nach {zahl(o['konflikte'])} Konflikten sind es {zahl(o['lebend_gelernt'])} lebende gelernte Klauseln, "
                        f"gelesen wurden {zahl(o['lesezugriffe'])} Literale.")
    if m["geloescht"] == 0:
        return "info", (f"Bis zum Ende ({zahl(m['konflikte'])} Konflikte) kam keine Löschrunde: der Abstand {zahl(v.abstand)} wird nicht erreicht oder alle Kandidaten sind geschützt. "
                        f"Beide Läufe sind gleich: {zahl(o['lebend_gelernt'])} lebende gelernte Klauseln.")
    bestand = aenderung(m["lebend_gelernt"], o["lebend_gelernt"])
    lesen = aenderung(m["lesezugriffe"], o["lesezugriffe"])
    konf = aenderung(m["konflikte"], o["konflikte"])
    satz = (f"Mit Löschen {abstand_text(v.abstand)}: {zahl(m['lebend_gelernt'])} statt {zahl(o['lebend_gelernt'])} lebende gelernte Klauseln "
            f"({prozent(abs(bestand))} % {'weniger' if bestand < 0 else 'mehr'}, Basis ohne Löschen), "
            f"{zahl(m['lesezugriffe'])} statt {zahl(o['lesezugriffe'])} Lesezugriffe ({prozent(abs(lesen))} % {'weniger' if lesen < 0 else 'mehr'}). "
            f"Konflikte bis zur Antwort: {zahl(m['konflikte'])} statt {zahl(o['konflikte'])} "
            f"({'gleich viele' if konf == 0 else prozent(abs(konf)) + ' % ' + ('weniger' if konf < 0 else 'mehr')}; eine einzelne Formel sagt nichts über die Streuung der Suche).")
    if v.ohne.ergebnis.antwort is None or v.mit.ergebnis.antwort is None:
        return "warning", satz + " Mindestens ein Lauf brach am Konfliktbudget ab: die Zahlen sind Untergrenzen."
    return ("success" if lesen < 0 else "info"), satz


def regel_text(anteil_prozent=50, grenze=2, regel="lbd") -> str:
    return f"Anteil {anteil_text(Fraction(anteil_prozent, 100))}, LBD-Grenze {grenze}, Regel {C.REGEL_KURZ[regel]}"


def verdict_loeschen(zeilen, abstand, regel="lbd", anteil_prozent=50, grenze=2) -> tuple:
    """Verdikt von Experiment 3 für einen Abstand: Lesezugriffe und Bestand gegen den Lauf ohne Löschen, Konflikte gegen die Streubreite der Suche."""
    if not abstand:
        return "info", "Ohne Löschen ist der Vergleichslauf selbst; einen Abstand wählen, um ihn mit dem Löschen zu vergleichen."
    ohne, mit = kennzahlen(waehle(zeilen)), kennzahlen(waehle(zeilen, abstand, regel))
    s = streuung(zeilen)
    if mit.mit_loeschen == 0:
        return "info", f"Bei Löschen {abstand_text(abstand)} fiel in keiner der {mit.formeln} Formeln eine Klausel: alle Läufe sind gleich dem Lauf ohne Löschen."
    lesen = aenderung(mit.lesezugriffe_median, ohne.lesezugriffe_median)
    bestand = aenderung(mit.lebend_median, ohne.lebend_median)
    konf = aenderung(mit.konflikte_median, ohne.konflikte_median)
    teile = [f"Löschen {abstand_text(abstand)} ({regel_text(anteil_prozent, grenze, regel)}), {mit.formeln} Formeln, in {mit.mit_loeschen} davon fiel mindestens eine Klausel: "
             f"Median der Lesezugriffe {zahl(mit.lesezugriffe_median)} statt {zahl(ohne.lesezugriffe_median)} ({_richtung(lesen)}, Basis ohne Löschen), "
             f"Median der lebenden gelernten Klauseln {zahl(mit.lebend_median)} statt {zahl(ohne.lebend_median)} ({_richtung(bestand)}). "
             f"Median der Konflikte {zahl(mit.konflikte_median)} statt {zahl(ohne.konflikte_median)} ({_richtung(konf)})."]
    art = "success" if lesen is not None and lesen < 0 else "info"
    if s is None:
        teile.append("Die Streubreite der Suche ist in dieser Messung nicht enthalten: ohne sie ist über die Konflikte kein Urteil möglich.")
    else:
        band = f"{zahl(s.untere)} bis {zahl(s.obere)}"
        if s.untere <= mit.konflikte_median <= s.obere:
            teile.append(f"Das liegt innerhalb der Streubreite der Suche (Mediane von sechs Läufen ohne Löschen: {band}): in den Konflikten ist kein Unterschied erkennbar.")
        else:
            richtung = "unter" if mit.konflikte_median < s.untere else "über"
            teile.append(f"Das liegt {richtung} der Streubreite der Suche (Mediane von sechs Läufen ohne Löschen: {band}).")
            if richtung == "über":
                art = "warning"
        teile.append(f"Je Formel schwanken die sechs Läufe ohne Löschen im Median um den Faktor {dezimal(s.faktor_median, 2)} (größte gegen kleinste Konfliktzahl).")
    summe = aenderung(mit.lesezugriffe_summe, ohne.lesezugriffe_summe)
    p = paarvergleich(zeilen, abstand, regel)
    teile.append(f"Summe der Lesezugriffe über die {mit.formeln} Formeln: {zahl(mit.lesezugriffe_summe)} statt {zahl(ohne.lesezugriffe_summe)} ({_richtung(summe)}). "
                 f"In den {p['aktiv']} Formeln mit Löschrunde brauchte der Lauf mit Löschen in {p['weniger_konflikte']} weniger, in {p['gleich_konflikte']} gleich viele und in {p['mehr_konflikte']} mehr Konflikte "
                 f"als der Lauf ohne Löschen und in {p['weniger_lesezugriffe']} weniger Lesezugriffe (je Formel ein Lauf, ohne Streubreite).")
    if mit.abbrueche or ohne.abbrueche:
        teile.append(f"Abbrüche am Konfliktbudget: {ohne.abbrueche} ohne Löschen, {mit.abbrueche} mit Löschen; ihre Konfliktzahlen sind Untergrenzen.")
    return art, " ".join(teile)


def _richtung(x) -> str:
    if x is None:
        return "Basis 0"
    if x == 0:
        return "unverändert"
    return f"{prozent(abs(x))} % {'weniger' if x < 0 else 'mehr'}"


def verdict_regeln(zeilen, abstand=C.REGEL_ABSTAND) -> tuple:
    """Verdikt von Experiment 4: drei Regeln bei gleichem Anteil und gleichem Abstand. Konflikte gegen die Streubreite, Lesezugriffe und Bestand als Mediane."""
    ks = {r: kennzahlen(waehle(zeilen, abstand, r)) for r in C.REGELN}
    s = streuung(zeilen)
    zeile = "; ".join(f"{C.REGEL_KURZ[r]}: Konflikte {zahl(ks[r].konflikte_median)}, Lesezugriffe {zahl(ks[r].lesezugriffe_median)}, lebend {zahl(ks[r].lebend_median)}" for r in C.REGELN)
    text = f"Mediane über {ks['lbd'].formeln} Formeln bei Löschen {abstand_text(abstand)}: {zeile}."
    if s is None:
        return "info", text + " Ohne die Referenzläufe ist über die Konflikte kein Urteil möglich."
    aussen = [r for r in C.REGELN if not s.untere <= ks[r].konflikte_median <= s.obere]
    band = f"{zahl(s.untere)} bis {zahl(s.obere)}"
    if not aussen:
        text += f" Die Konflikte aller drei Regeln liegen innerhalb der Streubreite der Suche ({band}, Mediane von sechs Läufen ohne Löschen): in den Konflikten fällt die Rangordnung nicht auseinander."
        return "info", text
    namen = ", ".join(C.REGEL_KURZ[r] for r in aussen)
    return "warning", text + (f" Außerhalb der Streubreite der Suche ({band}) {'liegt die Regel' if len(aussen) == 1 else 'liegen die Regeln'} {namen}."
                              " Außerhalb des Bandes heißt nicht deutlich schlechter als eine Regel im Band: dafür zählt der Abstand der Mediane im Vergleich zur Breite des Bandes.")
