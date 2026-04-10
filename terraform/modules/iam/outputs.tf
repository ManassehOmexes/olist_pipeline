output "glue_role_arn" {
  description = "ARN der Glue Rolle - wird beim Erstellen von Glue Jobs benötigt"
  value       = aws_iam_role.glue.arn
}

output "airflow_role_arn" {
  description = "ARN der Airflow Rolle"
  value       = aws_iam_role.airflow.arn
}

output "redshift_role_arn" {
  description = "ARN der Redshift Rolle — wird beim Erstellen des Workgroup benötigt"
  value       = aws_iam_role.redshift.arn
}
