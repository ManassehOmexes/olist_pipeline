WITH source AS (
    SELECT * FROM read_parquet(
        's3://olist-data-lake-dev/silver/olist_order_payments_dataset/olist_order_payments_dataset.parquet'
    )
)

SELECT
    order_id,
    payment_sequential,
    payment_type,
    payment_installments,
    payment_value
FROM source
