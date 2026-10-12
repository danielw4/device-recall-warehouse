from pathlib import Path

import duckdb


def test_malformed_date_and_k_number_explosion():
    connection = duckdb.connect()
    connection.execute("CREATE SCHEMA raw")
    connection.execute(
        """
        CREATE TABLE raw.recall AS
        SELECT
            '1'::VARCHAR AS cfres_id,
            '10'::VARCHAR AS res_event_number,
            'ABC'::VARCHAR AS product_code,
            '10-08-17'::VARCHAR AS event_date_initiated,
            '2020-01-02'::VARCHAR AS event_date_posted,
            NULL::VARCHAR AS event_date_terminated,
            ['K000001', 'K000002', 'K000003']::VARCHAR[] AS k_numbers
        """
    )
    for filename in ("01_stg_recalls.sql", "02_stg_recall_k_numbers.sql"):
        connection.execute(Path("sql", filename).read_text())
    assert connection.execute("SELECT event_date_initiated FROM stg_recalls").fetchone()[0] is None
    assert connection.execute("SELECT count(*) FROM stg_recall_k_numbers").fetchone()[0] == 3
