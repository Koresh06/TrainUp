from decimal import Decimal

import pytest

from src.presentation.telegram.features.progress.validaters import parse_measurement


def test_positional_and_skip() -> None:
    assert parse_measurement("72,5") == {"weight": Decimal("72.5"), "waist": None, "chest": None, "hips": None}
    assert parse_measurement("- 80 95") == {
        "weight": None, "waist": Decimal("80.0"), "chest": Decimal("95.0"), "hips": None,
    }


def test_keywords() -> None:
    assert parse_measurement("Талия 80 вес 71")["waist"] == Decimal("80.0")
    assert parse_measurement("бёдра 98")["hips"] == Decimal("98.0")


@pytest.mark.parametrize("text", ["", "-", "720", "1 2 3 4 5", "рост 180", "талия"])
def test_errors(text: str) -> None:
    with pytest.raises(ValueError):
        parse_measurement(text)
