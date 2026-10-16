import math
from pathlib import Path

import duckdb
import pytest


def test_hand_computed_pchart_and_mode_tie_break():
    connection = duckdb.connect()
    connection.execute(
        """
        CREATE TABLE stg_recalls(
            res_event_number VARCHAR,
            event_date_initiated DATE,
            root_cause_description VARCHAR
        );
        INSERT INTO stg_recalls VALUES
            ('jan-process', '2010-01-05', 'Process control'),
            ('jan-other', '2010-01-06', 'Other'),
            ('jan-tie', '2010-01-07', 'Process control'),
            ('jan-tie', '2010-01-07', 'Device Design'),
            ('jan-design', '2010-01-08', 'Device Design'),
            ('feb-process', '2010-02-05', 'Process control'),
            ('feb-process', '2010-02-05', 'Process control'),
            ('feb-design', '2010-02-06', 'Device Design'),
            ('mar-design', '2010-03-05', 'Device Design'),
            ('mar-unknown', '2010-03-06', 'Unknown/Undetermined by firm'),
            ('partial', '2010-04-05', 'Process control');
        """
    )
    connection.execute(Path("sql/11_mart_process_control_pchart.sql").read_text())
    actual = connection.execute(
        """
        SELECT n_events, process_control_events, p, p_bar, ucl, lcl
        FROM mart_process_control_pchart
        ORDER BY month
        """
    ).fetchall()

    assert [(row[0], row[1]) for row in actual] == [(3, 1), (2, 1), (1, 0)]
    p_bar = 2 / 6
    expected_p = [1 / 3, 1 / 2, 0]
    for row, n_events, p in zip(actual, [3, 2, 1], expected_p):
        sigma = math.sqrt(p_bar * (1 - p_bar) / n_events)
        assert row[2] == pytest.approx(p)
        assert row[3] == pytest.approx(p_bar)
        assert row[4] == pytest.approx(p_bar + 3 * sigma)
        assert row[5] == pytest.approx(max(0, p_bar - 3 * sigma))


def test_eighth_month_on_same_side_triggers_run_rule():
    connection = duckdb.connect()
    connection.execute(
        """
        CREATE TABLE stg_recalls(
            res_event_number VARCHAR,
            event_date_initiated DATE,
            root_cause_description VARCHAR
        );
        INSERT INTO stg_recalls
        SELECT 'process-' || month, make_date(2010, month, 15), 'Process control'
        FROM range(1, 9) AS months(month);
        INSERT INTO stg_recalls
        SELECT 'design-' || event, DATE '2010-09-15', 'Device Design'
        FROM range(20) AS events(event);
        INSERT INTO stg_recalls VALUES ('partial', '2010-10-15', 'Other');
        """
    )
    connection.execute(Path("sql/11_mart_process_control_pchart.sql").read_text())
    july, august = connection.execute(
        """
        SELECT run_rule
        FROM mart_process_control_pchart
        WHERE month IN (DATE '2010-07-01', DATE '2010-08-01')
        ORDER BY month
        """
    ).fetchall()

    assert july[0] is False
    assert august[0] is True


def test_real_pchart_invariants(warehouse):
    process_control_events, n_events, p_bar = warehouse.execute(
        """
        SELECT sum(process_control_events), sum(n_events), min(p_bar)
        FROM mart_process_control_pchart
        """
    ).fetchone()
    assert process_control_events / n_events == pytest.approx(p_bar)

    invalid_limits = warehouse.execute(
        """
        SELECT count(*)
        FROM mart_process_control_pchart
        WHERE lcl < 0 OR lcl > p_bar OR p_bar > ucl
        """
    ).fetchone()[0]
    assert invalid_limits == 0

    months_after_window = warehouse.execute(
        """
        SELECT count(*)
        FROM mart_process_control_pchart
        WHERE month >= (
            SELECT date_trunc('month', max(event_date_initiated)) FROM stg_recalls
        )
        """
    ).fetchone()[0]
    assert months_after_window == 0
