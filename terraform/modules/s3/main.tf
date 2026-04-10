# -------------------------------------------------------
# S3 Data Lake - Medallion Architecture
# Bronze (raw) → Silver (cleaned) → Gold (aggregated)
# -------------------------------------------------------

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
