-- dim_entities: dimension table of unique entities (users, content items)
-- seen across all signal types.

{{
    config(materialized='table')
}}

SELECT DISTINCT
    entity_id,
    MIN(signal_timestamp) OVER (PARTITION BY entity_id)     AS first_seen_at,
    MAX(signal_timestamp) OVER (PARTITION BY entity_id)     AS last_seen_at,
    COUNT(*) OVER (PARTITION BY entity_id)                  AS total_signals,
    SUM(CASE WHEN is_positive THEN 1 ELSE 0 END)
        OVER (PARTITION BY entity_id)                       AS positive_signal_count,
    SUM(CASE WHEN was_enforced THEN 1 ELSE 0 END)
        OVER (PARTITION BY entity_id)                       AS enforcement_count
FROM {{ ref('fct_signals') }}
