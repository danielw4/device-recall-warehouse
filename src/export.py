"""Export analysis marts and the data-quality report as CSV files."""

from pathlib import Path

import duckdb


TABLES = [
    "mart_clearance_survival",
    "mart_recall_rate_kpis",
    "mart_root_cause_trends",
    "mart_km_curves",
    "mart_process_control_pchart",
    "dq_report",
]


def main() -> None:
    output_dir = Path("exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    with duckdb.connect("data/warehouse.duckdb", read_only=True) as connection:
        for table in TABLES:
            destination = (output_dir / f"{table}.csv").resolve()
            escaped = str(destination).replace("'", "''")
            connection.execute(f"COPY {table} TO '{escaped}' (HEADER, DELIMITER ',')")
            count = connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            print(f"{destination}: {count:,} rows")


if __name__ == "__main__":
    main()
