WITH source AS (
    SELECT * FROM read_parquet(
        's3://olist-data-lake-dev/silver/olist_sellers_dataset/olist_sellers_dataset.parquet'
    )
)

SELECT
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
FROM source