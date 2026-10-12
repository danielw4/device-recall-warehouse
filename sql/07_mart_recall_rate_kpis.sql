CREATE OR REPLACE TABLE mart_recall_rate_kpis AS
WITH dimensions AS (
    SELECT 'clearance_type' AS dimension, clearance_type AS level, recalled, duration_days
    FROM mart_clearance_survival
    UNION ALL
    SELECT 'specialty', coalesce(specialty, 'Missing'), recalled, duration_days
    FROM mart_clearance_survival
    UNION ALL
    SELECT 'device_class', coalesce(device_class, 'Missing'), recalled, duration_days
    FROM mart_clearance_survival
    UNION ALL
    SELECT 'decision_year', decision_year::VARCHAR, recalled, duration_days
    FROM mart_clearance_survival
)
SELECT
    dimension,
    level,
    count(*)::INTEGER AS cleared_count,
    sum(recalled)::INTEGER AS recalled_count,
    round(100.0 * sum(recalled) / count(*), 4) AS recall_percentage,
    round(median(duration_days / 365.25) FILTER (WHERE recalled = 1), 4) AS median_years_to_first_recall
FROM dimensions
GROUP BY dimension, level;
