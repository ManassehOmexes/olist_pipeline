WITH source AS (
    SELECT * FROM read_parquet(
        's3://olist-data-lake-dev/silver/olist_order_reviews_dataset/olist_order_reviews_dataset.parquet'
    )
),

-- review_id ist im Quelldatensatz nicht unique (789 Duplikate).
-- Wir behalten je review_id die neueste Antwort.
deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY review_id
            ORDER BY review_answer_timestamp DESC
        ) AS rn
    FROM source
)

SELECT
    review_id,
    order_id,
    review_score,
    review_creation_date,
    review_answer_timestamp
FROM deduped
WHERE rn = 1
