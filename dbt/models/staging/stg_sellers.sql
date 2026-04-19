{{ config(dist='all') }}

WITH source AS (
    SELECT * FROM {{ silver_source('olist_sellers_dataset') }}
)

SELECT
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
FROM source