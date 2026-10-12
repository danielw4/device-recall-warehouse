CREATE OR REPLACE TABLE mart_clearance_survival AS
WITH censor AS (
    SELECT max(event_date_initiated) AS censor_date
    FROM stg_recalls
), classifications AS (
    SELECT product_code, device_class
    FROM stg_classification
    QUALIFY row_number() OVER (PARTITION BY product_code ORDER BY product_code) = 1
)
SELECT
    k.k_number,
    k.decision_date,
    year(k.decision_date)::INTEGER AS decision_year,
    k.clearance_type,
    k.product_code,
    c.device_class,
    k.advisory_committee_description AS specialty,
    (f.first_recall_date IS NOT NULL)::INTEGER AS recalled,
    f.first_recall_date,
    date_diff('day', k.decision_date, coalesce(f.first_recall_date, x.censor_date))::INTEGER AS duration_days,
    x.censor_date
FROM stg_510k k
LEFT JOIN int_first_recall f USING (k_number, decision_date)
LEFT JOIN classifications c USING (product_code)
CROSS JOIN censor x
WHERE k.decision_code LIKE 'SE%'
  AND k.decision_date >= DATE '2003-01-01'
  -- A clearance after the analysis censor date has no observable follow-up time.
  AND k.decision_date <= x.censor_date
  AND k.clearance_type IN ('Traditional', 'Special', 'Abbreviated')
QUALIFY row_number() OVER (PARTITION BY k.k_number ORDER BY k.decision_date) = 1;
