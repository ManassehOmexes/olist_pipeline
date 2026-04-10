WITH orders AS (
    SELECT * FROM {{ ref('int_orders_enriched') }}
),

order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

reviews AS (
    SELECT * FROM {{ ref('stg_order_reviews') }}
)

SELECT
    o.customer_state                                AS state,
    COUNT(DISTINCT o.order_id)                      AS total_orders,
    ROUND(SUM(oi.price), 2)                         AS total_revenue,
    ROUND(AVG(oi.price), 2)                         AS avg_order_value,
    ROUND(AVG(r.review_score), 2)                   AS avg_review_score

FROM orders o
LEFT JOIN order_items oi ON o.order_id = oi.order_id
LEFT JOIN reviews r      ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY o.customer_state
ORDER BY total_revenue DESC
