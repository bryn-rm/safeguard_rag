-- dim_actions: dimension table of enforcement actions taken against entities.

{{
    config(materialized='table')
}}

SELECT DISTINCT
    action_id,
    entity_id,
    action_type,
    policy_id,
    enforced_by,
    enforcement_reason,
    action_timestamp,
    signal_id           -- FK back to fct_signals
FROM {{ ref('fct_signals') }}
WHERE action_id IS NOT NULL
