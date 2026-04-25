{{ config(materialized='table', dist='order_id', sort='order_month') }}

-- Grain: eine Zeile pro Bestellposition (order_item)
-- Warum dieser Grain: Power BI kann damit nach Monat, Bundesstaat
-- und Kategorie gleichzeitig schneiden ohne vorher aggregieren zu müssen.
--
-- KPI-Karten im Dashboard:
--   Gesamtumsatz       = SUM(item_revenue)
--   Gesamte Bestellungen = DISTINCTCOUNT(order_id)
--   Avg. Review Score  = AVERAGE(review_score)

WITH order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

orders AS (
    -- int_orders_enriched hat bereits customer_state via JOIN mit stg_customers
    SELECT * FROM {{ ref('int_orders_enriched') }}
),

products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

reviews AS (
    -- Eine Bewertung pro Bestellung (AVG falls mehrere existieren)
    SELECT
        order_id,
        ROUND(AVG(review_score), 1) AS review_score
    FROM {{ ref('stg_order_reviews') }}
    GROUP BY order_id
)

SELECT
    oi.order_id || '-' || CAST(oi.order_item_id AS VARCHAR)       AS order_item_pk,
    oi.order_id,
    oi.order_item_id,
    CAST(DATE_TRUNC('month', o.order_purchase_timestamp) AS DATE) AS order_month,
    o.customer_state,
    COALESCE(p.product_category_name_en, 'unknown')               AS product_category,
    ROUND(oi.price, 2)                                            AS item_revenue,
    r.review_score

FROM order_items oi
LEFT JOIN orders   o ON oi.order_id   = o.order_id
LEFT JOIN products p ON oi.product_id = p.product_id
LEFT JOIN reviews  r ON oi.order_id   = r.order_id
WHERE o.order_status = 'delivered'
