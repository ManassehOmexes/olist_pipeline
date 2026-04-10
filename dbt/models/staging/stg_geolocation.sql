-- Mehrfacheinträge pro PLZ auf Median-Koordinate aggregieren (EDA Befund)
WITH source AS (
    SELECT * FROM read_parquet(
        's3://olist-data-lake-dev/silver/olist_geolocation_dataset/olist_geolocation_dataset.parquet'
    )
)

SELECT
    geolocation_zip_code_prefix AS zip_code_prefix,
    AVG(geolocation_lat)        AS latitude,
    AVG(geolocation_lng)        AS longitude,
    ANY_VALUE(geolocation_city) AS city,
    ANY_VALUE(geolocation_state) AS state
FROM source
GROUP BY geolocation_zip_code_prefix
