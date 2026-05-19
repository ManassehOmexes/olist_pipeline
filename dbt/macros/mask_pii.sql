{% macro mask_pii(column_name, method='hash') %}
    {%- if method == 'hash' -%}
        MD5(CAST({{ column_name }} AS VARCHAR))
    {%- elif method == 'truncate_zip' -%}
        LEFT(CAST({{ column_name }} AS VARCHAR), 3)
    {%- elif method == 'round_coords' -%}
        ROUND(CAST({{ column_name }} AS DOUBLE), 2)
    {%- else -%}
        {{ exceptions.raise_compiler_error("mask_pii: unknown method '" ~ method ~ "'. Use hash, truncate_zip, or round_coords.") }}
    {%- endif %}
{% endmacro %}
