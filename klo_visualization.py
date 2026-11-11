"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import klo_constants as C
import klo_evaluation as E


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def klausel_status(nr, h, gesperrt, grenze) -> str:
    """Rolle einer Klausel in der Löschrunde: „faellt“, „bleibt“ (Kandidat, der bleibt), „geschuetzt“ (LBD höchstens Grenze), „gesperrt“."""
    if nr in h.faellt:
        return "faellt"
    if nr in gesperrt:
        return "gesperrt"
    if nr in h.kandidaten:
        return "bleibt"
    return "geschuetzt"


STATUS_TEXT = {"faellt": "fällt", "bleibt": "Kandidat, bleibt", "geschuetzt": "geschützt (LBD ≤ Grenze)", "gesperrt": "gesperrt (Grund eines Trail-Literals)"}
STATUS_FARBE = {"faellt": C.COLOR_FAELLT, "bleibt": C.COLOR_BLEIBT, "geschuetzt": C.COLOR_GESCHUETZT, "gesperrt": C.COLOR_GESPERRT}


def build_hand(h, gesperrt, grenze):
    """LBD je Klausel der Handtabelle als Balken; Farbe = Rolle in der Löschrunde, Zahl im Balken = Länge, Zahl darüber = Platz in der Rangfolge."""
    nummern = sorted(h.lbd)
    status = {nr: klausel_status(nr, h, gesperrt, grenze) for nr in nummern}
    fig = go.Figure()
    for s in ("faellt", "bleibt", "geschuetzt", "gesperrt"):
        xs = [f"Klausel {nr}" for nr in nummern if status[nr] == s]
        if not xs:
            continue
        nr_s = [nr for nr in nummern if status[nr] == s]
        rang = [(h.rangfolge.index(nr) + 1) if nr in h.rangfolge else None for nr in nr_s]
        fig.add_trace(go.Bar(x=xs, y=[h.lbd[nr] for nr in nr_s], name=STATUS_TEXT[s], marker_color=STATUS_FARBE[s],
                             text=[f"Länge {h.laenge[nr]}" + (f"<br>Rang {r}" if r else "") for nr, r in zip(nr_s, rang)], textposition="inside",
                             hovertemplate="%{x}: LBD %{y}<extra>" + STATUS_TEXT[s] + "</extra>"))
    fig.add_hline(y=grenze + 0.5, line_dash="dot", line_color="gray", annotation_text=f"LBD-Grenze {grenze}", annotation_position="top left")
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=[f"Klausel {nr}" for nr in nummern])
    fig.update_yaxes(title_text="LBD (verschiedene Stufen)", dtick=1, rangemode="tozero")
    fig.update_layout(barmode="stack")
    return _base(fig)


def _stufen(punkte, spalte):
    """Stützstellen (Konflikte, Wert) als Treppe darstellen: der Wert gilt bis zur nächsten Stützstelle."""
    return [p[0] for p in punkte], [p[spalte] for p in punkte]


def build_bestand(v):
    """Lebende gelernte Klauseln über den Konflikten, ohne und mit Löschen (Sägezahn der Löschrunden)."""
    fig = go.Figure()
    x, y = _stufen(v.ohne.verlauf, 1)
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color=C.COLOR_OHNE, width=3), name="ohne Löschen", hovertemplate="%{x} Konflikte: %{y} lebend<extra>ohne</extra>"))
    if v.abstand is not None:
        x, y = _stufen(v.mit.verlauf, 1)
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color=C.COLOR_MIT, width=3), name=f"mit Löschen {E.abstand_text(v.abstand)}",
                                 hovertemplate="%{x} Konflikte: %{y} lebend<extra>mit</extra>"))
    fig.update_xaxes(title_text="Konflikte")
    fig.update_yaxes(title_text="lebende gelernte Klauseln", rangemode="tozero")
    return _base(fig)


def build_lesen(v):
    """Kumulierte Lesezugriffe (gelesene Literale) über den Konflikten."""
    fig = go.Figure()
    x, y = _stufen(v.ohne.verlauf, 2)
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color=C.COLOR_OHNE, width=3), name="ohne Löschen", hovertemplate="%{x} Konflikte: %{y:,} Lesezugriffe<extra>ohne</extra>"))
    if v.abstand is not None:
        x, y = _stufen(v.mit.verlauf, 2)
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color=C.COLOR_MIT, width=3), name=f"mit Löschen {E.abstand_text(v.abstand)}",
                                 hovertemplate="%{x} Konflikte: %{y:,} Lesezugriffe<extra>mit</extra>"))
    fig.update_xaxes(title_text="Konflikte")
    fig.update_yaxes(title_text="Lesezugriffe (kumuliert)", rangemode="tozero")
    return _base(fig)


def _name(a, regel="lbd"):
    return "nie" if a is None else f"alle {E.zahl(a)}"


def build_konflikte(zeilen, abstaende=(250, 500, 1000, 2000, None)):
    """Konfliktzahl je Formel (Punkte, logarithmische Achse) für jeden Abstand, dazu das Band der Streubreite (Mediane von sechs Läufen ohne Löschen)."""
    fig = go.Figure()
    s = E.streuung(zeilen)
    namen = [_name(a) for a in abstaende]
    if s is not None:
        fig.add_hrect(y0=max(1, s.untere), y1=max(1, s.obere), fillcolor=C.COLOR_BAND, line_width=0,
                      annotation_text="Streubreite der Suche (Median ohne Löschen)", annotation_position="top left")
    for a, name in zip(abstaende, namen):
        rows = E.waehle(zeilen, a)
        farbe = C.COLOR_OHNE if a is None else C.COLOR_MIT
        fig.add_trace(go.Box(y=[max(1, r["konflikte"]) for r in rows], name=name, boxpoints="all", jitter=0.4, pointpos=0, marker=dict(color=farbe, size=5),
                             line=dict(color=farbe), fillcolor="rgba(0,0,0,0)", hovertemplate="%{y} Konflikte<extra>" + name + "</extra>", showlegend=False))
    fig.update_xaxes(title_text="Löschabstand", categoryorder="array", categoryarray=namen)
    fig.update_yaxes(title_text="Konflikte bis zur Antwort je Formel", type="log")
    return _base(fig, height=380)


def build_median_balken(zeilen, spalte, titel, abstaende=(250, 500, 1000, 2000, None), log=False):
    """Median je Abstand als Balken (Lesezugriffe oder lebende Klauseln)."""
    namen = [_name(a) for a in abstaende]
    werte = [E.kennzahlen(E.waehle(zeilen, a)) for a in abstaende]
    ys = [getattr(k, spalte) for k in werte]
    fig = go.Figure(go.Bar(x=namen, y=ys, marker_color=[C.COLOR_OHNE if a is None else C.COLOR_MIT for a in abstaende],
                           text=[E.zahl(y) for y in ys], textposition="outside", cliponaxis=False, hovertemplate="%{x}: %{y:,}<extra></extra>"))
    fig.update_xaxes(title_text="Löschabstand (Konflikte)", categoryorder="array", categoryarray=namen)
    fig.update_yaxes(title_text=titel, type="log" if log else "linear", rangemode="tozero" if not log else "normal")
    return _base(fig, height=300)


def build_regeln(zeilen, abstand=C.REGEL_ABSTAND):
    """Konfliktzahl je Formel für die drei Regeln (gleicher Anteil, gleicher Abstand), dazu das Band der Streubreite."""
    fig = go.Figure()
    s = E.streuung(zeilen)
    if s is not None:
        fig.add_hrect(y0=max(1, s.untere), y1=max(1, s.obere), fillcolor=C.COLOR_BAND, line_width=0,
                      annotation_text="Streubreite der Suche (Median ohne Löschen)", annotation_position="top left")
    for r in C.REGELN:
        rows = E.waehle(zeilen, abstand, r)
        fig.add_trace(go.Box(y=[max(1, z["konflikte"]) for z in rows], name=C.REGEL_KURZ[r], boxpoints="all", jitter=0.4, pointpos=0,
                             marker=dict(color=C.REGEL_FARBEN[r], size=5), line=dict(color=C.REGEL_FARBEN[r]), fillcolor="rgba(0,0,0,0)", showlegend=False,
                             hovertemplate="%{y} Konflikte<extra>" + C.REGEL_KURZ[r] + "</extra>"))
    fig.update_xaxes(title_text=f"Regel (Löschen {E.abstand_text(abstand)})")
    fig.update_yaxes(title_text="Konflikte bis zur Antwort je Formel", type="log")
    return _base(fig, height=360)
