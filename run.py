"""Run the full analysis: python run.py  (options: --year 2023, --refresh, --no-map)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from amsterdam_housing import analysis, data, geo, plots  # noqa: E402

MIN_COVERAGE = 0.8  # use the newest year where >= 80% of districts have both figures


def pick_year(tables: dict[int, str], forced: int | None, refresh: bool):
    """Return (year, raw table, cleaned districts) for the newest usable year."""
    years = [forced] if forced else list(tables)[:4]
    for year in years:
        raw = data.download_table(tables[year], refresh=refresh)
        districts = data.clean_amsterdam(raw)
        share = data.coverage(districts)
        print(f"{year}: {len(districts)} districts, {share:.0%} with home value and income")
        if share >= MIN_COVERAGE or forced:
            return year, raw, districts
    raise SystemExit("No recent year has enough income and home-value data.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, help="force a specific CBS year")
    parser.add_argument("--refresh", action="store_true", help="re-download CBS data")
    parser.add_argument("--no-map", action="store_true", help="skip the map")
    args = parser.parse_args()

    tables = data.find_kwb_tables()
    print("CBS tables found:", tables)
    year, raw, districts = pick_year(tables, args.year, args.refresh)

    city = data.city_reference(raw)
    city_ratio = city["home_value"] / city["income"]
    result = analysis.add_affordability(districts)

    Path("outputs").mkdir(exist_ok=True)
    result.to_csv("outputs/amsterdam_district_affordability.csv", index=False)
    summary = analysis.summarise(result, city, year)
    Path("outputs/summary.md").write_text(summary, encoding="utf-8")

    plots.top_bottom_bar(result, city_ratio, year)
    plots.income_vs_value(result, year)
    plots.phd_years(result, year)
    if not args.no_map:
        shapes = geo.load_district_shapes(year)
        if shapes is not None:
            plots.affordability_map(result, shapes, year)

    print("\n" + summary)
    print("Saved: outputs/ (CSV + summary.md) and figures/ (PNG charts)")


if __name__ == "__main__":
    main()
