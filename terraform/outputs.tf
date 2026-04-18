output "s3_bucket_id" {
  description = "Name des Data Lake Buckets"
  value       = module.s3.bucket_id
}

output "s3_bucket_arn" {
  description = "ARN des Data Lake Buckets"
  value       = module.s3.bucket_arn
}

output "glue_role_arn" {
  description = "ARN der Glue Rolle"
  value       = module.iam.glue_role_arn
}

output "airflow_role_arn" {
  description = "ARN der Airflow Rolle"
  value       = module.iam.airflow_role_arn
}

output "redshift_role_arn" {
  description = "ARN der Redshift Rolle"
  value       = module.iam.redshift_role_arn
}

output "redshift_endpoint" {
  description = "Redshift Endpoint fuer ODBC Verbindung"
  value       = module.redshift.workgroup_endpoint
}

output "redshift_database" {
  description = "Datenbankname"
  value       = module.redshift.database_name
}
