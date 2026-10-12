CREATE OR REPLACE TABLE mart_root_cause_trends AS
WITH counts AS (
    SELECT
        recall_year,
        coalesce(nullif(trim(root_cause_description), ''), 'Missing') AS root_cause_description,
        count(*)::INTEGER AS recall_products,
        count(DISTINCT res_event_number)::INTEGER AS distinct_recall_events
    FROM stg_recalls
    WHERE recall_year IS NOT NULL
    GROUP BY recall_year, root_cause_description
)
SELECT
    *,
    recall_products::DOUBLE / sum(recall_products) OVER (PARTITION BY recall_year) AS product_share_of_year,
    distinct_recall_events::DOUBLE
        / sum(distinct_recall_events) OVER (PARTITION BY recall_year) AS event_share_of_year
FROM counts;
