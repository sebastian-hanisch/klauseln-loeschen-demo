"""Die drei kopierten Kern-Module (klo_rng, klo_instanzen, klo_cdcl) sind bis auf zwei Kopfzeilen und die Importe wörtlich dem Kern-Paket gleich,
und ihre Regressionswerte stimmen (SplitMix64 gegen die veröffentlichten Werte, Schubfach h = 4 / 5 / 6 mit 28 / 159 / 1 004 Konflikten laut Kern-README).
Der Vergleich mit dem Kern-Paket läuft nur, wenn `sat-cp-planung/kern/` neben dem Repo liegt; die Regressionswerte laufen immer."""
import re
from pathlib import Path

import pytest

import klo_cdcl as K
import klo_instanzen as I
from klo_rng import SplitMix64

ROOT = Path(__file__).resolve().parent.parent
KERN = ROOT.parent / "sat-cp-planung" / "kern"
MODULE = ("rng", "instanzen", "cdcl")


def _normal(text: str) -> str:
    return text.replace("\r\n", "\n")


@pytest.mark.parametrize("modul", MODULE)
def test_kopf_nennt_herkunft_und_kern_version(modul):
    text = (ROOT / f"klo_{modul}.py").read_text(encoding="utf-8")
    zeilen = text.splitlines()
    assert zeilen[0].startswith(f"# Kopie von sat-cp-planung/kern/{modul}.py, Kern-Version ")
    assert re.fullmatch(r"[0-9a-f]{16}", re.search(r"Kern-Version ([0-9a-f]+) ", zeilen[0]).group(1))
    assert "Nur die Importe" in zeilen[1]


@pytest.mark.parametrize("modul", MODULE)
def test_kopie_ist_bis_auf_kopf_und_importe_der_kern(modul):
    if not (KERN / f"{modul}.py").exists():
        pytest.skip("Kern-Paket liegt nicht neben dem Repo")
    kopie = _normal((ROOT / f"klo_{modul}.py").read_text(encoding="utf-8")).split("\n", 2)[2]
    kern = _normal((KERN / f"{modul}.py").read_text(encoding="utf-8"))
    assert kopie.replace("from klo_rng import", "from rng import") == kern


@pytest.mark.parametrize("modul", MODULE)
def test_kern_version_gleich_hashes_datei(modul):
    hashes = KERN / "HASHES.txt"
    if not hashes.exists():
        pytest.skip("Kern-Paket liegt nicht neben dem Repo")
    erwartet = dict(reversed(z.split()) for z in hashes.read_text(encoding="utf-8").splitlines() if z.strip())[f"{modul}.py"]
    assert f"Kern-Version {erwartet} " in (ROOT / f"klo_{modul}.py").read_text(encoding="utf-8").splitlines()[0]


def test_keine_importe_aus_anderen_demos_oder_dem_kern():
    for pfad in ROOT.glob("*.py"):
        for zeile in pfad.read_text(encoding="utf-8").splitlines():
            if zeile.startswith(("import ", "from ")):
                assert not re.match(r"(import|from) (rng|instanzen|cdcl|dpll|rup)\b", zeile), f"{pfad.name}: {zeile}"


def test_splitmix64_bekannte_werte():
    g = SplitMix64(0)
    assert [g.next() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]
    assert SplitMix64(12345).next() == 2454886589211414944


def test_schubfach_konflikte_wie_im_kern():
    assert [K.solve(*I.pigeonhole(h)[:2]).stat["konflikte"] for h in (4, 5, 6)] == [28, 159, 1004]
