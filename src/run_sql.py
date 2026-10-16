"""Run the SQL models in filename order."""

from pathlib import Path

import duckdb


def main() -> None:
    database = Path("data/warehouse.duckdb")
    if not database.exists():
        raise FileNotFoundError(f"missing {database}; run `make load`")

    sql_files = sorted(Path("sql").glob("*.sql"))
    if not sql_files:
        raise RuntimeError("no SQL models found")

    with duckdb.connect(database) as connection:
        for sql_file in sql_files:
            connection.execute(sql_file.read_text(encoding="utf-8"))
            table = sql_file.stem.split("_", 1)[1]
            count = connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            print(f"{table}: {count:,} rows")
            if table == "mart_process_control_pchart":
                mixed = connection.execute(
                    """
                    SELECT count(*)
                    FROM (
                        SELECT res_event_number
                        FROM stg_recalls
                        GROUP BY res_event_number
                        HAVING count(event_date_initiated) > 0
                           AND count(DISTINCT nullif(trim(root_cause_description), '')) > 1
                    )
                    """
                ).fetchone()[0]
                print(f"recall events with multiple root causes: {mixed:,}")


if __name__ == "__main__":
    main()
