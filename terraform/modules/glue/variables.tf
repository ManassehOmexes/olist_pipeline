variable "project" {
  description = "Projektname als Prefix"
  type        = string
}

variable "environment" {
  description = "Umgebung: dev | prod"
  type        = string
}

variable "common_tags" {
  description = "Tags für alle Ressourcen"
  type        = map(string)
}

variable "glue_role_arn" {
  description = "ARN der Glue IAM Rolle — kommt aus dem IAM Modul"
  type        = string
}

variable "bucket_id" {
  description = "Name des S3 Buckets — für Script-Upload und Job-Parameter"
  type        = string
}
