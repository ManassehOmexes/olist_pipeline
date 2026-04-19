{{ config(dist='all', sort='avg_delivery_days') }}

WITH delivery AS (
    SELECT * FROM {{ ref('int_delivery_times') }}
)

SELECT
    customer_state                                          AS state,
    COUNT(order_id)                                         AS total_delivered_orders,
    ROUND(AVG(delivery_days), 1)                            AS avg_delivery_days,
    ROUND(MIN(delivery_days), 1)                            AS min_delivery_days,
    ROUND(MAX(delivery_days), 1)                            AS max_delivery_days,
    SUM(CASE WHEN is_late THEN 1 ELSE 0 END)               AS late_orders,
    ROUND(
        100.0 * SUM(CASE WHEN is_late THEN 1 ELSE 0 END)
        / COUNT(order_id), 2
    )                                                       AS late_rate_pct

FROM delivery
GROUP BY customer_state
ORDER BY avg_delivery_days DESC