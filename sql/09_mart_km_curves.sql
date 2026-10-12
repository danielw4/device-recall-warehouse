CREATE OR REPLACE TABLE mart_km_curves AS
WITH timeline AS (
    -- Collapse subjects to one row per observed duration within each pathway.
    SELECT
        clearance_type,
        duration_days,
        count(*)::INTEGER AS exits_at_time,
        sum(recalled)::INTEGER AS events_at_time
    FROM mart_clearance_survival
    GROUP BY clearance_type, duration_days
), risk_sets AS (
    -- Subjects at risk just before t are the group total minus all earlier exits.
    SELECT
        clearance_type,
        duration_days,
        events_at_time,
        sum(exits_at_time) OVER (PARTITION BY clearance_type)::INTEGER
          - coalesce(sum(exits_at_time) OVER (
                PARTITION BY clearance_type ORDER BY duration_days
                ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
            ), 0)::INTEGER AS at_risk
    FROM timeline
), factors AS (
    SELECT
        *,
        1.0 - events_at_time::DOUBLE / at_risk AS survival_factor
    FROM risk_sets
)
SELECT
    clearance_type,
    duration_days,
    at_risk,
    events_at_time,
    CASE
        WHEN max((survival_factor = 0)::INTEGER) OVER (
            PARTITION BY clearance_type ORDER BY duration_days
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) = 1 THEN 0.0
        ELSE exp(sum(ln(survival_factor)) OVER (
            PARTITION BY clearance_type ORDER BY duration_days
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ))
    END AS survival_probability
FROM factors
ORDER BY clearance_type, duration_days;
