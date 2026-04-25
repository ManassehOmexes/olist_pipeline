# -------------------------------------------------------
# IAM Rollen für die olist Pipeline
# Glue, Airflow, Redshift
# -------------------------------------------------------

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}


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
  # Glue Jobs starten und überwachen — nur Jobs dieses Projekts
  statement {
    sid = "GlueAccess"
    actions = [
      "glue:StartJobRun",
      "glue:GetJobRun",
      "glue:GetJobRuns",
      "glue:BatchStopJobRun"
    ]
    resources = [
      "arn:aws:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:job/${var.project}-*"
    ]
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

  # Secrets Manager — Redshift-Credentials lesen
  # Warum: Airflow DAGs lesen das Passwort aus SM statt aus Umgebungsvariablen
  statement {
    sid     = "SecretsManagerRead"
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.project}/redshift/*"
    ]
  }

  # CloudWatch Logs — nur Pipeline-relevante Log Groups
  statement {
    sid     = "CloudWatchLogs"
    actions = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = [
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws-glue/*",
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/airflow/*"
    ]
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

# Redshift Spectrum: S3 Silver lesen + Glue Catalog Zugriff
data "aws_iam_policy_document" "redshift_s3" {
  statement {
    sid     = "S3ReadSilver"
    actions = ["s3:GetObject", "s3:ListBucket"]
    resources = [
      var.bucket_arn,
      "${var.bucket_arn}/silver/*"
    ]
  }

  statement {
    sid = "GlueCatalogRead"
    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetTable",
      "glue:GetTables",
      "glue:GetPartition",
      "glue:GetPartitions",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "redshift_s3" {
  name        = "${var.project}-redshift-s3-policy-${var.environment}"
  description = "Erlaubt Redshift Spectrum den Silver Layer und Glue Catalog zu lesen"
  policy      = data.aws_iam_policy_document.redshift_s3.json
  tags        = var.common_tags
}

resource "aws_iam_role_policy_attachment" "redshift_s3" {
  role       = aws_iam_role.redshift.name
  policy_arn = aws_iam_policy.redshift_s3.arn
}
