WITH source AS (
    SELECT * FROM {{ silver_source('olist_order_items_dataset') }}
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
