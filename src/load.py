"""Stream openFDA bulk JSON to NDJSON, then load it into DuckDB."""

import json
import zipfile
from pathlib import Path

import duckdb
import ijson


FILES = {
    "recall": ("device-recall.json.zip", "recall.ndjson"),
    "k510": ("device-510k.json.zip", "510k.ndjson"),
    "classification": ("device-classification.json.zip", "classification.ndjson"),
}


def archive_total(archive: Path) -> int:
    with zipfile.ZipFile(archive) as zipped:
        members = zipped.namelist()
        if len(members) != 1:
            raise RuntimeError(f"expected one JSON file in {archive}, found {len(members)}")
        with zipped.open(members[0]) as source:
            return int(next(ijson.items(source, "meta.results.total")))


def stream_results(archive: Path, destination: Path) -> None:
    if destination.exists() and destination.stat().st_mtime >= archive.stat().st_mtime:
        print(f"skip {destination} (up to date)")
        return
    temporary = destination.with_suffix(destination.suffix + ".part")
    count = 0
    with zipfile.ZipFile(archive) as zipped, zipped.open(zipped.namelist()[0]) as source:
        with temporary.open("w", encoding="utf-8") as output:
            for record in ijson.items(source, "results.item"):
                output.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
                output.write("\n")
                count += 1
    temporary.replace(destination)
    print(f"streamed {count:,} rows to {destination}")


def main() -> None:
    raw_dir = Path("data/raw")
    database = Path("data/warehouse.duckdb")
    database.parent.mkdir(parents=True, exist_ok=True)

    totals = {}
    for table, (archive_name, ndjson_name) in FILES.items():
        archive = raw_dir / archive_name
        if not archive.exists():
            raise FileNotFoundError(f"missing {archive}; run `make fetch`")
        destination = raw_dir / ndjson_name
        totals[table] = archive_total(archive)
        stream_results(archive, destination)

    with duckdb.connect(database) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
        for table, (_, ndjson_name) in FILES.items():
            path = str((raw_dir / ndjson_name).resolve()).replace("'", "''")
            connection.execute(
                f"""
                CREATE OR REPLACE TABLE raw.{table} AS
                SELECT * FROM read_json_auto(
                    '{path}',
                    format = 'newline_delimited',
                    records = true,
                    sample_size = -1,
                    union_by_name = true,
                    -- Keep dates as source text so staging can reject malformed values.
                    dateformat = '%Y/%m/%d',
                    maximum_object_size = 268435456
                )
                """
            )
            loaded = connection.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0]
            if loaded != totals[table]:
                raise RuntimeError(
                    f"raw.{table}: loaded {loaded:,} rows, archive metadata says {totals[table]:,}"
                )
            print(f"raw.{table}: {loaded:,} rows (matches metadata)")


if __name__ == "__main__":
    main()
