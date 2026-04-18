# -------------------------------------------------------
# AWS Glue Job: Bronze → Silver
# -------------------------------------------------------

# Glue Script nach S3 hochladen
resource "aws_s3_object" "bronze_to_silver_script" {
  bucket = var.bucket_id
  key    = "scripts/bronze_to_silver.py"
  source = "${path.module}/../../../glue/jobs/bronze_to_silver.py"
  etag   = filemd5("${path.module}/../../../glue/jobs/bronze_to_silver.py")
}

# Glue Job Definition
resource "aws_glue_job" "bronze_to_silver" {
  name     = "${var.project}-bronze-to-silver-${var.environment}"
  role_arn = var.glue_role_arn

  command {
    # Python Shell = kein Spark, günstiger, ausreichend für unsere Datenmenge
    name            = "pythonshell"
    script_location = "s3://${var.bucket_id}/scripts/bronze_to_silver.py"
    python_version  = "3.9"
  }

  glue_version = "3.0"

  default_arguments = {
    "--JOB_NAME"                        = "${var.project}-bronze-to-silver-${var.environment}"
    "--source_bucket"                   = var.bucket_id
    "--target_bucket"                   = var.bucket_id
    "--job-language"                    = "python"
    "--continuous-log-logGroup"         = "/aws-glue/jobs/${var.project}-${var.environment}"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"    = "true"
  }

  # 0.0625 DPU = kleinstes mögliches für Python Shell Jobs
  max_capacity = 0.0625

  # Bei transientem AWS-Fehler: bis zu 2 automatische Wiederholungsversuche
  max_retries = 2

  tags = var.common_tags
}

# Glue Crawler - katalogisiert Silver Parquet in Glue Data Catalog
# Notwendig damit Redshift Spectrum die Tabellen lesen kann
resource "aws_glue_crawler" "silver" {
  name          = "${var.project}-silver-crawler-${var.environment}"
  role          = var.glue_role_arn
  database_name = "${var.project}_silver_${var.environment}"

  s3_target {
    path = "s3://${var.bucket_id}/silver/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }

  tags = var.common_tags
}
