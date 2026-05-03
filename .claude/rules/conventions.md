# Projekt-Konventionen

## dbt Modell-Naming

| Schicht | Präfix | Materialisierung | Beispiel |
|---------|--------|-----------------|---------|
| Staging | `stg_` | view | `stg_orders` |
| Intermediate | `int_` | ephemeral | `int_orders_enriched` |
| Marts | `fct_` / `dim_` / `kpi_` | table | `fct_revenue` |

Jedes Modell braucht eine `.yml`-Datei mit Tests:
- PK: `not_null` + `unique`
- FK: `relationships` (ohne `arguments:` wrapper)

## Airflow DAG-Naming

Schema: `olist_<schicht>_<aktion>`

Beispiele: `olist_bronze_upload`, `olist_silver_to_gold`

Pflichtfelder in `default_args`: `owner`, `retries=3`, `retry_delay=timedelta(minutes=5)`  
Pflichtfelder im DAG: `tags`, `doc_md`

## S3 Pfadschema

```
s3://olist-data-lake-dev/<schicht>/<tabellenname>/<tabellenname>.<ext>
```

Bronze ist **immutable** — niemals überschreiben, nur anhängen.

## Python Credentials

Ausschließlich `os.environ['KEY']` — niemals Werte hardcoden.  
Keine `.env`-Dateien committen.

## Terraform

Remote State in S3, `common_tags` auf allen Ressourcen.  
Kein ClickOps — alles über Terraform.

## Naming — Keine Bindestriche

Alle selbst definierten Bezeichner verwenden Unterstriche (`_`), keine Bindestriche (`-`).

| Kontext | Richtig | Falsch |
|---------|---------|--------|
| dbt Modelle | `stg_orders` | `stg-orders` |
| Python Funktionen / Variablen | `upload_file` | `upload-file` |
| Airflow DAGs | `olist_bronze_upload` | `olist-bronze-upload` |
| Terraform Ressourcen (Name-Attribut) | `s3_replication` | `s3-replication` |
| SQL Spalten / Aliases | `order_count` | `order-count` |

**Ausnahmen (AWS erzwingt Bindestriche):**  
S3 Bucket-Namen (`olist-data-lake-dev`) und AWS-Ressourcen-Namen wo Unterstriche nicht erlaubt sind.
