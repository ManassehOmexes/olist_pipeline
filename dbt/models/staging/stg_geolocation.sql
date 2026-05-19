-- Mehrfacheinträge pro PLZ auf Median-Koordinate aggregieren (EDA Befund)
WITH source AS (
    SELECT * FROM {{ silver_source('olist_geolocation_dataset') }}
)

SELECT
    geolocation_zip_code_prefix                             AS zip_code_prefix,
    {{ mask_pii('AVG(geolocation_lat)', 'round_coords') }} AS latitude,
    {{ mask_pii('AVG(geolocation_lng)', 'round_coords') }} AS longitude,
    ANY_VALUE(geolocation_city)                            AS city,
    ANY_VALUE(geolocation_state)                           AS state
FROM source
GROUP BY geolocation_zip_code_prefix
