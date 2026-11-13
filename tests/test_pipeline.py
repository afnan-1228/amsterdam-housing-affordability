"""Tests on a tiny fake table shaped like the real CBS download."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from amsterdam_housing import analysis, data  # noqa: E402


@pytest.fixture
def raw():
    # Same column naming as CBS: stable prefix + changing number, padded text.
    return pd.DataFrame({
        "ID": [0, 1, 2, 3, 4],
        "WijkenEnBuurten": ["Amsterdam", "Centrum-West", "Noord-Oost", "Ommen", "Zuid-Leeg"],
        "Gemeentenaam_1": ["Amsterdam ", "Amsterdam ", "Amsterdam ", "Ommen ", "Amsterdam "],
        "SoortRegio_2": ["Gemeente  ", "Wijk      ", "Wijk      ", "Wijk      ", "Wijk      "],
        "Codering_3": ["GM0363    ", "WK036300  ", "WK036370  ", "WK017500  ", "WK036399  "],
        "AantalInwoners_5": [930000, 25000, 40000, 5000, 100],
        "GemiddeldeWOZWaardeVanWoningen_35": [520.0, 700.0, 350.0, 300.0, None],
        "GemiddeldInkomenPerInkomensontvanger_67": [45.0, 56.0, 35.0, 40.0, None],
    })


def test_find_column_ignores_number_suffix(raw):
    assert data.find_column(raw.columns, "Gemeentenaam") == "Gemeentenaam_1"


def test_find_column_reports_missing(raw):
    with pytest.raises(KeyError):
        data.find_column(raw.columns, "Onbestaand")


def test_clean_keeps_only_amsterdam_districts(raw):
    df = data.clean_amsterdam(raw)
    assert list(df["code"]) == ["WK036300", "WK036370", "WK036399"]
    assert data.coverage(df) == pytest.approx(2 / 3)


def test_affordability_ratio_and_ranking(raw):
    result = analysis.add_affordability(data.clean_amsterdam(raw))
    assert len(result) == 2  # district without data is dropped
    assert result.loc[0, "name"] == "Noord-Oost"  # most affordable first
    assert result.loc[0, "price_to_income"] == pytest.approx(10.0)
    assert result.loc[1, "price_to_income"] == pytest.approx(12.5)
    assert result.loc[0, "years_phd_salary"] == pytest.approx(
        350_000 / analysis.PHD_ANNUAL_GROSS_EUR)


def test_city_reference(raw):
    city = data.city_reference(raw)
    assert city["home_value"] / city["income"] == pytest.approx(520 / 45)


def test_summary_mentions_key_numbers(raw):
    result = analysis.add_affordability(data.clean_amsterdam(raw))
    text = analysis.summarise(result, data.city_reference(raw), 2024)
    assert "Noord-Oost" in text and "11.6" in text
