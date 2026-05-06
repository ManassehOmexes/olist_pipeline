# Runbook - Olist Analytics Pipeline

This runbook describes how to diagnose and resolve common pipeline failures.

---

## Pipeline Overview

```
Airflow DAG (olist_bronze_upload)
    → S3 Bronze (raw CSV)
    → AWS Glue (bronze_to_silver)
    → S3 Silver (Parquet)
    → Great Expectations (validate_silver.py)
    → dbt run + dbt test
    → Gold Layer (DuckDB / Redshift)
    → Power BI Dashboard
```

Each step depends on the previous one. A failure in any step stops the pipeline.

---

## Alert: Airflow DAG Failed

**Symptoms:** DAG shows red in Airflow UI, no new data in S3 Bronze.

**Diagnosis:**
1. Open Airflow UI → DAGs → `olist_bronze_upload` → click the failed task
2. Check the logs for the error message
3. Common causes:

| Error | Cause | Fix |
|-------|-------|-----|
| `NoCredentialsError` | AWS credentials expired or missing | Rotate IAM credentials, update `.env` and Airflow connections |
| `NoSuchBucket` | S3 bucket name wrong | Check `S3_BUCKET` in `.env` matches actual bucket name |
| `AccessDenied` | IAM permissions insufficient | Check IAM policy allows `s3:PutObject` on the bucket |
| `FileNotFoundError` | CSV file missing in `data/raw/` | Re-download dataset from Kaggle |

**Resolution:**
```bash
# After fixing the root cause, clear and re-run the failed task
# Airflow UI → Task → Clear → Run
```

---

## Alert: Glue Job Failed

**Symptoms:** S3 Silver is empty or outdated, Glue console shows job failure.

**Diagnosis:**
1. AWS Console → Glue → Jobs → `bronze_to_silver` → Run history → View logs
2. Common causes:

| Error | Cause | Fix |
|-------|-------|-----|
| `NoSuchKey` | Bronze file not found on S3 | Check if Airflow DAG ran successfully first |
| `ModuleNotFoundError` | Python library missing | Upgrade to Glue 3.0, check `--additional-python-modules` |
| `ParquetException` | Corrupt input data | Check Bronze CSV for encoding issues |

**Resolution:**
```bash
# Re-run Glue job manually from AWS Console
# or trigger via CLI:
aws glue start-job-run --job-name bronze_to_silver
```

---

## Alert: Great Expectations Validation Failed

**Symptoms:** `run_pipeline.py` exits with error, dbt does not start.

**Diagnosis:**
```bash
python great_expectations/validate_silver.py
```

Read the log output - it shows exactly which table, which column, and which expectation failed.

**Common causes and fixes:**

| Expectation Failed | Likely Cause | Fix |
|-------------------|--------------|-----|
| `ExpectTableRowCountToBeBetween` | Glue job only partially completed | Re-run Glue job, check for errors |
| `ExpectColumnValuesToNotBeNull` | New nulls in source data | Add null handling in `glue/jobs/bronze_to_silver.py` |
| `ExpectColumnValuesToBeInSet` | New category value in source | Update `value_set` in the expectation suite |
| `ExpectColumnValuesToBeUnique` | Duplicate PKs in Silver | Add deduplication in Glue job |

**Resolution:** Fix the root cause in the Glue job, re-run Glue, then re-run the pipeline:
```bash
python run_pipeline.py
```

---

## Alert: dbt Run Failed

**Symptoms:** `run_pipeline.py` reports `dbt run fehlgeschlagen`, Gold tables not updated.

**Diagnosis:**
```bash
cd dbt
dbt run --no-partial-parse
```

Check the output for which model failed.

**Common causes:**

| Error | Cause | Fix |
|-------|-------|-----|
| `Column not found` | Silver schema changed | Update staging model SQL |
| `relation does not exist` | Upstream model failed | Fix the upstream model first |
| `DuckDB file locked` | VS Code DuckDB extension has file open | Disconnect extension, retry |
| `S3 access denied` | AWS credentials not loaded | Load `.env` variables, retry |

**Resolution:**
```bash
# Run only the failed model and its dependencies
dbt run --select +failed_model_name --no-partial-parse
```

---

## Alert: dbt Tests Failed

**Symptoms:** `run_pipeline.py` reports `dbt test fehlgeschlagen`.

**Diagnosis:**
```bash
cd dbt
dbt test --no-partial-parse
```

**Common causes:**

| Test Failed | Likely Cause | Fix |
|-------------|--------------|-----|
| `not_null` on PK | Upstream data has nulls | Add null filter in staging model |
| `unique` on PK | Duplicates in source data | Add `ROW_NUMBER()` deduplication in staging |
| `relationships` | FK mismatch between tables | Check join keys in intermediate model |

---

## Alert: GitHub Actions Pipeline Failed

**Symptoms:** Red X on commit in GitHub, PR blocked.

**Diagnosis:**
1. GitHub → Actions → failed workflow → click the failed step
2. Read the log output

**Common causes:**

| Error | Cause | Fix |
|-------|-------|-----|
| `KeyError: AWS_ACCESS_KEY_ID` | GitHub Secret missing or wrong name | Settings → Secrets → verify all 4 secrets exist |
| `dbt deps failed` | `packages.yml` missing or wrong package | Check `dbt/packages.yml` |
| `No module named X` | Dependency not in workflow `pip install` | Add missing package to workflow install step |

---

## Manual Pipeline Run

When running locally, always load environment variables first:

```powershell
# PowerShell
Get-Content .env | Where-Object { $_ -match '=' -and $_ -notmatch '^#' } | ForEach-Object { $parts = $_ -split '=', 2; [System.Environment]::SetEnvironmentVariable($parts[0], $parts[1]) }
```

Then run the pipeline:
```bash
python run_pipeline.py
```

---

## Disaster Recovery

### SLA-Definition

| Kennzahl                           | Wert        | Bedeutung                                                      |
|------------------------------------|-------------|----------------------------------------------------------------|
| **RTO** (Recovery Time Objective)  | 4 Stunden   | Maximale Zeit bis die Pipeline nach einem Ausfall wieder läuft |
| **RPO** (Recovery Point Objective) | 24 Stunden  | Maximaler akzeptabler Datenverlust (ein Tages-Batch)           |

### S3 Object Lock — Bronze-Schutz

Bronze-Objekte sind im COMPLIANCE-Modus für 30 Tage gesperrt. Das bedeutet:

- Kein Nutzer kann ein Bronze-Objekt in den ersten 30 Tagen löschen — auch kein Admin oder Root-User
- S3 gibt bei Löschversuchen einen `AccessDenied`-Fehler zurück
- Nach 30 Tagen greift die Lifecycle-Policy: Bronze → Glacier Instant Retrieval

**Was tun wenn ein Bronze-Objekt versehentlich überschrieben wurde?**

Da Versionierung aktiv ist, existiert die alte Version noch:
```bash
# Alle Versionen eines Objekts auflisten
aws s3api list-object-versions \
  --bucket olist-data-lake-dev \
  --prefix bronze/olist_orders/

# Alte Version wiederherstellen (VersionId aus dem Output oben)
aws s3api copy-object \
  --copy-source olist-data-lake-dev/bronze/olist_orders/FILE.parquet?versionId=VERSIONID \
  --bucket olist-data-lake-dev \
  --key bronze/olist_orders/FILE.parquet
```

### S3 Cross-Region Replication — Wiederherstellung

Wenn eu-central-1 (Primär-Region) ausfällt, sind Bronze-Daten in eu-west-1 verfügbar.

```bash
# Daten aus Replica-Bucket lesen (temporär auf eu-west-1 zeigen)
aws s3 ls s3://olist-data-lake-dev-replica/bronze/ --region eu-west-1
```

RTO-Uhr startet sobald ein Region-Ausfall bestätigt ist. Ziel: Pipeline in eu-west-1 in unter 4 Stunden neu aufgesetzt.

### Redshift Serverless — Recovery Points (bekannte AWS-Einschränkung)

Redshift Serverless erstellt automatisch Recovery Points (interne Snapshots).

**Wichtige Einschränkung:** Die Retention-Dauer ist fest auf **24 Stunden** gesetzt.
Sie kann weder über Terraform noch über die AWS API verlängert werden.
Das Argument `snapshot_retention_period` existiert nur bei `aws_redshift_cluster` (provisioned) — nicht bei `aws_redshiftserverless_namespace`.

**Bedeutung für unser SLA:**

- RPO = 24 Stunden → passt zur automatischen 24h-Retention ✅
- Für längere Retention: manuelle Snapshots per CLI oder `aws_redshiftserverless_snapshot` in Terraform

**Manuellen Snapshot erstellen (bei geplanten Wartungsarbeiten oder vor großen Migrationen):**

```bash
# Manuellen Snapshot erstellen
aws redshift-serverless create-snapshot \
  --namespace-name olist-namespace-dev \
  --snapshot-name olist-manual-snapshot-$(date +%Y%m%d)

# Vorhandene Snapshots auflisten
aws redshift-serverless list-snapshots \
  --namespace-name olist-namespace-dev

# Namespace aus Snapshot wiederherstellen (erstellt neuen Namespace)
aws redshift-serverless restore-from-snapshot \
  --namespace-name olist-namespace-restored \
  --workgroup-name olist-workgroup-restored \
  --snapshot-name olist-manual-snapshot-20260101
```

---

## Useful Commands

```bash
# Check S3 Silver contents
aws s3 ls s3://olist-data-lake-dev/silver/ --recursive

# Run specific dbt model
cd dbt && dbt run --select model_name

# Run dbt tests for one model
cd dbt && dbt test --select model_name

# Validate Silver manually
python great_expectations/validate_silver.py

# Export Gold to CSV for Power BI
python scripts/export_to_csv.py
```
