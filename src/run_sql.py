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


if __name__ == "__main__":
    main()
