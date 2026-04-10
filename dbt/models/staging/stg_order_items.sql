WITH source AS (
    SELECT * FROM read_parquet(
        's3://olist-data-lake-dev/silver/olist_order_items_dataset/olist_order_items_dataset.parquet'
    )
)

SELECT
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date,
    price,
    freight_value
FROM source
