# -------------------------------------------------------
# Airbyte Connections as Code — Terraform Provider v0.13
#
# Voraussetzung: Airbyte muss laufen (docker compose up -d)
#
# Deploy-Reihenfolge:
#   1. cd terraform && terraform apply         → AWS-Infrastruktur
#   2. docker compose up -d                    → Airbyte starten
#   3. cd terraform/airbyte                    → dieser Workspace
#      terraform init && terraform apply       → Connections deployen
#
# Workspace ID ermitteln (einmalig, vor erstem apply):
#   curl -s -u airbyte:password http://localhost:8006/api/v1/workspaces/list \
#     | jq -r '.workspaces[0].workspaceId'
# -------------------------------------------------------

terraform {
  required_version = ">= 1.5"

  required_providers {
    airbyte = {
      source  = "airbytehq/airbyte"
      version = "~> 0.13"
    }
  }

  # Eigener State-Key — teilt S3-Backend + DynamoDB-Lock mit dem Haupt-Workspace
  backend "s3" {
    bucket         = "olist-data-lake-dev"
    key            = "terraform/airbyte/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "olist-terraform-locks"
    encrypt        = true
  }
}

provider "airbyte" {
  username   = var.airbyte_username
  password   = var.airbyte_password
  server_url = var.airbyte_url
}

# -------------------------------------------------------
# S3 Source — Olist raw CSVs
# -------------------------------------------------------
resource "airbyte_source_s3" "olist" {
  name         = "olist-s3-raw-csv"
  workspace_id = var.airbyte_workspace_id

  configuration = {
    bucket                = var.s3_bucket_name
    aws_access_key_id     = var.aws_access_key_id
    aws_secret_access_key = var.aws_secret_access_key
    start_date            = "2017-01-01T00:00:00Z"

    # Jede CSV-Datei im raw/-Prefix als eigener Stream
    streams = [
      {
        name  = "olist_orders_dataset"
        globs = ["raw/olist_orders_dataset*.csv"]
        format = { csv_format = { delimiter = ",", double_quote = true, encoding = "UTF-8" } }
      },
      {
        name  = "olist_order_items_dataset"
        globs = ["raw/olist_order_items_dataset*.csv"]
        format = { csv_format = { delimiter = ",", double_quote = true, encoding = "UTF-8" } }
      },
      {
        name  = "olist_order_payments_dataset"
        globs = ["raw/olist_order_payments_dataset*.csv"]
        format = { csv_format = { delimiter = ",", double_quote = true, encoding = "UTF-8" } }
      },
      {
        name  = "olist_order_reviews_dataset"
        globs = ["raw/olist_order_reviews_dataset*.csv"]
        format = { csv_format = { delimiter = ",", double_quote = true, encoding = "UTF-8" } }
      },
      {
        name  = "olist_customers_dataset"
        globs = ["raw/olist_customers_dataset*.csv"]
        format = { csv_format = { delimiter = ",", double_quote = true, encoding = "UTF-8" } }
      },
      {
        name  = "olist_sellers_dataset"
        globs = ["raw/olist_sellers_dataset*.csv"]
        format = { csv_format = { delimiter = ",", double_quote = true, encoding = "UTF-8" } }
      },
      {
        name  = "olist_products_dataset"
        globs = ["raw/olist_products_dataset*.csv"]
        format = { csv_format = { delimiter = ",", double_quote = true, encoding = "UTF-8" } }
      },
      {
        name  = "olist_geolocation_dataset"
        globs = ["raw/olist_geolocation_dataset*.csv"]
        format = { csv_format = { delimiter = ",", double_quote = true, encoding = "UTF-8" } }
      },
      {
        name  = "product_category_name_translation"
        globs = ["raw/product_category_name_translation*.csv"]
        format = { csv_format = { delimiter = ",", double_quote = true, encoding = "UTF-8" } }
      },
    ]
  }
}

# -------------------------------------------------------
# S3 Destination — Bronze Layer (Parquet, SNAPPY)
# -------------------------------------------------------
resource "airbyte_destination_s3" "bronze" {
  name         = "s3-bronze-layer"
  workspace_id = var.airbyte_workspace_id

  configuration = {
    s3_bucket_name    = var.s3_bucket_name
    s3_bucket_path    = "bronze"
    s3_bucket_region  = var.aws_region
    access_key_id     = var.aws_access_key_id
    secret_access_key = var.aws_secret_access_key
    # $${...} escapen — Terraform würde ${...} sonst als Interpolation lesen
    s3_path_format = "$${NAMESPACE}/$${STREAM_NAME}/$${STREAM_NAME}_$${EPOCH}"

    format = {
      parquet_columnar_storage = {
        compression_codec       = "SNAPPY"
        block_size_mb           = 128
        max_padding_size_mb     = 8
        page_size_kb            = 1024
        dictionary_encoding     = true
        dictionary_page_size_kb = 1024
      }
    }
  }
}

# -------------------------------------------------------
# Connection: Olist S3 → Bronze
# -------------------------------------------------------
resource "airbyte_connection" "olist_to_bronze" {
  name           = "olist-raw-to-bronze"
  source_id      = airbyte_source_s3.olist.source_id
  destination_id = airbyte_destination_s3.bronze.destination_id
  status         = "active"

  schedule = {
    schedule_type   = "cron"
    cron_expression = "0 6 * * *"
  }

  configurations = {
    streams = [
      { name = "olist_orders_dataset",              sync_mode = "incremental_append" },
      { name = "olist_order_items_dataset",         sync_mode = "incremental_append" },
      { name = "olist_order_payments_dataset",      sync_mode = "incremental_append" },
      { name = "olist_order_reviews_dataset",       sync_mode = "incremental_append" },
      { name = "olist_customers_dataset",           sync_mode = "full_refresh_overwrite" },
      { name = "olist_sellers_dataset",             sync_mode = "full_refresh_overwrite" },
      { name = "olist_products_dataset",            sync_mode = "full_refresh_overwrite" },
      { name = "olist_geolocation_dataset",         sync_mode = "full_refresh_overwrite" },
      { name = "product_category_name_translation", sync_mode = "full_refresh_overwrite" },
    ]
  }
}

# -------------------------------------------------------
# Shopify Source + Connection (optional — enable_shopify = true)
# -------------------------------------------------------
resource "airbyte_source_shopify" "customer" {
  count = var.enable_shopify ? 1 : 0

  name         = "shopify-${var.customer_id}"
  workspace_id = var.airbyte_workspace_id

  configuration = {
    shop       = var.shopify_shop
    start_date = var.shopify_start_date
    credentials = {
      # Provider v0.13: api_password ist doppelt verschachtelt
      api_password = {
        api_password = var.shopify_api_password
      }
    }
  }
}

resource "airbyte_connection" "shopify_to_bronze" {
  count = var.enable_shopify ? 1 : 0

  name           = "shopify-${var.customer_id}-to-bronze"
  source_id      = airbyte_source_shopify.customer[0].source_id
  destination_id = airbyte_destination_s3.bronze.destination_id
  status         = "active"

  schedule = {
    schedule_type   = "cron"
    cron_expression = "0 5 * * *"
  }

  configurations = {
    streams = [
      { name = "orders",        sync_mode = "incremental_deduped_history" },
      { name = "products",      sync_mode = "incremental_deduped_history" },
      { name = "customers",     sync_mode = "incremental_deduped_history" },
      { name = "order_refunds", sync_mode = "incremental_deduped_history" },
    ]
  }
}

# -------------------------------------------------------
# Postgres Source + Connection (optional — enable_postgres = true)
# -------------------------------------------------------
resource "airbyte_source_postgres" "customer" {
  count = var.enable_postgres ? 1 : 0

  name         = "postgres-${var.customer_id}"
  workspace_id = var.airbyte_workspace_id

  configuration = {
    host     = var.postgres_host
    port     = 5432
    database = var.postgres_database
    username = var.postgres_username
    password = var.postgres_password
    schemas  = ["public"]
    ssl_mode = {
      require = {}
    }
    replication_method = {
      scan_changes_with_user_defined_cursor = {}
    }
  }
}

resource "airbyte_connection" "postgres_to_bronze" {
  count = var.enable_postgres ? 1 : 0

  name           = "postgres-${var.customer_id}-to-bronze"
  source_id      = airbyte_source_postgres.customer[0].source_id
  destination_id = airbyte_destination_s3.bronze.destination_id
  status         = "active"

  schedule = {
    schedule_type   = "cron"
    cron_expression = "0 4 * * *"
  }

  configurations = {
    streams = [
      { name = "orders",    sync_mode = "incremental_deduped_history" },
      { name = "products",  sync_mode = "incremental_deduped_history" },
      { name = "customers", sync_mode = "incremental_deduped_history" },
    ]
  }
}
