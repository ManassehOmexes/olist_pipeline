output "sns_topic_arn" {
  value       = aws_sns_topic.pipeline_alerts.arn
  description = "ARN des SNS Topics für Pipeline-Alarme"
}
