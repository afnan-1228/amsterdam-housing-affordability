"""Affordability metrics for Amsterdam districts."""

from __future__ import annotations

import pandas as pd

# UvA PhD salary (vacancy 15626, 2026): EUR 3,200 gross per month (rounded from the vacancy),
# plus 8% holiday allowance and 8.3% year-end allowance.
PHD_MONTHLY_GROSS_EUR = 3200
PHD_ANNUAL_GROSS_EUR = PHD_MONTHLY_GROSS_EUR * 12 * (1 + 0.08 + 0.083)


def add_affordability(df: pd.DataFrame) -> pd.DataFrame:
    """Add the price-to-income ratio and 'years of PhD salary' for each district.

    price_to_income  = average home value / average income per income recipient
                       (how many years of a typical local income a typical home costs;
                       higher = less affordable)
    years_phd_salary = average home value / first-year UvA PhD gross salary
    """
    out = df.dropna(subset=["home_value", "income"]).copy()
    out = out[(out["home_value"] > 0) & (out["income"] > 0)]
    # Both CBS figures are in thousands of euros, so the ratio needs no conversion.
    out["price_to_income"] = out["home_value"] / out["income"]
    out["years_phd_salary"] = out["home_value"] * 1000 / PHD_ANNUAL_GROSS_EUR
    out["rank_most_affordable"] = out["price_to_income"].rank(method="min").astype(int)
    return out.sort_values("price_to_income").reset_index(drop=True)


def summarise(df: pd.DataFrame, city: pd.Series, year: int) -> str:
    """Write the key findings as Markdown."""
    most = df.nsmallest(3, "price_to_income")
    least = df.nlargest(3, "price_to_income")
    city_ratio = city["home_value"] / city["income"]
    corr = df["income"].corr(df["home_value"])
    above = int((df["price_to_income"] > city_ratio).sum())

    def rows(sub):
        return "\n".join(
            f"| {r.name} | {r.home_value * 1000:,.0f} | {r.income * 1000:,.0f} | "
            f"{r.price_to_income:.1f} | {r.years_phd_salary:.1f} |"
            for r in sub.itertuples()
        )

    header = (
        "| District | Avg. home value (EUR) | Avg. income (EUR/yr) | "
        "Price-to-income | Years of PhD salary |\n|---|---|---|---|---|"
    )
    return f"""# Results ({year} data, {len(df)} Amsterdam districts)

- Amsterdam as a whole: average home value EUR {city['home_value'] * 1000:,.0f}, \
average income EUR {city['income'] * 1000:,.0f} per income recipient, \
price-to-income ratio **{city_ratio:.1f}**.
- {above} of {len(df)} districts are less affordable than the city average.
- Correlation between district income and home value: **{corr:.2f}**.
- A first-year UvA PhD candidate earns about EUR {PHD_ANNUAL_GROSS_EUR:,.0f} gross per year \
(including allowances).

## Most affordable districts
{header}
{rows(most)}

## Least affordable districts
{header}
{rows(least)}
"""
