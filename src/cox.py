"""Fit the prespecified Cox proportional-hazards model."""

from contextlib import redirect_stdout
from pathlib import Path

import duckdb
import pandas as pd
from lifelines import CoxPHFitter


def main() -> None:
    database = Path("data/warehouse.duckdb")
    reports = Path("reports")
    reports.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(database, read_only=True) as connection:
        data = connection.execute(
            """
            SELECT duration_days, recalled, clearance_type, device_class,
                   decision_year, specialty
            FROM mart_clearance_survival
            """
        ).fetchdf()

    before = len(data)
    data["device_class"] = pd.to_numeric(data["device_class"], errors="coerce")
    data = data.dropna(
        subset=["duration_days", "recalled", "clearance_type", "device_class", "decision_year", "specialty"]
    ).copy()
    dropped = before - len(data)
    print(f"Cox model: dropped {dropped:,} of {before:,} rows with missing covariates")

    data["clearance_type"] = pd.Categorical(
        data["clearance_type"], categories=["Traditional", "Special", "Abbreviated"]
    )
    dummies = pd.get_dummies(data["clearance_type"], prefix="clearance_type", drop_first=True, dtype=float)
    model_data = pd.concat(
        [
            data[["duration_days", "recalled", "device_class", "decision_year", "specialty"]],
            dummies,
        ],
        axis=1,
    )

    model = CoxPHFitter()
    model.fit(model_data, duration_col="duration_days", event_col="recalled", strata=["specialty"])

    summary = model.summary.reset_index().rename(columns={"covariate": "term"})
    summary = summary[["term", "exp(coef)", "exp(coef) lower 95%", "exp(coef) upper 95%", "p"]]
    summary.columns = ["term", "hazard_ratio", "ci_lower_95", "ci_upper_95", "p_value"]
    summary.to_csv(reports / "cox_summary.csv", index=False)

    with (reports / "cox_summary.md").open("w", encoding="utf-8") as output:
        output.write("# Cox proportional-hazards model\n\n")
        output.write(f"Rows used: {len(model_data):,}; rows dropped for missing covariates: {dropped:,}.\n\n")
        output.write("| Term | Hazard ratio | 95% CI | p-value |\n")
        output.write("|---|---:|---:|---:|\n")
        for row in summary.itertuples(index=False):
            output.write(
                f"| {row.term} | {row.hazard_ratio:.4f} | "
                f"{row.ci_lower_95:.4f}–{row.ci_upper_95:.4f} | {row.p_value:.4g} |\n"
            )

    ph_path = reports / "cox_ph_check.txt"
    with ph_path.open("w", encoding="utf-8") as output, redirect_stdout(output):
        print(f"Rows used: {len(model_data):,}")
        print(f"Rows dropped for missing covariates: {dropped:,}")
        model.check_assumptions(model_data, p_value_threshold=0.05, show_plots=False)
    print(f"wrote {reports / 'cox_summary.csv'}, {reports / 'cox_summary.md'}, and {ph_path}")


if __name__ == "__main__":
    main()
