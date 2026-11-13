"""Charts and map for the affordability analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

FIG_DIR = Path("figures")
LIGHT, DARK, ACCENT = "#9ecae1", "#08519c", "#d94801"


def _save(fig, name: str) -> Path:
    FIG_DIR.mkdir(exist_ok=True)
    path = FIG_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def top_bottom_bar(df: pd.DataFrame, city_ratio: float, year: int, n: int = 10) -> Path:
    """Horizontal bars: the n most and n least affordable districts."""
    sub = pd.concat([df.nsmallest(n, "price_to_income"), df.nlargest(n, "price_to_income")])
    sub = sub.drop_duplicates("code").sort_values("price_to_income")
    colors = [LIGHT if v <= city_ratio else DARK for v in sub["price_to_income"]]

    fig, ax = plt.subplots(figsize=(8, 0.35 * len(sub) + 1.5))
    ax.barh(sub["name"], sub["price_to_income"], color=colors)
    ax.axvline(city_ratio, color=ACCENT, linestyle="--", linewidth=1.5,
               label=f"Amsterdam average ({city_ratio:.1f})")
    ax.legend(loc="lower right", frameon=True, fontsize=9)
    ax.set_xlabel("Average home value ÷ average income (years of income)")
    ax.set_title(f"Most and least affordable Amsterdam districts ({year})", loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    return _save(fig, "top_bottom_districts.png")


def income_vs_value(df: pd.DataFrame, year: int, label_n: int = 3) -> Path:
    """Scatter: income against home value, bubble size = residents."""
    fig, ax = plt.subplots(figsize=(8, 6))
    size = 20 + 180 * df["residents"] / df["residents"].max()
    ax.scatter(df["income"] * 1000, df["home_value"] * 1000, s=size,
               color=DARK, alpha=0.55, edgecolor="white")
    extremes = pd.concat([df.nsmallest(label_n, "price_to_income"),
                          df.nlargest(label_n, "price_to_income")])
    for i, r in enumerate(extremes.drop_duplicates("code").itertuples()):
        offset = (6, 6) if i % 2 == 0 else (6, -12)  # alternate to reduce overlap
        ax.annotate(r.name, (r.income * 1000, r.home_value * 1000), fontsize=8,
                    xytext=offset, textcoords="offset points")
    ax.set_xlabel("Average income per income recipient (€ per year)")
    ax.set_ylabel("Average home value, WOZ (€)")
    ax.set_title(f"Income and home value by district, Amsterdam ({year})", loc="left")
    ax.xaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
    ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
    ax.spines[["top", "right"]].set_visible(False)
    return _save(fig, "income_vs_home_value.png")


def phd_years(df: pd.DataFrame, year: int, n: int = 10) -> Path:
    """How many years of a first-year PhD salary the average home costs."""
    sub = pd.concat([df.nsmallest(n // 2, "years_phd_salary"),
                     df.nlargest(n // 2, "years_phd_salary")]).sort_values("years_phd_salary")
    fig, ax = plt.subplots(figsize=(8, 0.4 * len(sub) + 1.5))
    ax.barh(sub["name"], sub["years_phd_salary"], color=ACCENT)
    for i, v in enumerate(sub["years_phd_salary"]):
        ax.text(v, i, f" {v:.1f}", va="center", fontsize=9)
    ax.set_xlabel("Years of gross first-year UvA PhD salary to equal the average home value")
    ax.set_title(f"What an Amsterdam home costs in PhD years ({year})", loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    return _save(fig, "phd_salary_years.png")


def affordability_map(df: pd.DataFrame, shapes, year: int) -> Path:
    """Choropleth map of price-to-income ratio per district."""
    gdf = shapes.merge(df, left_on="wijkcode", right_on="code", how="left")
    fig, ax = plt.subplots(figsize=(9, 8))
    gdf.plot(column="price_to_income", cmap="Blues", linewidth=0.3, edgecolor="white",
             legend=True, ax=ax,
             legend_kwds={"label": "Home value ÷ income", "shrink": 0.6},
             missing_kwds={"color": "#eeeeee", "label": "No data"})
    ax.set_axis_off()
    ax.set_title(f"Housing affordability by district, Amsterdam ({year})", loc="left")
    return _save(fig, "affordability_map.png")
