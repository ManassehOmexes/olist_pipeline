WITH source AS (
    SELECT * FROM read_parquet(
        's3://olist-data-lake-dev/silver/olist_customers_dataset/olist_customers_dataset.parquet'
    )
)

SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
FROM source