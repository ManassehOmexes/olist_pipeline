WITH reviews AS (
    SELECT * FROM {{ ref('stg_order_reviews') }}
),

delivery AS (
    SELECT * FROM {{ ref('int_delivery_times') }}
)

SELECT
    r.review_score,
    COUNT(r.review_id)                                      AS total_reviews,
    ROUND(AVG(d.delivery_days), 1)                          AS avg_delivery_days,
    ROUND(
        100.0 * SUM(CASE WHEN d.is_late THEN 1 ELSE 0 END)
        / COUNT(r.review_id), 2
    )                                                       AS late_rate_pct

FROM reviews r
LEFT JOIN delivery d ON r.order_id = d.order_id
GROUP BY r.review_score
ORDER BY r.review_score DESC