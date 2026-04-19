{{ config(dist='all', sort='total_revenue') }}

WITH order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
)

SELECT
    p.product_category_name_en                  AS category,
    COUNT(DISTINCT o.order_id)                  AS total_orders,
    COUNT(oi.order_item_id)                     AS total_items_sold,
    ROUND(SUM(oi.price), 2)                     AS total_revenue,
    ROUND(SUM(oi.freight_value), 2)             AS total_freight,
    ROUND(AVG(oi.price), 2)                     AS avg_item_price

FROM order_items oi
LEFT JOIN products p  ON oi.product_id  = p.product_id
LEFT JOIN orders o    ON oi.order_id    = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY p.product_category_name_en
ORDER BY total_revenue DESC
