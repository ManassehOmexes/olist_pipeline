{{ config(dist='customer_id') }}

WITH source AS (
    SELECT * FROM {{ silver_source('olist_customers_dataset') }}
)

SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
FROM source