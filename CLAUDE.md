# CLAUDE.md — olist-analytics-pipeline

## Project Overview

Portfolio project 1 of 2. Cloud-based ELT pipeline on the Olist Brazilian E-Commerce Dataset
(Kaggle, CC BY-NC-SA 4.0). Demonstrates technical depth and DataOps competence.
Final deliverable: Power BI Dashboard (4 Business Questions, 6 SMART KPIs) + Case Study PDF.
Portfolio project 2: D2C Attribution Stack on BigQuery (separate repository, in progress).
Long-term goal: D2C Data Engineering Consultant. Help SMBs make data-driven decisions.
Stack follows the client, not the other way around.

## Collaboration Model

I am the architect and decision-maker. Claude acts as Senior Data Engineer
and technical advisor with implementation responsibility.

Claude:

- Implements directly — no waiting for prior attempts
- Explains concepts on request (not automatically)
- Thinks critically, actively flags risks and knowledge gaps
- Bases all statements on official sources — no speculation
- Does not introduce new topics before the current one is finished

## Claude Code Workflow

Modes (Shift+Tab to switch):

- Plan Mode: Required before any major feature. Analyze first, then implement.
- Edit Mode: Implementation after approved plan.
- Autonomous only for clearly scoped, low-risk tasks.

Autonomous allowed:

- Run dbt run + dbt test
- Generate terraform plan (apply never without explicit confirmation)
- Format Python files (Black + sqlfluff)
- Write tests for existing functions
- Update RUNBOOK.md

Never autonomous:

- terraform apply without confirmation
- Push directly to main
- Delete or modify AWS resources without confirmation
- Write credentials in code

## Stack

```
Orchestration:    Apache Airflow 2.x (local Docker)
Ingestion:        Airbyte (self-hosted Docker)
Transformation:   AWS Glue (Bronze→Silver, Python Shell) · dbt Core (Silver→Gold, Redshift)
Warehouse:        AWS Redshift Serverless (local: DuckDB)
Storage:          AWS S3 — Medallion Architecture: Bronze / Silver / Gold (Parquet)
Data Quality:     Great Expectations · dbt Tests · dbt-expectations
IaC:              Terraform >= 1.5, Remote State in S3 + DynamoDB Locking
CI/CD:            GitHub Actions (ci/ folder)
Monitoring:       AWS CloudWatch + SNS Alerting
Visualization:    Power BI Desktop (ODBC → Redshift)
Secrets:          AWS Secrets Manager (boto3 get_secret_value)
Lineage:          OpenLineage + Marquez
Language:         Python 3.11, SQL
```

## Conventions

```
dbt:       stg_ (view) → int_ (ephemeral) → fct_/dim_/kpi_ (table)
           Every model: .yml with not_null + unique on PK, relationships on FK
           dbt docs generate after every new model
Airflow:   owner, retries=3, retry_delay=5min, tags, doc_md required
           DAG naming scheme: olist_<layer>_<action>
Python:    Type hints + Docstrings + Error handling
           Credentials exclusively via AWS Secrets Manager:
           boto3.client('secretsmanager').get_secret_value()
           No os.environ[] for passwords or tokens
S3:        Bronze is immutable — never overwrite, append only
           Path schema: s3://olist-data-lake/<layer>/<table_name>/
Terraform: Remote state in S3, common_tags on all resources
Git:       Feature branches + pull requests, no direct push to main
           Commits: feat / fix / docs / test / refactor / chore / ci
```

## Current Status

CRISP-DM Phase 5 (Deployment / DataOps) active. Phase 6 (Handover) pending.

### Completed (Stage A + Stage B preparation)

- [x] Terraform: S3, IAM, Glue, Redshift Serverless, Monitoring, Secrets Manager
- [x] S3 CRR (Bronze → eu-west-1) + Object Lock (COMPLIANCE 30 days)
- [x] Airflow DAG: olist_bronze_upload + olist_silver_to_gold
- [x] AWS Glue Job: Bronze → Silver (Python Shell)
- [x] dbt: 17 models, 49/49 tests PASS on DuckDB (dev) and Redshift (prod)
- [x] Great Expectations: Silver Layer Validation
- [x] OpenLineage + Marquez Integration
- [x] Power BI Dashboard: 4 pages, 4 Business Questions, 6 KPIs
- [x] Secrets Manager: Airflow DAG reads Redshift password via boto3
- [x] IAM Policy: Glue role has secretsmanager:GetSecretValue

### Open — Stage B (active)

- [x] Bronze Validation Gate: GE check after S3 upload, before Glue
- [x] Volume Anomaly Alert: Row count comparison after upload, SNS at >30% deviation
- [x] GitHub Actions CI/CD: ci.yml + ci/run_dbt_ci.sh — dbt test on every push to main
- [x] README.md complete: architecture diagram, screenshots, setup guide
- [x] Case Study PDF: Problem → Architecture → Result → Metrics (1 page)

### Planned — Stage C (later)

- [ ] VPC Endpoints for S3 and Secrets Manager
- [ ] Enable CloudTrail
- [ ] Glue Python Shell → PySpark Migration
- [ ] S3 date partitioning: year/month/day/source
- [ ] Staging Environment (dev → staging → prod)

## Business Questions & KPIs

```
BQ-01  Which products and categories generate the most revenue?
BQ-02  Which regions and markets perform best?
BQ-03  How long does delivery take — where are the delays?
BQ-04  How satisfied are customers and what influences reviews?

KPIs:  Revenue per category · Revenue per region · Avg. delivery time ·
       Late delivery rate · Avg. review score · Delay/review correlation
```

## Knowledge Base

- dbt Docs: https://docs.getdbt.com
- Terraform Best Practices: https://developer.hashicorp.com/terraform/cloud-docs/recommended-practices
- Airbyte Docs: https://docs.airbyte.com
- AWS IAM Best Practices: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- AWS S3 Security: https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html
- CIS AWS Benchmark: https://docs.aws.amazon.com/securityhub/latest/userguide/cis-aws-foundations-benchmark.html
- Astronomer Airflow: https://www.astronomer.io/docs/learn/overview
- OpenLineage: https://openlineage.io
- Claude Code Best Practices: https://code.claude.com/docs/en/best-practices

## Rules

- No speculation — if something cannot be verified, state it explicitly.
- Only use actively deployed technologies (no out-of-stack tools).
- Do not implement code that I do not fully understand.
- Actively flag knowledge gaps and risks — not only when asked.
- Provide constructive feedback and concrete improvement suggestions.
- Learnings and corrections: see MEMORY.md
