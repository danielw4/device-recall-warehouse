CREATE OR REPLACE TABLE int_first_recall AS
WITH decisions AS (
    SELECT *
    FROM stg_510k
    QUALIFY row_number() OVER (PARTITION BY k_number ORDER BY decision_date NULLS LAST) = 1
)
SELECT
    d.k_number,
    d.decision_date,
    min(r.event_date_initiated) FILTER (
        WHERE r.event_date_initiated >= d.decision_date
    ) AS first_recall_date,
    count(*) FILTER (
        WHERE r.event_date_initiated < d.decision_date
    )::INTEGER AS dropped_predating_links
FROM decisions d
LEFT JOIN stg_recall_k_numbers r USING (k_number)
GROUP BY d.k_number, d.decision_date;
