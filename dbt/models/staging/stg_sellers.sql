{{ config(dist='all') }}

WITH source AS (
    SELECT * FROM {{ silver_source('olist_sellers_dataset') }}
)

SELECT
    seller_id,
    {{ mask_pii('seller_zip_code_prefix', 'truncate_zip') }} AS seller_zip_code_prefix,
    seller_city,
    seller_state
FROM source