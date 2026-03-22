-- dim_models: dimension table of classifier/generative models observed in signals.

{{
    config(materialized='table')
}}

SELECT DISTINCT
    model_id,
    signal_type,
    MIN(signal_timestamp) OVER (PARTITION BY model_id)      AS first_seen_at,
    MAX(signal_timestamp) OVER (PARTITION BY model_id)      AS last_seen_at,
    COUNT(*) OVER (PARTITION BY model_id)                   AS total_signals,
    AVG(score) OVER (PARTITION BY model_id)                 AS avg_score,
    AVG(CASE WHEN is_positive THEN 1.0 ELSE 0.0 END)
        OVER (PARTITION BY model_id)                        AS positive_rate
FROM {{ ref('fct_signals') }}
WHERE model_id IS NOT NULL
