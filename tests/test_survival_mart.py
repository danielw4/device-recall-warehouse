def test_survival_mart_has_one_row_per_k_number(warehouse):
    rows, distinct_k = warehouse.execute(
        "SELECT count(*), count(DISTINCT k_number) FROM mart_clearance_survival"
    ).fetchone()
    assert rows == distinct_k


def test_survival_durations_are_bounded(warehouse):
    negative, beyond_censor = warehouse.execute(
        """
        SELECT
            count(*) FILTER (WHERE duration_days < 0),
            count(*) FILTER (
                WHERE duration_days > date_diff('day', decision_date, censor_date)
            )
        FROM mart_clearance_survival
        """
    ).fetchone()
    assert negative == 0
    assert beyond_censor == 0


def test_recalled_count_matches_independent_join(warehouse):
    mart_count = warehouse.execute(
        "SELECT sum(recalled) FROM mart_clearance_survival"
    ).fetchone()[0]
    independent_count = warehouse.execute(
        """
        WITH cohort AS (
            SELECT k_number, decision_date
            FROM stg_510k
            WHERE decision_code LIKE 'SE%'
              AND decision_date >= DATE '2003-01-01'
              AND clearance_type IN ('Traditional', 'Special', 'Abbreviated')
            QUALIFY row_number() OVER (PARTITION BY k_number ORDER BY decision_date) = 1
        )
        SELECT count(*)
        FROM cohort c
        WHERE EXISTS (
            SELECT 1
            FROM stg_recall_k_numbers r
            WHERE r.k_number = c.k_number
              AND r.event_date_initiated >= c.decision_date
        )
        """
    ).fetchone()[0]
    assert mart_count == independent_count


def test_cohort_filter_is_respected(warehouse):
    invalid = warehouse.execute(
        """
        WITH expected AS (
            SELECT k_number
            FROM stg_510k
            CROSS JOIN (SELECT max(event_date_initiated) AS censor_date FROM stg_recalls) x
            WHERE decision_code LIKE 'SE%'
              AND decision_date >= DATE '2003-01-01'
              AND decision_date <= x.censor_date
              AND clearance_type IN ('Traditional', 'Special', 'Abbreviated')
        ), differences AS (
            (SELECT k_number FROM mart_clearance_survival EXCEPT SELECT k_number FROM expected)
            UNION ALL
            (SELECT k_number FROM expected EXCEPT SELECT k_number FROM mart_clearance_survival)
        )
        SELECT count(*) FROM differences
        """
    ).fetchone()[0]
    assert invalid == 0
