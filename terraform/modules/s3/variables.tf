variable "project" {
  description = "Projektname als Bucket-Prefix"
  type        = string
}

variable "environment" {
  description = "Umgebung: dev | prod"
  type        = string
}

variable "common_tags" {
  description = "Tags fuer alle Ressourcen"
  type        = map(string)
}
