variable "aws_region" {
  description = "AWS Region fuer alle Ressourcen"
  type        = string
  default     = "eu-central-1"
}

variable "replica_region" {
  description = "AWS Region fuer den S3 Replica-Bucket (Disaster Recovery)"
  type        = string
  default     = "eu-west-1"
}

variable "project" {
  description = "Projektname - wird als Prefix in Ressourcennamen verwendet"
  type        = string
  default     = "olist"
}

variable "environment" {
  description = "Umgebung: dev | prod"
  type        = string
  default     = "dev"
}

variable "alert_email" {
  description = "Email-Adresse fuer Pipeline-Failure-Alarme"
  type        = string
}

variable "redshift_admin_password" {
  description = "Admin Passwort für Redshift Serverless - aus .env laden"
  type        = string
  sensitive   = true
}

variable "common_tags" {
  description = "Tags die auf alle Ressourcen angewendet werden"
  type        = map(string)
  default = {
    Project     = "olist-analytics-pipeline"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}
