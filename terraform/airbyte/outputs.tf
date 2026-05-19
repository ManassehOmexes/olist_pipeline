output "olist_connection_id" {
  description = "Airbyte Connection ID: Olist S3 → Bronze"
  value       = airbyte_connection.olist_to_bronze.connection_id
}

output "shopify_connection_id" {
  description = "Airbyte Connection ID: Shopify → Bronze (null wenn nicht aktiviert)"
  value       = var.enable_shopify ? airbyte_connection.shopify_to_bronze[0].connection_id : null
}

output "postgres_connection_id" {
  description = "Airbyte Connection ID: Postgres → Bronze (null wenn nicht aktiviert)"
  value       = var.enable_postgres ? airbyte_connection.postgres_to_bronze[0].connection_id : null
}
