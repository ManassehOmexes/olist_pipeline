{% snapshot orders_snapshot %}

{{
    config(
        target_schema='snapshots',
        unique_key='order_id',
        strategy='check',
        check_cols=['order_status', 'order_delivered_customer_date'],
        invalidate_hard_deletes=True
    )
}}

SELECT
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp,
    order_approved_at,
    order_delivered_customer_date,
    order_estimated_delivery_date
FROM {{ ref('stg_orders') }}

{% endsnapshot %}
