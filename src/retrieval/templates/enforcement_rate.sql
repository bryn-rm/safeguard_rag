-- Enforcement rate query template
-- Parameters: action_type (str), start_date (str), end_date (str)
--
-- Returns daily enforcement counts and rate relative to total signals
-- for the specified action type.

SELECT
    DATE_TRUNC('day', a.timestamp)              AS day,
    a.action_type,
    COUNT(*)                                    AS enforcement_count,
    s.total_signals,
    ROUND(COUNT(*) / NULLIF(s.total_signals, 0), 4) AS enforcement_rate
FROM {{ schema }}.dim_actions AS a
JOIN (
    SELECT
        DATE_TRUNC('day', timestamp) AS day,
        COUNT(*)                     AS total_signals
    FROM {{ schema }}.fct_signals
    WHERE
        timestamp >= '{{ start_date }}'::TIMESTAMP_NTZ
        AND timestamp <  '{{ end_date }}'::TIMESTAMP_NTZ
    GROUP BY 1
) AS s ON DATE_TRUNC('day', a.timestamp) = s.day
WHERE
    a.action_type = '{{ action_type }}'
    AND a.timestamp >= '{{ start_date }}'::TIMESTAMP_NTZ
    AND a.timestamp <  '{{ end_date }}'::TIMESTAMP_NTZ
GROUP BY 1, 2, 4
ORDER BY 1 DESC
