output "workgroup_endpoint" {
  description = "Endpoint für ODBC Verbindung (Power BI, psql)"
  value       = aws_redshiftserverless_workgroup.main.endpoint
}

output "database_name" {
  description = "Datenbankname"
  value       = aws_redshiftserverless_namespace.main.db_name
}
