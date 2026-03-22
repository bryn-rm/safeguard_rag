-- fct_signals: incremental fact table of all safety signals.
-- High-watermark column: _loaded_at (avoids late-arriving data issues).
-- Unique key: signal_id.

{{
    config(
        materialized='incremental',
        unique_key='signal_id',
        incremental_strategy='merge',
        on_schema_change='fail'
    )
}}

WITH enriched AS (
    SELECT * FROM {{ ref('int_signals_enriched') }}
    {% if is_incremental() %}
    WHERE _loaded_at > (SELECT MAX(_loaded_at) FROM {{ this }})
    {% endif %}
)

SELECT
    signal_id,
    model_id,
    entity_id,
    label,
    score,
    threshold,
    is_positive,
    signal_timestamp,
    signal_type,
    action_id,
    action_type,
    policy_id,
    enforced_by,
    enforcement_reason,
    action_timestamp,
    was_enforced,
    _loaded_at,
    metadata
FROM enriched
