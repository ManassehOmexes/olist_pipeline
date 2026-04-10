# -------------------------------------------------------
# Redshift Serverless
# Namespace (Datenbank) + Workgroup (Compute/Netzwerk)
# -------------------------------------------------------

# Namespace: enthält die Datenbank, User und Schemas
resource "aws_redshiftserverless_namespace" "main" {
  namespace_name      = "${var.project}-namespace-${var.environment}"
  db_name             = var.project
  admin_username      = "admin"
  admin_user_password = var.admin_password

  # Die IAM Rolle erlaubt Redshift S3 zu lesen (COPY Befehle)
  iam_roles = [var.redshift_role_arn]

  tags = var.common_tags
}

# Workgroup: definiert Netzwerk und Compute-Kapazität
resource "aws_redshiftserverless_workgroup" "main" {
  namespace_name = aws_redshiftserverless_namespace.main.namespace_name
  workgroup_name = "${var.project}-workgroup-${var.environment}"

  # 8 RPUs = Minimum, ausreichend für dev/portfolio
  base_capacity = var.base_capacity

  # Publicly accessible = true damit Power BI per ODBC verbinden kann
  publicly_accessible = true

  tags = var.common_tags
}
