# -------------------------------------------------------
# Monitoring: SNS Topic + CloudWatch Alarm
# -------------------------------------------------------

# SNS Topic - Empfängt Alarme und sendet sie per Email weiter
resource "aws_sns_topic" "pipeline_alerts" {
  name = "${var.project}-alerts-${var.environment}"
  tags = var.common_tags
}

# SNS Subscription - Email-Benachrichtigung
resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.pipeline_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Alarm - Glue Job fehlgeschlagen
resource "aws_cloudwatch_metric_alarm" "glue_job_failed" {
  alarm_name          = "${var.project}-glue-job-failed-${var.environment}"
  alarm_description   = "Glue Job bronze-to-silver ist fehlgeschlagen"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "glue.driver.aggregate.numFailedTasks"
  namespace           = "Glue"
  period              = 300
  statistic           = "Sum"
  threshold           = 1

  dimensions = {
    JobName = var.glue_job_name
  }

  alarm_actions = [aws_sns_topic.pipeline_alerts.arn]
  ok_actions    = [aws_sns_topic.pipeline_alerts.arn]

  treat_missing_data = "notBreaching"

  tags = var.common_tags
}
