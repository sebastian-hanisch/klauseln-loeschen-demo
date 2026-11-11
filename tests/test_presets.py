"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Bereinigung."""

import klo_constants as C
import klo_presets as P


def test_every_preset_has_help_and_only_known_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) <= set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds_or_options():
    for name, preset in C.PRESETS.items():
        for key, value in preset.items():
            spec = P.SETTING_SPECS[P.PRESET_KEYS[key]]
            if spec.options is not None:
                assert value in spec.options, (name, key)
            else:
                assert spec.lo <= value <= spec.hi, (name, key)


def test_default_preset_is_empty():
    assert C.PRESETS[next(iter(C.PRESETS))] == {}


def test_every_preset_differs_from_the_default_in_exactly_the_keys_it_names():
    for name, preset in list(C.PRESETS.items())[1:]:
        assert preset, name
        for key, value in preset.items():
            assert value != P.SETTING_SPECS[P.PRESET_KEYS[key]].default, (name, key)


def test_presets_sind_paarweise_verschieden():
    namen = list(C.PRESETS)
    for i, a in enumerate(namen):
        for b in namen[i + 1:]:
            assert C.PRESETS[a] != C.PRESETS[b], (a, b)


def test_setting_specs_cover_every_preset_key_and_url_params_are_unique():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    params = [s.url_param for s in P.SETTING_SPECS.values()]
    assert len(params) == len(set(params))


def test_permalink_bereinigung_begrenzt_und_verwirft_ungueltiges():
    assert P._bereinige(P.SETTING_SPECS["n_slider"], 999) == C.N_MAX
    assert P._bereinige(P.SETTING_SPECS["n_slider"], -5) == C.N_MIN
    assert P._bereinige(P.SETTING_SPECS["budget_select"], 5000) == 5000
    assert P._bereinige(P.SETTING_SPECS["budget_select"], 12345) is None
    assert P._bereinige(P.SETTING_SPECS["familie_select"], "x") is None
    assert P._bereinige(P.SETTING_SPECS["regel_select"], "zufall") == "zufall"
    assert P._bereinige(P.SETTING_SPECS["gesperrt_multi"], "7,3") == [3, 7]
    assert P._bereinige(P.SETTING_SPECS["gesperrt_multi"], "3,99") is None
    assert P._bereinige(P.SETTING_SPECS["gesperrt_multi"], "a") is None
    assert P._bereinige(P.SETTING_SPECS["gesperrt_multi"], "") == []


def test_standardwerte_liegen_in_den_grenzen_und_optionen():
    assert C.N_MIN <= C.DEFAULT_N <= C.N_MAX and C.GRENZE_MIN <= C.DEFAULT_GRENZE <= C.GRENZE_MAX and C.LIVE_N_MIN <= C.DEFAULT_LIVE_N <= C.LIVE_N_MAX
    assert C.LIVE_F_MIN <= C.DEFAULT_LIVE_F <= C.LIVE_F_MAX and 0 <= C.DEFAULT_SEED <= C.SEED_MAX
    assert C.DEFAULT_BUDGET in C.BUDGET_OPTIONEN and C.DEFAULT_ABSTAND in C.ABSTAND_OPTIONEN and C.DEFAULT_ANTEIL in C.ANTEIL_OPTIONEN
    assert C.DEFAULT_REGEL in C.REGELN and C.DEFAULT_FAMILIE in C.FAMILIEN and set(C.DEFAULT_GESPERRT) <= set(C.GESPERRT_OPTIONEN)
    assert C.REGEL_ABSTAND in C.ABSTAND_OPTIONEN


def test_normierung_der_mehrfachauswahl():
    assert P.normiert([7, 3]) == P.normiert((3, 7)) == (3, 7) and P.normiert("lbd") == "lbd"
