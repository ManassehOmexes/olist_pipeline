WITH orders AS (
    SELECT * FROM {{ ref('int_orders_enriched') }}
)

SELECT
    order_id,
    customer_state,
    order_purchase_timestamp,
    order_delivered_customer_date,
    order_estimated_delivery_date,

    -- Lieferdauer in Tagen
    DATEDIFF('day',
        order_purchase_timestamp,
        order_delivered_customer_date
    ) AS delivery_days,

    -- Verspätet ja/nein
    CASE
        WHEN order_delivered_customer_date > order_estimated_delivery_date THEN TRUE
        ELSE FALSE
    END AS is_late

FROM orders
WHERE order_delivered_customer_date IS NOT NULL
