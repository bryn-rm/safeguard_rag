-- stg_signals: staging view over raw.classifier_outputs and raw.model_outputs
-- Normalises column names and casts types. All timestamps are UTC (timestamp_ntz).

WITH source AS (

    SELECT
        signal_id::VARCHAR                              AS signal_id,
        model_id::VARCHAR                               AS model_id,
        entity_id::VARCHAR                              AS entity_id,
        label::VARCHAR                                  AS label,
        score::FLOAT                                    AS score,
        threshold::FLOAT                                AS threshold,
        is_positive::BOOLEAN                            AS is_positive,
        CONVERT_TIMEZONE('UTC', timestamp)::TIMESTAMP_NTZ AS signal_timestamp,
        _loaded_at::TIMESTAMP_NTZ                       AS _loaded_at,
        'classifier'                                    AS signal_type,
        metadata::VARIANT                               AS metadata
    FROM {{ source('raw', 'classifier_outputs') }}

)

SELECT * FROM source
