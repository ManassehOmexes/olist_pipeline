{{ config(materialized='table', schema='utils') }}

{% if target.type == 'duckdb' %}

select
    generate_series::date as date_day
from generate_series(
    '2017-01-01'::date,
    '2025-12-31'::date,
    interval '1 day'
)

{% else %}

-- Redshift: generate_series nicht verfügbar — Cross-Join über Ziffern 0–9
with digits as (
    select 0 as d union all select 1 union all select 2 union all select 3
    union all select 4 union all select 5 union all select 6 union all select 7
    union all select 8 union all select 9
),
numbers as (
    select d1.d * 1000 + d2.d * 100 + d3.d * 10 + d4.d as n
    from digits d1
    cross join digits d2
    cross join digits d3
    cross join digits d4
)
select dateadd(day, n, '2017-01-01'::date) as date_day
from numbers
where dateadd(day, n, '2017-01-01'::date) <= '2025-12-31'::date
order by date_day

{% endif %}
