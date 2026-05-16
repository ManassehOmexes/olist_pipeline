{{ config(materialized='table', schema='intermediate', dist='order_item_id', sort='order_purchase_timestamp') }}

-- Grain-level base table for MetricFlow Semantic Layer.
-- One row per order item (delivered orders only).
-- Joins all dimensions and measures needed for the 6 KPIs.

WITH order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

orders AS (
    SELECT * FROM {{ ref('int_orders_enriched') }}
),

products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

reviews AS (
    SELECT * FROM {{ ref('stg_order_reviews') }}
),

delivery AS (
    SELECT * FROM {{ ref('int_delivery_times') }}
)

SELECT
    oi.order_item_id,
    o.order_id,
    o.customer_id,
    o.order_purchase_timestamp,
    o.customer_state,
    p.product_id,
    p.product_category_name_en                       AS category,
    oi.price,
    oi.freight_value,
    r.review_score,
    d.delivery_days,
    CASE WHEN d.is_late THEN 1 ELSE 0 END            AS is_late_flag

FROM order_items oi
LEFT JOIN orders o    ON oi.order_id   = o.order_id
LEFT JOIN products p  ON oi.product_id = p.product_id
LEFT JOIN reviews r   ON oi.order_id   = r.order_id
LEFT JOIN delivery d  ON oi.order_id   = d.order_id
WHERE o.order_status = 'delivered'
