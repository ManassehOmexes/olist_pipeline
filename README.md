# Olist E-Commerce Analytics Pipeline

E-commerce companies often struggle to answer fundamental business questions because data is scattered across multiple systems and reports are manually maintained.

This project demonstrates how a modern analytics platform can automatically transform raw operational data into reliable business insights.

[![CI](https://github.com/ManassehOmexes/olist_pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/ManassehOmexes/olist_pipeline/actions)
[![dbt](https://img.shields.io/badge/dbt-17%20models%20%7C%2049%20tests-FF694B?style=flat&logo=dbt&logoColor=white)](https://docs.getdbt.com)
[![AWS](https://img.shields.io/badge/AWS-Redshift%20%7C%20S3%20%7C%20Glue-FF9900?style=flat&logo=amazon-aws&logoColor=white)](https://aws.amazon.com)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-5835CC?style=flat&logo=terraform&logoColor=white)](https://www.terraform.io)
[![License](https://img.shields.io/badge/Dataset-CC%20BY--NC--SA%204.0-lightgrey?style=flat)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

Production-grade ELT pipeline on AWS using the [Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). Built to industry standard - automated testing, data quality gates, secrets management, CI/CD, disaster recovery.

**Business outcome:** Reduced manual reporting effort from hours to minutes while providing daily visibility into revenue, delivery performance and customer satisfaction.

---

## Architecture

```
[Kaggle CSV Files]
       │
       ▼ Airflow DAG (Volume Anomaly Check → Bronze Validation)
[S3 Bronze Layer]  ─ immutable, Object Lock, 30-day WORM
       │
       ▼ AWS Glue (Python Shell)
[S3 Silver Layer]  ─ Parquet, Great Expectations (49 checks)
       │
       ▼ dbt Core (17 models, 49 tests)
[Redshift Serverless / DuckDB]
       │
       ▼
[Power BI Dashboard]  ─ 4 pages, 4 business questions, 6 KPIs
```

**Medallion Architecture:** Bronze (raw, immutable) → Silver (cleaned Parquet) → Gold (business-ready mart tables)

**Cross-region replication:** S3 Bronze → eu-west-1 replica. RTO < 4h, RPO < 1h.

---

## DataOps Features

| Feature | Implementation |
|---|---|
| Volume Anomaly Detection | Row count compared to baseline after every sync. SNS alert + pipeline stop at >30% deviation |
| Bronze Validation Gate | Great Expectations schema + PK checks on all 9 tables before Glue runs |
| Silver Validation | 49 GE checks after transformation, before dbt |
| Automated Testing | 49 dbt tests (not_null, unique, relationships) on every push via GitHub Actions |
| Secrets Management | AWS Secrets Manager - no plaintext credentials anywhere in code |
| IaC | Full Terraform: S3, IAM, Glue, Redshift, Monitoring, Secrets Manager |
| State Management | Terraform remote state in S3 + DynamoDB locking |
| Monitoring | CloudWatch + SNS alerting on Glue failures and data anomalies |
| Data Lineage | OpenLineage + Marquez integration |
| Disaster Recovery | S3 CRR (eu-west-1), Object Lock (COMPLIANCE 30 days) |
| GDPR Compliance | PII masking via dbt macro, data retention policies, encryption at rest |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow 2.x (Docker) |
| Ingestion | Python + boto3 |
| Bronze → Silver | AWS Glue (Python Shell) |
| Silver → Gold | dbt Core - DuckDB (dev) / Redshift Serverless (prod) |
| Data Warehouse | AWS Redshift Serverless |
| Storage | AWS S3 - Medallion Architecture |
| Data Quality | Great Expectations + dbt Tests + dbt-expectations |
| IaC | Terraform >= 1.5 |
| CI/CD | GitHub Actions |
| Visualization | Power BI Desktop (ODBC) |
| Lineage | OpenLineage + Marquez |
| Language | Python 3.11, SQL |

---

## Business Questions & KPIs

| # | Question | KPI |
|---|---|---|
| BQ-01 | Which product categories generate the most revenue? | Revenue per category, MoM growth |
| BQ-02 | Which regions and markets perform best? | Revenue per state, order density |
| BQ-03 | How long does delivery take - where are the delays? | Avg. delivery days, late delivery rate % |
| BQ-04 | How satisfied are customers and what drives reviews? | Avg. review score, delay/rating correlation |

---

## dbt Models

```
models/
├── staging/          (8 models)   stg_orders, stg_customers, stg_order_items,
│                                  stg_order_payments, stg_order_reviews,
│                                  stg_products, stg_sellers, stg_geolocation
├── intermediate/     (3 models)   int_orders_enriched, int_delivery_times,
│                                  int_orders_complete
├── marts/            (5 models)   fct_sales, fct_regional_performance,
│                                  fct_delivery, fct_reviews, fct_company_performance
└── utils/            (1 model)    metricflow_time_spine
```

All 49 dbt tests pass. Semantic Layer (MetricFlow) integrated for metric definitions.

---

## Data Model

```
stg_orders ──────┬──── stg_customers     (customer_id)
                 ├──── stg_order_items   (order_id)
                 │         ├──── stg_products   (product_id)
                 │         └──── stg_sellers    (seller_id)
                 ├──── stg_order_reviews  (order_id)
                 └──── stg_order_payments (order_id)
```

---

## Project Structure

```
ecomm_pipeline/
├── airflow/
│   ├── dags/
│   │   ├── olist_bronze_upload.py      # Upload → Volume Check → Bronze Validation → Glue
│   │   └── olist_silver_to_gold.py     # Silver Validation → dbt run → dbt test
│   └── docker-compose.yml
├── glue/
│   └── jobs/
│       └── bronze_to_silver.py         # S3 Bronze → S3 Silver (Parquet)
├── dbt/
│   ├── models/                         # 17 models across 4 layers
│   ├── macros/
│   │   └── mask_pii.sql                # GDPR: PII pseudonymization
│   └── snapshots/
│       └── orders_snapshot.sql         # SCD Type 2 order status history
├── great_expectations/
│   ├── validate_bronze.py              # 9 tables, PK + row count checks
│   └── validate_silver.py              # 49 checks on Silver layer
├── terraform/
│   ├── main.tf                         # Remote state S3 + DynamoDB locking
│   └── modules/                        # s3, iam, glue, redshift, monitoring
├── .github/
│   └── workflows/
│       └── ci.yml                      # dbt test on every push to main
└── scripts/
    ├── airbyte_deploy.py
    └── run_dbt_with_lineage.py         # OpenLineage integration
```

---

## Setup

### Prerequisites

- Python 3.11
- Docker Desktop
- AWS account (S3, Glue, Redshift Serverless, IAM, Secrets Manager configured via Terraform)

### Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### Local Development

```bash
git clone https://github.com/ManassehOmexes/olist-analytics-pipeline.git
cd ecomm_pipeline

python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Linux/Mac

pip install dbt-duckdb great-expectations boto3 pandas pyarrow

cp .env.example .env
# Fill AWS credentials in .env
```

### Run the Pipeline

```bash
# PowerShell: load environment variables
Get-Content .env | Where-Object { $_ -match '=' -and $_ -notmatch '^#' } |
  ForEach-Object { $parts = $_ -split '=', 2; [System.Environment]::SetEnvironmentVariable($parts[0], $parts[1]) }

# Start Airflow locally
cd airflow && docker-compose up -d

# dbt (local, DuckDB)
cd dbt
dbt run --target dev
dbt test --target dev
dbt docs generate && dbt docs serve
```

---

## Dashboard

<img width="742" height="418" alt="Unternhemensperformance" src="https://github.com/user-attachments/assets/3318892f-8882-4338-8680-170a6fe1a7b5" />
<img width="734" height="416" alt="Sales" src="https://github.com/user-attachments/assets/f0dfe361-94fe-4bee-8a63-1a59f07436d2" />
<img width="747" height="416" alt="Regionen" src="https://github.com/user-attachments/assets/cefc5362-c99f-4d20-9380-9ff063a7bcb2" />
<img width="751" height="417" alt="Lieferung" src="https://github.com/user-attachments/assets/49c22ae7-aa38-47c3-a522-a9cd5de79823" />
<img width="747" height="419" alt="Bewertungen" src="https://github.com/user-attachments/assets/da7c8401-367a-44e9-8932-8efaef65ebca" />

<!-- Add screenshots here -->
| Page | Business Question |
|---|---|
| Revenue Overview | BQ-01: Revenue by category and product |
| Regional Performance | BQ-02: Revenue and order volume by state |
| Delivery Analysis | BQ-03: Delivery time, late rate, bottlenecks |
| Customer Satisfaction | BQ-04: Review score distribution, delay correlation |

---

## Dataset

[Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) - Kaggle, CC BY-NC-SA 4.0

~100,000 orders from 2016 to 2018 across multiple Brazilian marketplaces. 9 source tables.
