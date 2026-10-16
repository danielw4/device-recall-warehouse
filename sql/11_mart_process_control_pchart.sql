CREATE OR REPLACE TABLE mart_process_control_pchart AS
WITH cause_counts AS (
    -- Count product-level cause labels within each recall event.
    SELECT
        res_event_number,
        nullif(trim(root_cause_description), '') AS root_cause_description,
        count(*) AS cause_count
    FROM stg_recalls
    GROUP BY res_event_number, root_cause_description
), event_causes AS (
    -- Select the modal event cause, resolving ties alphabetically.
    SELECT res_event_number, root_cause_description
    FROM cause_counts
    QUALIFY row_number() OVER (
        PARTITION BY res_event_number
        ORDER BY cause_count DESC, root_cause_description ASC NULLS LAST
    ) = 1
), events AS (
    SELECT
        r.res_event_number,
        date_trunc('month', min(r.event_date_initiated))::DATE AS month,
        c.root_cause_description
    FROM stg_recalls r
    JOIN event_causes c USING (res_event_number)
    GROUP BY r.res_event_number, c.root_cause_description
    HAVING min(r.event_date_initiated) IS NOT NULL
), window_end AS (
    -- The month containing the latest event is partial and is excluded.
    SELECT date_trunc('month', max(event_date_initiated))::DATE AS latest_month
    FROM stg_recalls
), monthly AS (
    SELECT
        month,
        count(*)::INTEGER AS n_events,
        count(*) FILTER (WHERE root_cause_description = 'Process control')::INTEGER
            AS process_control_events
    FROM events
    CROSS JOIN window_end
    WHERE month >= DATE '2010-01-01'
      AND month < latest_month
      AND root_cause_description NOT IN (
          'Other',
          'Under Investigation by firm',
          'Unknown/Undetermined by firm'
      )
    GROUP BY month
), proportions AS (
    -- Use the pooled event share for the p-chart center line.
    SELECT
        *,
        process_control_events::DOUBLE / n_events AS p,
        sum(process_control_events) OVER ()::DOUBLE / sum(n_events) OVER () AS p_bar
    FROM monthly
), limits AS (
    SELECT
        *,
        greatest(0.0, p_bar - 3 * sqrt(p_bar * (1 - p_bar) / n_events)) AS lcl,
        p_bar + 3 * sqrt(p_bar * (1 - p_bar) / n_events) AS ucl
    FROM proportions
), sides AS (
    SELECT
        *,
        CASE WHEN p > p_bar THEN 1 WHEN p < p_bar THEN -1 ELSE 0 END AS side
    FROM limits
), run_starts AS (
    -- Equal points and gaps in the monthly series break a same-side run.
    SELECT
        *,
        CASE
            WHEN side = 0 THEN 1
            WHEN lag(side) OVER (ORDER BY month) = side
             AND lag(month) OVER (ORDER BY month) = month - INTERVAL 1 MONTH THEN 0
            ELSE 1
        END AS starts_run
    FROM sides
), run_groups AS (
    SELECT
        *,
        sum(starts_run) OVER (ORDER BY month) AS run_group
    FROM run_starts
), flagged AS (
    SELECT
        *,
        row_number() OVER (PARTITION BY run_group ORDER BY month) AS run_position
    FROM run_groups
)
SELECT
    month,
    n_events,
    process_control_events,
    p,
    p_bar,
    lcl,
    ucl,
    (p > ucl OR p < lcl) AS out_of_control,
    (side <> 0 AND run_position >= 8) AS run_rule
FROM flagged
ORDER BY month;
