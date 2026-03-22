-- Report volume query template
-- Parameters: report_type (str), start_date (str), end_date (str)
--
-- Returns hourly report submission counts for the specified report type,
-- broken down by severity tier.

SELECT
    DATE_TRUNC('hour', r.timestamp)             AS hour,
    r.report_type,
    r.severity,
    COUNT(*)                                    AS report_count,
    COUNT(DISTINCT r.reporter_id)               AS unique_reporters,
    COUNT(DISTINCT r.reported_entity_id)        AS unique_entities_reported
FROM {{ schema }}.fct_signals AS r
WHERE
    r.signal_type = 'report'
    AND r.report_type = '{{ report_type }}'
    AND r.timestamp >= '{{ start_date }}'::TIMESTAMP_NTZ
    AND r.timestamp <  '{{ end_date }}'::TIMESTAMP_NTZ
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 4 DESC
