-- Classifier precision query template
-- Parameters: model_id (str), start_date (str), end_date (str)
--
-- Returns daily precision metrics for the specified classifier model
-- over the given date range.

SELECT
    DATE_TRUNC('day', s.timestamp)                          AS day,
    s.model_id,
    COUNT(*)                                                AS total_signals,
    SUM(CASE WHEN s.is_positive THEN 1 ELSE 0 END)          AS predicted_positives,
    SUM(CASE WHEN s.is_positive AND e.action_id IS NOT NULL
             THEN 1 ELSE 0 END)                             AS true_positives,
    ROUND(
        SUM(CASE WHEN s.is_positive AND e.action_id IS NOT NULL
                 THEN 1 ELSE 0 END)
        / NULLIF(SUM(CASE WHEN s.is_positive THEN 1 ELSE 0 END), 0),
        4
    )                                                       AS precision
FROM {{ schema }}.fct_signals     AS s
LEFT JOIN {{ schema }}.dim_actions AS e
    ON s.signal_id = e.signal_id
WHERE
    s.model_id   = '{{ model_id }}'
    AND s.timestamp >= '{{ start_date }}'::TIMESTAMP_NTZ
    AND s.timestamp <  '{{ end_date }}'::TIMESTAMP_NTZ
GROUP BY 1, 2
ORDER BY 1 DESC
