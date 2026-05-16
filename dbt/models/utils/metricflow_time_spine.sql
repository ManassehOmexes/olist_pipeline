{{ config(materialized='table', schema='utils') }}

-- Time spine required by MetricFlow Semantic Layer (dbt 1.9+).
-- Generates one row per day from 2017-01-01 (Olist dataset start) to 2025-12-31.
-- DuckDB: generate_series returns a struct, cast to date.
select
    generate_series::date as date_day
from generate_series(
    '2017-01-01'::date,
    '2025-12-31'::date,
    interval '1 day'
)
