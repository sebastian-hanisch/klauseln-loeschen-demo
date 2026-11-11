"""Permalink (Begrenzen), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio)."""

import time
from dataclasses import dataclass

import streamlit as st

import klo_constants as C
from klo_rng import SplitMix64


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple | None = None
    liste: bool = False          # Mehrfachauswahl: Wert ist eine Teilmenge von `options`, in der Adresszeile „3,7“


SETTING_SPECS = {
    "familie_select": SettingSpec("familie", str, C.DEFAULT_FAMILIE, options=C.FAMILIEN),
    "n_slider": SettingSpec("n", int, C.DEFAULT_N, C.N_MIN, C.N_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
    "budget_select": SettingSpec("budget", int, C.DEFAULT_BUDGET, options=C.BUDGET_OPTIONEN),
    "anteil_select": SettingSpec("anteil", int, C.DEFAULT_ANTEIL, options=C.ANTEIL_OPTIONEN),
    "grenze_slider": SettingSpec("grenze", int, C.DEFAULT_GRENZE, C.GRENZE_MIN, C.GRENZE_MAX),
    "regel_select": SettingSpec("regel", str, C.DEFAULT_REGEL, options=C.REGELN),
    "gesperrt_multi": SettingSpec("gesperrt", int, C.DEFAULT_GESPERRT, options=C.GESPERRT_OPTIONEN, liste=True),
    "abstand_select": SettingSpec("abstand", int, C.DEFAULT_ABSTAND, options=C.ABSTAND_OPTIONEN),
    "live_n_slider": SettingSpec("livemn", int, C.DEFAULT_LIVE_N, C.LIVE_N_MIN, C.LIVE_N_MAX),
    "live_f_slider": SettingSpec("livef", int, C.DEFAULT_LIVE_F, C.LIVE_F_MIN, C.LIVE_F_MAX),
}
PRESET_KEYS = {
    "familie": "familie_select", "n": "n_slider", "seed": "seed_input", "budget": "budget_select", "anteil": "anteil_select", "grenze": "grenze_slider",
    "regel": "regel_select", "gesperrt": "gesperrt_multi", "abstand": "abstand_select", "live_n": "live_n_slider", "live_f": "live_f_slider",
}


def start_wert(spec):
    """Anfangswert für den Session State (Mehrfachauswahl als Liste)."""
    return list(spec.default) if spec.liste else spec.default


def normiert(wert):
    """Vergleichsform: Mehrfachauswahlen als sortiertes Tupel, damit die Reihenfolge der Auswahl nichts ändert."""
    return tuple(sorted(wert)) if isinstance(wert, (list, tuple)) else wert


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = start_wert(spec)


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def _bereinige(spec, wert):
    """Wert aus der Adresszeile auf die Reglergrenzen begrenzen beziehungsweise auf erlaubte Optionen prüfen; None = verwerfen."""
    if spec.liste:
        teile = [t for t in str(wert).split(",") if t.strip()]
        try:
            zahlen = sorted({int(t) for t in teile})
        except ValueError:
            return None
        return zahlen if all(z in spec.options for z in zahlen) else None
    if spec.options is not None:
        return wert if wert in spec.options else None
    if spec.lo is not None:
        wert = max(spec.lo, wert)
    if spec.hi is not None:
        wert = min(spec.hi, wert)
    return wert


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die Reglergrenzen begrenzt."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                roh = qp[spec.url_param] if spec.liste else spec.caster(qp[spec.url_param])
                wert = _bereinige(spec, roh)
            except (ValueError, TypeError):
                continue
            if wert is not None:
                st.session_state[state_key] = wert
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = ",".join(str(v) for v in sorted(value)) if SETTING_SPECS[state_key].liste else str(value)
    except Exception:
        pass


def apply_preset(name):
    """Ein Preset setzt alle Regler: was es nicht nennt, bekommt den Standardwert."""
    for key, state_key in PRESET_KEYS.items():
        spec = SETTING_SPECS[state_key]
        wert = C.PRESETS[name].get(key, spec.default)
        st.session_state[state_key] = list(wert) if spec.liste else wert


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen
    Standardwert) mit dem Session State. Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS,
    dann hebt auch seine Änderung die Markierung auf (tests/test_layout.py prüft das für jeden Regler)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            normiert(st.session_state.get(state_key, spec.default)) == normiert(preset.get(preset_key_of.get(state_key), spec.default))
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    """Neuer Zufalls-Seed der Live-Aufgabe; der Strom kommt aus dem SplitMix64 des Repos, gespeist von der Uhr."""
    st.session_state["seed_input"] = SplitMix64(time.time_ns()).below(C.SEED_MAX + 1)
