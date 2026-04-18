-- Mehrfacheinträge pro PLZ auf Median-Koordinate aggregieren (EDA Befund)
WITH source AS (
    SELECT * FROM {{ silver_source('olist_geolocation_dataset') }}
)

SELECT
    geolocation_zip_code_prefix AS zip_code_prefix,
    AVG(geolocation_lat)        AS latitude,
    AVG(geolocation_lng)        AS longitude,
    ANY_VALUE(geolocation_city) AS city,
    ANY_VALUE(geolocation_state) AS state
FROM source
GROUP BY geolocation_zip_code_prefix
