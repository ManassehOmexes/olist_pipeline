WITH source AS (
    SELECT * FROM read_parquet(
        's3://olist-data-lake-dev/silver/olist_products_dataset/olist_products_dataset.parquet'
    )
),

translation AS (
    SELECT * FROM read_parquet(
        's3://olist-data-lake-dev/silver/product_category_name_translation/product_category_name_translation.parquet'
    )
)

SELECT
    p.product_id,
    p.product_category_name,
    COALESCE(t.product_category_name_english, p.product_category_name) AS product_category_name_en,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm
FROM source p
LEFT JOIN translation t ON p.product_category_name = t.product_category_name