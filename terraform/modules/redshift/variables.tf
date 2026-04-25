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

variable "redshift_role_arn" {
  description = "ARN der Redshift IAM Rolle - kommt aus dem IAM Modul"
  type        = string
}

variable "admin_password" {
  description = "Admin Passwort für Redshift - wird aus .env geladen, nie hardcoden"
  type        = string
  sensitive   = true
}

variable "base_capacity" {
  description = "Minimale Kapazität in RPUs (Redshift Processing Units). 8 = kleinstes möglich"
  type        = number
  default     = 8
}

variable "aws_region" {
  description = "AWS Region — wird im Secrets Manager Eintrag als Host-Teil gespeichert"
  type        = string
}
