#!/usr/bin/env bash
# Lokaler CI-Check: dbt run + dbt test gegen DuckDB dev.
# Voraussetzung: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION gesetzt.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DBT_DIR="$SCRIPT_DIR/../dbt"

cd "$DBT_DIR"
dbt deps
dbt run --target dev --profiles-dir .
dbt test --target dev --profiles-dir .
