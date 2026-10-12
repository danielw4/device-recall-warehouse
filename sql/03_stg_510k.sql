CREATE OR REPLACE TABLE stg_510k AS
SELECT * REPLACE (
    upper(trim(k_number)) AS k_number,
    trim(product_code) AS product_code,
    trim(clearance_type) AS clearance_type,
    trim(decision_code) AS decision_code,
    CASE WHEN regexp_full_match(trim(decision_date), '[0-9]{4}-[0-9]{2}-[0-9]{2}')
              AND year(try_strptime(trim(decision_date), '%Y-%m-%d')) BETWEEN 1900 AND 2100
        THEN try_strptime(trim(decision_date), '%Y-%m-%d')::DATE END AS decision_date,
    CASE WHEN regexp_full_match(trim(date_received), '[0-9]{4}-[0-9]{2}-[0-9]{2}')
              AND year(try_strptime(trim(date_received), '%Y-%m-%d')) BETWEEN 1900 AND 2100
        THEN try_strptime(trim(date_received), '%Y-%m-%d')::DATE END AS date_received,
    nullif(trim(advisory_committee_description), '') AS advisory_committee_description
)
FROM raw.k510;
