-- stg_enforcement: staging view over raw.enforcement_logs
-- Normalises column names and casts types. All timestamps are UTC (timestamp_ntz).

WITH source AS (

    SELECT
        action_id::VARCHAR                              AS action_id,
        entity_id::VARCHAR                              AS entity_id,
        action_type::VARCHAR                            AS action_type,
        policy_id::VARCHAR                              AS policy_id,
        enforced_by::VARCHAR                            AS enforced_by,
        reason::VARCHAR                                 AS reason,
        CONVERT_TIMEZONE('UTC', timestamp)::TIMESTAMP_NTZ AS action_timestamp,
        _loaded_at::TIMESTAMP_NTZ                       AS _loaded_at,
        metadata::VARIANT                               AS metadata
    FROM {{ source('raw', 'enforcement_logs') }}

)

SELECT * FROM source
