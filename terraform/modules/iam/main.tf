# -------------------------------------------------------
# IAM Rollen für die olist Pipeline
# Glue, Airflow, Redshift
# -------------------------------------------------------


# -------------------------------------------------------
# 1. GLUE ROLLE
# -------------------------------------------------------

# Nur der Glue Service darf diese Rolle annehmen
data "aws_iam_policy_document" "glue_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue" {
  name               = "${var.project}-glue-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.glue_assume_role.json
  tags               = var.common_tags
}

# Glue darf im gesamten Bucket lesen und schreiben
data "aws_iam_policy_document" "glue_s3" {
  statement {
    sid       = "ListBucket"
    actions   = ["s3:ListBucket"]
    resources = [var.bucket_arn]
  }

  statement {
    sid       = "ReadWriteObjects"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${var.bucket_arn}/*"]
  }
}

resource "aws_iam_policy" "glue_s3" {
  name        = "${var.project}-glue-s3-policy-${var.environment}"
  description = "Erlaubt Glue den Zugriff auf den Data Lake S3 Bucket"
  policy      = data.aws_iam_policy_document.glue_s3.json
  tags        = var.common_tags
}

# AWS Managed Policy: enthält CloudWatch Logs + Glue Catalog Zugriff
resource "aws_iam_role_policy_attachment" "glue_managed" {
  role       = aws_iam_role.glue.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy_attachment" "glue_s3" {
  role       = aws_iam_role.glue.name
  policy_arn = aws_iam_policy.glue_s3.arn
}


# -------------------------------------------------------
# 2. AIRFLOW ROLLE
# -------------------------------------------------------

data "aws_iam_policy_document" "airflow_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["airflow.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "airflow" {
  name               = "${var.project}-airflow-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.airflow_assume_role.json
  tags               = var.common_tags
}

data "aws_iam_policy_document" "airflow_permissions" {
  # Glue Jobs starten und überwachen
  statement {
    sid = "GlueAccess"
    actions = [
      "glue:StartJobRun",
      "glue:GetJobRun",
      "glue:GetJobRuns",
      "glue:BatchStopJobRun"
    ]
    resources = ["*"]
  }

  # S3 für DAG Dateien und Logs
  statement {
    sid     = "S3Access"
    actions = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
    resources = [
      var.bucket_arn,
      "${var.bucket_arn}/*"
    ]
  }

  statement {
    sid     = "CloudWatchLogs"
    actions = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_policy" "airflow" {
  name        = "${var.project}-airflow-policy-${var.environment}"
  description = "Erlaubt Airflow Glue Jobs zu starten und S3 zu nutzen"
  policy      = data.aws_iam_policy_document.airflow_permissions.json
  tags        = var.common_tags
}

resource "aws_iam_role_policy_attachment" "airflow" {
  role       = aws_iam_role.airflow.name
  policy_arn = aws_iam_policy.airflow.arn
}


# -------------------------------------------------------
# 3. REDSHIFT ROLLE
# -------------------------------------------------------

data "aws_iam_policy_document" "redshift_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["redshift.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "redshift" {
  name               = "${var.project}-redshift-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.redshift_assume_role.json
  tags               = var.common_tags
}

# Redshift darf nur den Gold Layer lesen — Least Privilege Prinzip
data "aws_iam_policy_document" "redshift_s3" {
  statement {
    sid     = "S3ReadGold"
    actions = ["s3:GetObject", "s3:ListBucket"]
    resources = [
      var.bucket_arn,
      "${var.bucket_arn}/gold/*"
    ]
  }
}

resource "aws_iam_policy" "redshift_s3" {
  name        = "${var.project}-redshift-s3-policy-${var.environment}"
  description = "Erlaubt Redshift den Gold Layer aus S3 zu lesen"
  policy      = data.aws_iam_policy_document.redshift_s3.json
  tags        = var.common_tags
}

resource "aws_iam_role_policy_attachment" "redshift_s3" {
  role       = aws_iam_role.redshift.name
  policy_arn = aws_iam_policy.redshift_s3.arn
}
