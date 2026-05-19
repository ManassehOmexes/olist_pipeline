{{ config(dist='customer_id') }}

WITH source AS (
    SELECT * FROM {{ silver_source('olist_customers_dataset') }}
)

SELECT
    customer_id,
    {{ mask_pii('customer_unique_id', 'hash') }}               AS customer_unique_id,
    {{ mask_pii('customer_zip_code_prefix', 'truncate_zip') }} AS customer_zip_code_prefix,
    customer_city,
    customer_state
FROM source