-- int_signals_enriched: joins staging signals with enforcement logs
-- to produce a denormalised intermediate layer ready for mart loading.

WITH signals AS (
    SELECT * FROM {{ ref('stg_signals') }}
),

enforcement AS (
    SELECT * FROM {{ ref('stg_enforcement') }}
),

enriched AS (
    SELECT
        s.signal_id,
        s.model_id,
        s.entity_id,
        s.label,
        s.score,
        s.threshold,
        s.is_positive,
        s.signal_timestamp,
        s.signal_type,
        s.metadata,
        s._loaded_at,
        e.action_id,
        e.action_type,
        e.policy_id,
        e.enforced_by,
        e.reason                                        AS enforcement_reason,
        e.action_timestamp,
        -- Derived: was this positive signal acted upon?
        CASE
            WHEN s.is_positive AND e.action_id IS NOT NULL THEN TRUE
            ELSE FALSE
        END                                             AS was_enforced
    FROM signals AS s
    LEFT JOIN enforcement AS e
        ON s.entity_id = e.entity_id
        AND e.action_timestamp BETWEEN s.signal_timestamp
            AND DATEADD('hour', 24, s.signal_timestamp)
)

SELECT * FROM enriched
