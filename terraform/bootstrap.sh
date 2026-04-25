#!/usr/bin/env bash
# bootstrap.sh — Schritt 1 beim Deployment in einem frischen AWS Account.
#
# Löst das Chicken-and-Egg Problem:
# Terraform benötigt S3-Bucket + DynamoDB vor dem ersten `terraform init`,
# aber beide werden normalerweise von Terraform selbst erstellt.
#
# Dieses Skript erstellt nur die Voraussetzungen per AWS CLI,
# danach übernimmt Terraform den Rest.
#
# Aufruf: bash bootstrap.sh <bucket-name> <region> <project>
# Beispiel: bash bootstrap.sh olist-data-lake-dev eu-central-1 olist

set -euo pipefail

BUCKET=${1:-"olist-data-lake-dev"}
REGION=${2:-"eu-central-1"}
PROJECT=${3:-"olist"}
DYNAMO_TABLE="${PROJECT}-terraform-locks"

echo "==> Bootstrap: S3 Bucket + DynamoDB für Terraform State"
echo "    Bucket:  $BUCKET"
echo "    Region:  $REGION"
echo "    DynDB:   $DYNAMO_TABLE"
echo ""

# S3 Bucket erstellen (idempotent: Fehler wenn schon existiert wird ignoriert)
if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "[OK] Bucket $BUCKET existiert bereits"
else
  echo "[-->] Erstelle S3 Bucket..."
  if [ "$REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
  else
    aws s3api create-bucket \
      --bucket "$BUCKET" \
      --region "$REGION" \
      --create-bucket-configuration LocationConstraint="$REGION"
  fi
  echo "[OK] Bucket erstellt"
fi

# Versioning aktivieren
aws s3api put-bucket-versioning \
  --bucket "$BUCKET" \
  --versioning-configuration Status=Enabled
echo "[OK] Versioning aktiviert"

# Encryption aktivieren
aws s3api put-bucket-encryption \
  --bucket "$BUCKET" \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}
    }]
  }'
echo "[OK] Encryption aktiviert"

# Public Access blockieren
aws s3api put-public-access-block \
  --bucket "$BUCKET" \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
echo "[OK] Public Access blockiert"

# DynamoDB Table für State Locking
if aws dynamodb describe-table --table-name "$DYNAMO_TABLE" --region "$REGION" 2>/dev/null; then
  echo "[OK] DynamoDB Table $DYNAMO_TABLE existiert bereits"
else
  echo "[-->] Erstelle DynamoDB Table..."
  aws dynamodb create-table \
    --table-name "$DYNAMO_TABLE" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region "$REGION"
  echo "[OK] DynamoDB Table erstellt"
fi

echo ""
echo "==> Bootstrap abgeschlossen. Nächste Schritte:"
echo "    1. cp terraform.tfvars.example terraform.tfvars"
echo "    2. Werte in terraform.tfvars eintragen"
echo "    3. terraform init"
echo "    4. terraform apply"
