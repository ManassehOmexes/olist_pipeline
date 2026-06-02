{% macro initcap_sql(column) %}
    {% if target.type == 'duckdb' %}
        array_to_string(
            list_transform(
                string_split({{ column }}, ' '),
                x -> UPPER(LEFT(x, 1)) || LOWER(SUBSTRING(x, 2))
            ),
            ' '
        )
    {% else %}
        INITCAP({{ column }})
    {% endif %}
{% endmacro %}
