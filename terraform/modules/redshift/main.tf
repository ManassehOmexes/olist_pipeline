# -------------------------------------------------------
# Redshift Serverless
# Namespace (Datenbank) + Workgroup (Compute/Netzwerk)
# -------------------------------------------------------

# Security Group: öffnet Port 5439 für eingehende Verbindungen
# Notwendig damit dbt (lokal) und Power BI (ODBC) verbinden können
resource "aws_security_group" "redshift" {
  name        = "${var.project}-redshift-sg-${var.environment}"
  description = "Erlaubt eingehende Verbindungen auf Redshift Port 5439"

  ingress {
    from_port   = 5439
    to_port     = 5439
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Redshift Serverless - dbt + Power BI Zugriff"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.common_tags
}

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

  security_group_ids = [aws_security_group.redshift.id]

  tags = var.common_tags
}
