CREATE OR REPLACE TABLE stg_recall_k_numbers AS
WITH exploded AS (
    SELECT
        cfres_id,
        res_event_number,
        upper(trim(unnest(k_numbers))) AS k_number,
        event_date_initiated
    FROM stg_recalls
    WHERE k_numbers IS NOT NULL
)
SELECT *
FROM exploded
WHERE k_number <> '';
