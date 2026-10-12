CREATE OR REPLACE TABLE dq_report AS
WITH metrics AS (
    SELECT 'unparseable_recall_event_date_initiated' AS metric, count(*)::BIGINT AS issue_count
    FROM raw.recall
    WHERE nullif(trim(event_date_initiated), '') IS NOT NULL
      AND (NOT regexp_full_match(trim(event_date_initiated), '[0-9]{4}-[0-9]{2}-[0-9]{2}')
           OR try_strptime(trim(event_date_initiated), '%Y-%m-%d') IS NULL
           OR coalesce(year(try_strptime(trim(event_date_initiated), '%Y-%m-%d')), 0) NOT BETWEEN 1900 AND 2100)
    UNION ALL
    SELECT 'unparseable_recall_event_date_posted', count(*)
    FROM raw.recall
    WHERE nullif(trim(event_date_posted), '') IS NOT NULL
      AND (NOT regexp_full_match(trim(event_date_posted), '[0-9]{4}-[0-9]{2}-[0-9]{2}')
           OR try_strptime(trim(event_date_posted), '%Y-%m-%d') IS NULL
           OR coalesce(year(try_strptime(trim(event_date_posted), '%Y-%m-%d')), 0) NOT BETWEEN 1900 AND 2100)
    UNION ALL
    SELECT 'unparseable_recall_event_date_terminated', count(*)
    FROM raw.recall
    WHERE nullif(trim(event_date_terminated), '') IS NOT NULL
      AND (NOT regexp_full_match(trim(event_date_terminated), '[0-9]{4}-[0-9]{2}-[0-9]{2}')
           OR try_strptime(trim(event_date_terminated), '%Y-%m-%d') IS NULL
           OR coalesce(year(try_strptime(trim(event_date_terminated), '%Y-%m-%d')), 0) NOT BETWEEN 1900 AND 2100)
    UNION ALL
    SELECT 'unparseable_510k_decision_date', count(*)
    FROM raw.k510
    WHERE nullif(trim(decision_date), '') IS NOT NULL
      AND (NOT regexp_full_match(trim(decision_date), '[0-9]{4}-[0-9]{2}-[0-9]{2}')
           OR try_strptime(trim(decision_date), '%Y-%m-%d') IS NULL
           OR coalesce(year(try_strptime(trim(decision_date), '%Y-%m-%d')), 0) NOT BETWEEN 1900 AND 2100)
    UNION ALL
    SELECT 'unparseable_510k_date_received', count(*)
    FROM raw.k510
    WHERE nullif(trim(date_received), '') IS NOT NULL
      AND (NOT regexp_full_match(trim(date_received), '[0-9]{4}-[0-9]{2}-[0-9]{2}')
           OR try_strptime(trim(date_received), '%Y-%m-%d') IS NULL
           OR coalesce(year(try_strptime(trim(date_received), '%Y-%m-%d')), 0) NOT BETWEEN 1900 AND 2100)
    UNION ALL
    SELECT 'recall_rows_without_k_numbers', count(*)
    FROM raw.recall
    WHERE k_numbers IS NULL OR len(k_numbers) = 0
    UNION ALL
    SELECT 'recalled_k_numbers_missing_from_510k', count(DISTINCT r.k_number)
    FROM stg_recall_k_numbers r
    LEFT JOIN stg_510k k USING (k_number)
    WHERE k.k_number IS NULL
    UNION ALL
    SELECT 'links_dropped_for_predating_decision', coalesce(sum(dropped_predating_links), 0)
    FROM int_first_recall
    UNION ALL
    SELECT '510k_rows_without_classification_match', count(*)
    FROM stg_510k k
    LEFT JOIN stg_classification c USING (product_code)
    WHERE c.product_code IS NULL
)
SELECT * FROM metrics;
