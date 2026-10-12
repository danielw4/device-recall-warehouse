from pathlib import Path

import duckdb
import numpy as np
from lifelines import KaplanMeierFitter


def test_sql_km_matches_lifelines(warehouse):
    subjects = warehouse.execute(
        "SELECT clearance_type, duration_days, recalled FROM mart_clearance_survival"
    ).fetchdf()
    curves = warehouse.execute(
        "SELECT clearance_type, duration_days, survival_probability FROM mart_km_curves"
    ).fetchdf()
    for clearance_type, curve in curves.groupby("clearance_type"):
        group = subjects[subjects["clearance_type"] == clearance_type]
        fitted = KaplanMeierFitter().fit(group["duration_days"], group["recalled"])
        expected = fitted.predict(curve["duration_days"]).to_numpy()
        assert np.allclose(curve["survival_probability"], expected, atol=1e-9, rtol=0)


def test_six_row_hand_computed_km_fixture():
    connection = duckdb.connect()
    connection.execute(
        """
        CREATE TABLE mart_clearance_survival(
            clearance_type VARCHAR, duration_days INTEGER, recalled INTEGER
        );
        INSERT INTO mart_clearance_survival VALUES
            ('Traditional', 1, 1),
            ('Traditional', 2, 0),
            ('Traditional', 2, 1),
            ('Traditional', 3, 1),
            ('Traditional', 4, 0),
            ('Traditional', 4, 1);
        """
    )
    connection.execute(Path("sql/09_mart_km_curves.sql").read_text())
    actual = connection.execute(
        "SELECT duration_days, survival_probability FROM mart_km_curves ORDER BY duration_days"
    ).fetchall()
    expected = [(1, 5 / 6), (2, 2 / 3), (3, 4 / 9), (4, 2 / 9)]
    assert [row[0] for row in actual] == [row[0] for row in expected]
    assert np.allclose([row[1] for row in actual], [row[1] for row in expected], atol=1e-12)
