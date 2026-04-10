variable "project" {
  description = "Projektname als Prefix für Rollennamen"
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

variable "bucket_arn" {
  description = "ARN des S3 Data Lake Buckets — kommt als Output aus dem S3 Modul"
  type        = string
}
