"""Gemeinsame Fixtures: die Handtabelle (Plan Stück 5, von Hand gerechnet) und ein kleiner Löser-Hilfsaufbau."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import klo_scenario as S  # noqa: E402


@pytest.fixture
def hand():
    """Handtabelle: LBD [2, 3, 4, 2, 4, 4, 4, 5], Längen [2, 3, 4, 3, 5, 5, 4, 6], gesperrt 3 und 7, Kandidaten [2, 5, 6, 8],
    Rangfolge [8, 5, 6, 2], es fallen 8 und 5, es bleiben [1, 2, 3, 4, 6, 7]."""
    return S.hand_runde()
