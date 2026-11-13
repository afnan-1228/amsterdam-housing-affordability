"""District boundaries from PDOK (the Dutch government map service)."""

from __future__ import annotations

import requests

PDOK_URL = "https://api.pdok.nl/cbs/wijken-en-buurten-{year}/ogc/v1/collections/wijken/items"
AMSTERDAM_CODE = "GM0363"


def load_district_shapes(year: int):
    """Download Amsterdam district shapes as a GeoDataFrame.

    Returns None (and the map is skipped) if the service is unavailable,
    so the rest of the analysis still runs.
    """
    import geopandas as gpd

    url = PDOK_URL.format(year=year)
    params = {"f": "json", "gemeentecode": AMSTERDAM_CODE, "limit": 1000}
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        gdf = gpd.GeoDataFrame.from_features(response.json()["features"], crs="EPSG:4326")
    except Exception as err:  # network, format or year not available
        print(f"Map skipped: could not load district shapes ({err}).")
        return None

    if "gemeentecode" in gdf.columns:
        gdf = gdf[gdf["gemeentecode"] == AMSTERDAM_CODE]
    if gdf.empty or "wijkcode" not in gdf.columns:
        print("Map skipped: no Amsterdam districts found in the PDOK response.")
        return None
    return gdf
