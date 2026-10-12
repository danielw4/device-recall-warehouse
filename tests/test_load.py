import ijson


EXPECTED = {
    "recall": ("data/raw/device-recall.json.zip", 59_344),
    "k510": ("data/raw/device-510k.json.zip", 176_223),
    "classification": ("data/raw/device-classification.json.zip", 7_094),
}


def test_raw_counts_match_archive_metadata_and_frozen_totals(warehouse):
    import zipfile

    for table, (path, expected) in EXPECTED.items():
        with zipfile.ZipFile(path) as archive, archive.open(archive.namelist()[0]) as source:
            metadata_total = int(next(ijson.items(source, "meta.results.total")))
        loaded = warehouse.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0]
        assert metadata_total == expected
        assert loaded == metadata_total
