"""Build the static figures used to inspect the marts."""

import os
from pathlib import Path

import duckdb

matplotlib_config = Path("data/.matplotlib").resolve()
matplotlib_config.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_config))

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt


def save(figure: plt.Figure, path: Path) -> None:
    figure.tight_layout()
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    print(f"wrote {path}")


def main() -> None:
    output_dir = Path("reports/figures")
    output_dir.mkdir(parents=True, exist_ok=True)
    with duckdb.connect("data/warehouse.duckdb", read_only=True) as connection:
        km = connection.execute(
            "SELECT * FROM mart_km_curves ORDER BY clearance_type, duration_days"
        ).fetchdf()
        specialty = connection.execute(
            """
            SELECT level || ' (n=' || cleared_count || ')' AS level, recall_percentage
            FROM mart_recall_rate_kpis
            -- Specialties with few clearances give unstable percentages.
            WHERE dimension = 'specialty' AND cleared_count >= 500 AND level <> 'Unknown'
            ORDER BY recall_percentage
            """
        ).fetchdf()
        causes = connection.execute(
            """
            WITH top_causes AS (
                SELECT root_cause_description
                FROM mart_root_cause_trends
                WHERE recall_year BETWEEN 2008 AND 2025
                GROUP BY root_cause_description
                ORDER BY sum(recall_products) DESC
                LIMIT 6
            )
            SELECT recall_year, root_cause_description, product_share_of_year
            FROM mart_root_cause_trends
            WHERE root_cause_description IN (SELECT root_cause_description FROM top_causes)
              -- Root causes were rarely coded before 2008, and 2026 is a partial year.
              AND recall_year BETWEEN 2008 AND 2025
            ORDER BY recall_year, root_cause_description
            """
        ).fetchdf()
        pchart = connection.execute(
            "SELECT * FROM mart_process_control_pchart ORDER BY month"
        ).fetchdf()

    figure, axis = plt.subplots(figsize=(8, 5))
    for clearance_type, group in km.groupby("clearance_type", sort=True):
        axis.step(
            group["duration_days"] / 365.25,
            100 * (1 - group["survival_probability"]),
            where="post",
            label=clearance_type,
        )
    axis.set(xlabel="Years since clearance", ylabel="Cumulative share named in a recall (%)", ylim=(0, 25))
    axis.legend(title="Clearance type", frameon=False)
    save(figure, output_dir / "km_by_clearance_type.png")

    height = max(5, 0.34 * len(specialty))
    figure, axis = plt.subplots(figsize=(9, height))
    bars = axis.barh(specialty["level"], specialty["recall_percentage"], color="#4c78a8")
    axis.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=8)
    axis.set(xlabel="Clearances later named in a recall (%)", ylabel="Medical specialty")
    axis.margins(x=0.12)
    save(figure, output_dir / "recall_percentage_by_specialty.png")

    figure, axis = plt.subplots(figsize=(10, 6))
    for cause, group in causes.groupby("root_cause_description", sort=True):
        axis.plot(group["recall_year"], 100 * group["product_share_of_year"], label=cause)
    axis.set(xlabel="Recall year", ylabel="Share of recall products (%)", xticks=range(2008, 2026, 2))
    axis.legend(title="Root cause", frameon=False, fontsize=8)
    save(figure, output_dir / "root_cause_share_over_time.png")

    figure, axis = plt.subplots(figsize=(11, 6))
    axis.plot(
        pchart["month"],
        100 * pchart["p"],
        color="#4c78a8",
        marker="o",
        markersize=3,
        linewidth=1,
        label="Monthly share",
    )
    axis.axhline(100 * pchart["p_bar"].iloc[0], color="#555555", label="Center line")
    axis.step(pchart["month"], 100 * pchart["ucl"], where="post", color="#f58518", label="3-sigma control limits")
    axis.step(pchart["month"], 100 * pchart["lcl"], where="post", color="#f58518", label="_nolegend_")
    signals = pchart[pchart["out_of_control"]]
    axis.scatter(
        signals["month"],
        100 * signals["p"],
        color="#e45756",
        marker="X",
        s=45,
        label="Out of control",
        zorder=3,
    )
    axis.set(xlabel="Recall event month", ylabel="Process control recall events (%)")
    axis.xaxis.set_major_locator(mdates.YearLocator(2))
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axis.legend(frameon=False, ncol=3)
    save(figure, output_dir / "process_control_pchart.png")


if __name__ == "__main__":
    main()
