output "bucket_id" {
  description = "Name des S3 Buckets"
  value       = aws_s3_bucket.data_lake.id
}

output "bucket_arn" {
  description = "ARN des S3 Buckets - wird fuer IAM Policies benoetigt"
  value       = aws_s3_bucket.data_lake.arn
}
