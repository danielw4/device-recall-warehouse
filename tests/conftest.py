from pathlib import Path

import duckdb
import pytest


@pytest.fixture(scope="session")
def warehouse():
    path = Path("data/warehouse.duckdb")
    if not path.exists():
        pytest.skip("data/warehouse.duckdb is absent; run `make load sql` for real-data tests")
    connection = duckdb.connect(path, read_only=True)
    yield connection
    connection.close()
