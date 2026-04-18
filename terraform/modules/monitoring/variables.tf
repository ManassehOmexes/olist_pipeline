variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "common_tags" {
  type = map(string)
}

variable "alert_email" {
  type        = string
  description = "Email-Adresse für Pipeline-Alarme"
}

variable "glue_job_name" {
  type        = string
  description = "Name des Glue Jobs der überwacht werden soll"
}
