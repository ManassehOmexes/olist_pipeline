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
    "--JOB_NAME"      = "${var.project}-bronze-to-silver-${var.environment}"
    "--source_bucket" = var.bucket_id
    "--target_bucket" = var.bucket_id
    "--job-language"  = "python"
  }

  # 0.0625 DPU = kleinstes mögliches für Python Shell Jobs
  max_capacity = 0.0625

  tags = var.common_tags
}
