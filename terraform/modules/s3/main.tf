# -------------------------------------------------------
# S3 Data Lake - Medallion Architecture
# Bronze (raw) → Silver (cleaned) → Gold (aggregated)
# -------------------------------------------------------

# Deklariert den aws.replica Provider-Alias als Anforderung dieses Moduls.
# Der Root-Provider übergibt ihn via providers-Map im module-Block.
terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      configuration_aliases = [aws.replica]
    }
  }
}

locals {
  bucket_name = "${var.project}-data-lake-${var.environment}"
}

# --- Data Lake Bucket ---
resource "aws_s3_bucket" "data_lake" {
  bucket = local.bucket_name

  tags = merge(var.common_tags, {
    Name = local.bucket_name
  })
}

# Versionierung: Bei Fehlern kann man zu einem früheren Stand zurück
resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Verschlüsselung: Daten im Bucket werden verschlüsselt gespeichert
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Öffentlichen Zugriff blockieren - Bucket ist nur intern erreichbar
resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- Ordnerstruktur (Medallion Layer als S3 Prefixes) ---
# S3 hat keine echten Ordner - leere Objekte simulieren die Struktur
resource "aws_s3_object" "bronze" {
  bucket = aws_s3_bucket.data_lake.id
  key    = "bronze/"
}

resource "aws_s3_object" "silver" {
  bucket = aws_s3_bucket.data_lake.id
  key    = "silver/"
}

resource "aws_s3_object" "gold" {
  bucket = aws_s3_bucket.data_lake.id
  key    = "gold/"
}

# Glue Scripts werden hier abgelegt bevor der Job sie ausführt
resource "aws_s3_object" "scripts" {
  bucket = aws_s3_bucket.data_lake.id
  key    = "scripts/"
}

# Lifecycle: Bronze nach 30 Tagen nach Glacier Instant Retrieval verschieben
# Glacier IR: 68% günstiger als Standard, Zugriff in Millisekunden
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "bronze-to-glacier-ir"
    status = "Enabled"

    filter {
      prefix = "bronze/"
    }

    transition {
      days          = 30
      storage_class = "GLACIER_IR"
    }
  }

  rule {
    id     = "silver-to-ia"
    status = "Enabled"

    filter {
      prefix = "silver/"
    }

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
  }
}

# --- S3 Cross-Region Replication (CRR) ---

# Replica-Bucket in der Disaster-Recovery-Region (default: eu-west-1)
resource "aws_s3_bucket" "replica" {
  bucket   = "${var.project}-data-lake-${var.environment}-replica"
  provider = aws.replica

  tags = merge(var.common_tags, {
    Name = "${var.project}-data-lake-${var.environment}-replica"
  })
}

# CRR-Pflicht: Versionierung muss auf dem Replica-Bucket aktiv sein
resource "aws_s3_bucket_versioning" "replica" {
  bucket   = aws_s3_bucket.replica.id
  provider = aws.replica

  versioning_configuration {
    status = "Enabled"
  }
}

# Öffentlichen Zugriff auf Replica-Bucket blockieren
resource "aws_s3_bucket_public_access_block" "replica" {
  bucket   = aws_s3_bucket.replica.id
  provider = aws.replica

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM Role: erlaubt dem S3-Service das Kopieren von Objekten zwischen Buckets
resource "aws_iam_role" "s3_replication" {
  name = "${var.project}-s3-replication-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "s3.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = var.common_tags
}

# IAM Policy: Lesen aus Source-Bucket, Schreiben in Replica-Bucket
resource "aws_iam_role_policy" "s3_replication" {
  name = "${var.project}-s3-replication-policy-${var.environment}"
  role = aws_iam_role.s3_replication.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetReplicationConfiguration", "s3:ListBucket"]
        Resource = aws_s3_bucket.data_lake.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Resource = "${aws_s3_bucket.data_lake.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ]
        Resource = "${aws_s3_bucket.replica.arn}/*"
      }
    ]
  })
}

# Replication Configuration: nur bronze/ wird repliziert.
# Silver/Gold sind aus Bronze reproduzierbar — kein Replica nötig.
resource "aws_s3_bucket_replication_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  role   = aws_iam_role.s3_replication.arn

  rule {
    id     = "bronze-replication"
    status = "Enabled"

    filter {
      prefix = "bronze/"
    }

    delete_marker_replication {
      status = "Enabled"
    }

    destination {
      bucket = aws_s3_bucket.replica.arn
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.data_lake,
    aws_s3_bucket_versioning.replica,
    aws_iam_role_policy.s3_replication
  ]
}
