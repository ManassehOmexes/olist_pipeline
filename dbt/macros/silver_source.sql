{% macro silver_source(table_name) %}
    {% if target.type == 'duckdb' %}
        read_parquet('s3://olist-data-lake-dev/silver/{{ table_name }}/{{ table_name }}.parquet')
    {% else %}
        {{ source('silver', table_name) }}
    {% endif %}
{% endmacro %}
