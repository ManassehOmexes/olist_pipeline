# MEMORY.md — Gelernte Korrekturen

## Encoding
- Node.js/docx npm: JavaScript String Literals defaulten zu ae/oe/ue.
  Fix: Unicode Umlaut-Zeichen (ä ö ü ß) direkt in alle deutschen String Literals einbetten.

## Credentials
- Niemals os.environ[] für Passwörter oder Tokens.
  Fix: boto3.client('secretsmanager').get_secret_value() für alle Secrets.
  Secret Name Pattern: {project}/redshift/admin-password/{environment}

## dbt Target
- Lokale Verifikation immer mit --target dev (DuckDB), nicht prod.
  Grund: Redshift kostet, DuckDB ist deterministisch und schnell.
  Ausnahme: expliziter Prod-Test nach Infrastruktur-Änderungen.

## Terraform
- terraform apply nur nach explizitem terraform plan Review.
  Niemals autonom. Kein Destroy ohne schriftliche Bestätigung.

## Git
- Commits auf Deutsch mit englischen Fachbegriffen.
  Schema: feat / fix / docs / test / refactor / chore / ci
  Beispiel: "feat: bronze validation gate — 9 tabellen, ge checks vor glue start"

## PowerShell (Windows)
- head existiert nicht. Stattdessen: Select-Object -First N
- find existiert anders als Unix. Stattdessen: Get-ChildItem -Recurse
- Immer aus Projekt-Root arbeiten (C:\Projects\ecomm_pipeline)
