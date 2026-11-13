"""Download and clean CBS neighbourhood data for Amsterdam.

Data source: Statistics Netherlands (CBS), StatLine tables
"Kerncijfers wijken en buurten <year>" (key figures for districts and
neighbourhoods), downloaded through the open-data API with `cbsodata`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

AMSTERDAM = "Amsterdam"
TITLE_PATTERN = re.compile(r"^Kerncijfers wijken en buurten (\d{4})$")

# CBS column names end with a number that changes between years
# (e.g. "Gemeentenaam_1" in one year, "Gemeentenaam_2" in another),
# so we look columns up by their stable prefix.
COLUMN_PREFIXES = {
    "name": "WijkenEnBuurten",
    "municipality": "Gemeentenaam",
    "region_type": "SoortRegio",
    "code": "Codering",
    "residents": "AantalInwoners",
    "home_value": "GemiddeldeWOZWaardeVanWoningen",  # x 1,000 euro
    "income": "GemiddeldInkomenPerInkomensontvanger",  # x 1,000 euro per year
}

RAW_DIR = Path("data/raw")


def find_kwb_tables() -> dict[int, str]:
    """Return {year: table_id} for every 'Kerncijfers wijken en buurten' table, newest first."""
    import cbsodata

    found = {}
    for table in cbsodata.get_table_list():
        match = TITLE_PATTERN.match(str(table.get("Title", "")).strip())
        if match:
            found[int(match.group(1))] = table["Identifier"]
    return dict(sorted(found.items(), reverse=True))


def download_table(table_id: str, refresh: bool = False) -> pd.DataFrame:
    """Download one CBS table (or read the cached copy in data/raw/)."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache = RAW_DIR / f"{table_id}.csv"
    if cache.exists() and not refresh:
        return pd.read_csv(cache, low_memory=False)

    import cbsodata

    print(f"Downloading CBS table {table_id} (this can take a minute)...")
    df = pd.DataFrame(cbsodata.get_data(table_id))
    df.to_csv(cache, index=False)
    return df


def find_column(columns, prefix: str) -> str:
    """Find the CBS column whose name is `prefix` or `prefix_<number>`."""
    pattern = re.compile(rf"^{re.escape(prefix)}(_\d+)?$")
    matches = [c for c in columns if pattern.match(c)]
    if len(matches) == 1:
        return matches[0]
    hint = [c for c in columns if prefix[:12].lower() in c.lower()]
    raise KeyError(
        f"Expected one column for '{prefix}', found {matches}. "
        f"Similar columns: {hint[:10]}"
    )


def clean_amsterdam(raw: pd.DataFrame, level: str = "Wijk") -> pd.DataFrame:
    """Keep Amsterdam districts ('Wijk') or neighbourhoods ('Buurt') with tidy English columns."""
    columns = {key: find_column(raw.columns, prefix) for key, prefix in COLUMN_PREFIXES.items()}
    df = raw[list(columns.values())].rename(columns={v: k for k, v in columns.items()})

    # CBS pads text with spaces ("Wijk      "), so strip it.
    for col in ["name", "municipality", "region_type", "code"]:
        df[col] = df[col].astype(str).str.strip()

    df = df[(df["municipality"] == AMSTERDAM) & (df["region_type"] == level)].copy()

    for col in ["residents", "home_value", "income"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.reset_index(drop=True)


def city_reference(raw: pd.DataFrame) -> pd.Series:
    """The row for Amsterdam as a whole (region type 'Gemeente'), used as a benchmark."""
    columns = {key: find_column(raw.columns, prefix) for key, prefix in COLUMN_PREFIXES.items()}
    df = raw[list(columns.values())].rename(columns={v: k for k, v in columns.items()})
    for col in ["municipality", "region_type"]:
        df[col] = df[col].astype(str).str.strip()
    row = df[(df["municipality"] == AMSTERDAM) & (df["region_type"] == "Gemeente")]
    if row.empty:
        raise ValueError("No city-level row for Amsterdam found.")
    row = row.iloc[0].copy()
    for col in ["residents", "home_value", "income"]:
        row[col] = pd.to_numeric(row[col], errors="coerce")
    return row


def coverage(df: pd.DataFrame) -> float:
    """Share of districts that have both a home value and an income figure."""
    if df.empty:
        return 0.0
    return float(df[["home_value", "income"]].notna().all(axis=1).mean())
