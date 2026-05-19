# --- Airbyte ---
variable "airbyte_url" {
  description = "Airbyte API URL"
  type        = string
  default     = "http://localhost:8006"
}

variable "airbyte_username" {
  description = "Airbyte Basic-Auth Benutzername"
  type        = string
  default     = "airbyte"
}

variable "airbyte_password" {
  description = "Airbyte Basic-Auth Passwort"
  type        = string
  sensitive   = true
  default     = "password"
}

variable "airbyte_workspace_id" {
  description = "Airbyte Workspace ID — ermitteln via: curl -s http://localhost:8006/api/v1/workspaces/list | jq '.workspaces[0].workspaceId'"
  type        = string
}

# --- AWS ---
variable "aws_region" {
  description = "AWS Region des S3-Buckets"
  type        = string
  default     = "eu-central-1"
}

variable "s3_bucket_name" {
  description = "S3-Bucket-Name fuer Bronze Layer"
  type        = string
  default     = "olist-data-lake-dev"
}

variable "aws_access_key_id" {
  description = "AWS Access Key ID fuer Airbyte S3-Zugriff"
  type        = string
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "AWS Secret Access Key fuer Airbyte S3-Zugriff"
  type        = string
  sensitive   = true
}

# --- Kunde ---
variable "customer_id" {
  description = "Eindeutiger Kundenbezeichner (z.B. 'acme') — wird in Resource-Namen verwendet"
  type        = string
  default     = "olist"
}

# --- Shopify (optional) ---
variable "enable_shopify" {
  description = "Shopify Source + Connection deployen"
  type        = bool
  default     = false
}

variable "shopify_shop" {
  description = "Shopify Shop-Domain (z.B. 'acme.myshopify.com')"
  type        = string
  default     = ""
}

variable "shopify_api_password" {
  description = "Shopify Admin API Access Token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "shopify_start_date" {
  description = "Sync-Startdatum ISO 8601 (z.B. '2023-01-01T00:00:00Z')"
  type        = string
  default     = "2023-01-01T00:00:00Z"
}

# --- Postgres (optional) ---
variable "enable_postgres" {
  description = "Postgres Source + Connection deployen"
  type        = bool
  default     = false
}

variable "postgres_host" {
  description = "PostgreSQL Hostname"
  type        = string
  default     = ""
}

variable "postgres_database" {
  description = "Datenbankname"
  type        = string
  default     = ""
}

variable "postgres_username" {
  description = "PostgreSQL Benutzername"
  type        = string
  default     = ""
}

variable "postgres_password" {
  description = "PostgreSQL Passwort"
  type        = string
  sensitive   = true
  default     = ""
}
