CREATE OR REPLACE TABLE stg_recalls AS
SELECT
    * REPLACE (
        trim(product_code) AS product_code,
        CASE WHEN regexp_full_match(trim(event_date_initiated), '[0-9]{4}-[0-9]{2}-[0-9]{2}')
                  AND year(try_strptime(trim(event_date_initiated), '%Y-%m-%d')) BETWEEN 1900 AND 2100
            THEN try_strptime(trim(event_date_initiated), '%Y-%m-%d')::DATE END AS event_date_initiated,
        CASE WHEN regexp_full_match(trim(event_date_posted), '[0-9]{4}-[0-9]{2}-[0-9]{2}')
                  AND year(try_strptime(trim(event_date_posted), '%Y-%m-%d')) BETWEEN 1900 AND 2100
            THEN try_strptime(trim(event_date_posted), '%Y-%m-%d')::DATE END AS event_date_posted,
        CASE WHEN regexp_full_match(trim(event_date_terminated), '[0-9]{4}-[0-9]{2}-[0-9]{2}')
                  AND year(try_strptime(trim(event_date_terminated), '%Y-%m-%d')) BETWEEN 1900 AND 2100
            THEN try_strptime(trim(event_date_terminated), '%Y-%m-%d')::DATE END AS event_date_terminated
    ),
    year(CASE WHEN regexp_full_match(trim(event_date_initiated), '[0-9]{4}-[0-9]{2}-[0-9]{2}')
                   AND year(try_strptime(trim(event_date_initiated), '%Y-%m-%d')) BETWEEN 1900 AND 2100
        THEN try_strptime(trim(event_date_initiated), '%Y-%m-%d') END)::INTEGER AS recall_year
FROM raw.recall;
