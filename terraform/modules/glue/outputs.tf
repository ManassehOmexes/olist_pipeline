output "job_name" {
  description = "Name des Glue Jobs - wird vom Airflow DAG verwendet"
  value       = aws_glue_job.bronze_to_silver.name
}
