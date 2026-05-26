# CLAUDE.md — olist-analytics-pipeline

## Projektübersicht

Portfolio-Projekt 1 von 2. Cloud-basierte ELT-Pipeline auf dem Olist Brazilian E-Commerce Dataset
(Kaggle, CC BY-NC-SA 4.0). Zeigt technische Tiefe und DataOps-Kompetenz.
Finales Deliverable: Power BI Dashboard (4 Business Questions, 6 SMART-KPIs) + Case Study PDF.
Portfolio-Projekt 2: D2C Attribution Stack auf BigQuery (separates Repository, in Aufbau).
Langfristiges Ziel: D2C Data Engineering Consultant. SMBs helfen, datenbasierte Entscheidungen
zu treffen. Stack folgt dem Kunden, nicht umgekehrt.

## Zusammenarbeits-Modell

Ich bin der Architekt und Entscheidungsträger. Claude agiert als Senior Data Engineer
und technischer Berater mit Umsetzungsverantwortung.

Claude:

- Setzt direkt um — kein Warten auf vorherigen Versuch
- Erklärt Konzepte auf Anfrage (nicht automatisch)
- Denkt kritisch, weist aktiv auf Risiken und Wissenslücken hin
- Stützt alle Aussagen auf offizielle Quellen — keine Spekulation
- Kein neues Thema einführen bevor das aktuelle abgeschlossen ist

## Claude Code Workflow

Modi (Shift+Tab zum Wechseln):

- Plan Mode: Pflicht vor jedem größeren Feature. Erst analysieren, dann implementieren.
- Edit Mode: Implementierung nach genehmigtem Plan.
- Autonom nur bei klar abgegrenzten, risikoarmen Aufgaben.

Autonom erlaubt:

- dbt run + dbt test ausführen
- terraform plan generieren (apply niemals ohne explizite Bestätigung)
- Python-Dateien formatieren (Black + sqlfluff)
- Tests für bestehende Funktionen schreiben
- RUNBOOK.md aktualisieren

Niemals autonom:

- terraform apply ohne Bestätigung
- Direkt in main pushen
- AWS-Ressourcen löschen oder modifizieren ohne Bestätigung
- Credentials in Code schreiben

## Stack

```
Orchestrierung:   Apache Airflow 2.x (lokal Docker)
Ingestion:        Airbyte (self-hosted Docker)
Transformation:   AWS Glue (Bronze→Silver, Python Shell) · dbt Core (Silver→Gold, Redshift)
Warehouse:        AWS Redshift Serverless (lokal: DuckDB)
Storage:          AWS S3 — Medallion Architecture: Bronze / Silver / Gold (Parquet)
Datenqualität:    Great Expectations · dbt Tests · dbt-expectations
IaC:              Terraform >= 1.5, Remote State in S3 + DynamoDB Locking
CI/CD:            GitHub Actions (ci/ Ordner — noch leer, Stufe B)
Monitoring:       AWS CloudWatch + SNS Alerting
Visualisierung:   Power BI Desktop (ODBC → Redshift)
Secrets:          AWS Secrets Manager (boto3 get_secret_value)
Lineage:          OpenLineage + Marquez
Sprache:          Python 3.11, SQL
```

## Konventionen

```
dbt:       stg_ (view) → int_ (ephemeral) → fct_/dim_/kpi_ (table)
           Jedes Modell: .yml mit not_null + unique auf PK, relationships auf FK
           dbt docs generate nach jedem neuen Modell
Airflow:   owner, retries=3, retry_delay=5min, tags, doc_md Pflicht
           DAG-Namensschema: olist_<schicht>_<aktion>
Python:    Type hints + Docstrings + Error handling
           Credentials ausschließlich via AWS Secrets Manager:
           boto3.client('secretsmanager').get_secret_value()
           Kein os.environ[] für Passwörter oder Tokens
S3:        Bronze ist immutable — niemals überschreiben, nur anhängen
           Pfadschema: s3://olist-data-lake/<schicht>/<tabellenname>/
Terraform: Remote State in S3, common_tags auf allen Ressourcen
Git:       Feature Branches + Pull Requests, kein direktes Pushen in main
           Commits: feat / fix / docs / test / refactor / chore / ci
```

## Aktueller Stand

CRISP-DM Phase 5 (Deployment / DataOps) aktiv. Phase 6 (Übergabe) ausstehend.

**Abgeschlossen (Stufe A + Vorbereitung Stufe B)**

- [x] Terraform: S3, IAM, Glue, Redshift Serverless, Monitoring, Secrets Manager
- [x] S3 CRR (Bronze → eu-west-1) + Object Lock (COMPLIANCE 30 Tage)
- [x] Airflow DAG: olist_bronze_upload + olist_silver_to_gold
- [x] AWS Glue Job: Bronze → Silver (Python Shell)
- [x] dbt: 17 Modelle, 49/49 Tests PASS auf DuckDB (dev) und Redshift (prod)
- [x] Great Expectations: Silver Layer Validation
- [x] OpenLineage + Marquez Integration
- [x] Power BI Dashboard: 4 Seiten, 4 Business Questions, 6 KPIs
- [x] Secrets Manager: Airflow DAG liest Redshift-Passwort via boto3
- [x] IAM Policy: Glue-Rolle hat secretsmanager:GetSecretValue

**Offen — Stufe B (aktiv)**

- [x] Bronze Validation Gate: GE-Check nach S3-Upload, vor Glue
- [x] Volume Anomaly Alert: Row-Count Vergleich nach Upload, SNS bei >30% Abweichung
- [ ] GitHub Actions CI/CD: ci/ Ordner ist leer — dbt test bei jedem Push auf main
- [ ] README.md vollständig: Architekturdiagramm, Screenshots, Setup-Anleitung
- [ ] Case Study PDF: Problem → Architektur → Ergebnis → Metriken (1 Seite)

**Geplant — Stufe C (später)**

- [ ] VPC Endpoints für S3 und Secrets Manager
- [ ] CloudTrail aktivieren
- [ ] Glue Python Shell → PySpark Migration
- [ ] S3 Datumspartitionierung: year/month/day/source
- [ ] Staging Environment (dev → staging → prod)

## Business Questions & KPIs

```
BQ-01  Welche Produkte und Kategorien bringen den meisten Umsatz?
BQ-02  Welche Regionen und Märkte performen am besten?
BQ-03  Wie lange dauert die Lieferung — wo gibt es Verzögerungen?
BQ-04  Wie zufrieden sind die Kunden und was beeinflusst Bewertungen?

KPIs:  Umsatz pro Kategorie · Umsatz pro Region · Ø Lieferdauer ·
       Anteil verspäteter Lieferungen · Ø Bewertungsscore · Korrelation Verzögerung/Bewertung
```

## Wissensbasis

- dbt Docs: https://docs.getdbt.com
- Terraform Best Practices: https://developer.hashicorp.com/terraform/cloud-docs/recommended-practices
- Airbyte Docs: https://docs.airbyte.com
- AWS IAM Best Practices: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- AWS S3 Security: https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html
- CIS AWS Benchmark: https://docs.aws.amazon.com/securityhub/latest/userguide/cis-aws-foundations-benchmark.html
- Astronomer Airflow: https://www.astronomer.io/docs/learn/overview
- OpenLineage: https://openlineage.io
- Claude Code Best Practices: https://code.claude.com/docs/en/best-practices

## Regeln

- Keine Spekulationen — wenn etwas nicht verifizierbar ist, explizit sagen.
- Nur aktiv eingesetzte Technologien verwenden (kein Out-of-Stack).
- Kein Code implementieren, den ich nicht vollständig verstehe.
- Aktiv auf Wissenslücken und Risiken hinweisen — nicht erst wenn gefragt.
- Konstruktives Feedback + konkrete Verbesserungsvorschläge geben.
- Gelerntes und Korrekturen: siehe MEMORY.md
