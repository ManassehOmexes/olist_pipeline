terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Lokaler State für jetzt - nach S3-Erstellung auf Remote State migrieren
  backend "local" {}
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.common_tags
  }
}

# --- S3 Modul ---
module "s3" {
  source = "./modules/s3"

  project     = var.project
  environment = var.environment
  common_tags = var.common_tags
}

# --- IAM Modul ---
# bucket_arn kommt als Output aus dem S3 Modul
module "iam" {
  source = "./modules/iam"

  project     = var.project
  environment = var.environment
  common_tags = var.common_tags
  bucket_arn  = module.s3.bucket_arn
}

# --- Glue Modul ---
module "glue" {
  source = "./modules/glue"

  project       = var.project
  environment   = var.environment
  common_tags   = var.common_tags
  glue_role_arn = module.iam.glue_role_arn
  bucket_id     = module.s3.bucket_id
}

# --- Monitoring Modul ---
module "monitoring" {
  source = "./modules/monitoring"

  project       = var.project
  environment   = var.environment
  common_tags   = var.common_tags
  alert_email   = var.alert_email
  glue_job_name = module.glue.job_name
}

# --- Redshift Serverless Modul ---
module "redshift" {
  source = "./modules/redshift"

  project           = var.project
  environment       = var.environment
  common_tags       = var.common_tags
  redshift_role_arn = module.iam.redshift_role_arn
  admin_password    = var.redshift_admin_password
}
