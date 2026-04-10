# CLAUDE.md — olist-analytics-pipeline

## Projektübersicht
Cloud-basierte ELT-Pipeline auf dem Olist Brazilian E-Commerce Dataset (Kaggle, CC BY-NC-SA 4.0).
Ziel: End-to-end Datenpipeline als Portfolio-Projekt nach Industriestandard und Best Practices.
Finales Deliverable: Power BI Dashboard mit 4 Business Questions und 6 SMART-KPIs.

## Stack
- Orchestrierung:   Apache Airflow 2.x (lokal Docker, Prod Amazon MWAA)
- Transformation:   AWS Glue (Bronze→Silver) · dbt Core (Silver→Gold, Redshift)
- Warehouse:        AWS Redshift Serverless
- Storage:          AWS S3 — Medallion Architecture: Bronze / Silver / Gold (Parquet)
- Datenqualität:    Great Expectations · dbt Tests
- IaC:              Terraform >= 1.5, AWS Provider
- CI/CD:            GitHub Actions
- Monitoring:       Grafana + AWS CloudWatch
- Visualisierung:   Power BI Desktop (ODBC → Redshift)
- Sprache:          Python 3.11, SQL

## Mein Level
- Angehender Data Engineer, DataOps Engineer, Data Analyst (Einsteiger-Praxis)
- Grundkenntnisse: Python, SQL, Excel
- Oberflächlich bekannt: AWS, Docker, S3, Kafka, Kubernetes
- Lerne gerade: Airflow, dbt, Great Expectations, Glue, Redshift, DataOps-Prinzipien
- Erkläre neue Konzepte immer kurz — nicht nur Code liefern
- Bei Architekturentscheidungen: 2 Optionen + Empfehlung zeigen
- Methodik: Agile CRISP-DM Hybrid (Phase 0–6, Sprint-basiert)

## Konventionen
dbt:      stg_ (view) → int_ (ephemeral) → fct_/dim_/kpi_ (table)
          Jedes Modell hat .yml mit Tests (not_null + unique auf PK, relationships auf FK)
          dbt docs generate nach jedem neuen Modell
Airflow:  owner, retries=3, retry_delay=5min, tags, doc_md Pflicht
          DAG-Namensschema: olist_<schicht>_<aktion> (z.B. olist_bronze_upload)
Python:   Type hints + Docstrings + Error handling + nur os.environ[] für Credentials
          Keine hardcodierten Werte — alles über .env
S3:       Bronze ist immutable — niemals überschreiben, nur anhängen
          Pfadschema: s3://olist-data-lake/<schicht>/<tabellenname>/
Terraform: Remote State in S3, common_tags auf allen Ressourcen
Git:      Feature Branches + Pull Requests, kein direktes Pushen in main
          Commits: feat / fix / docs / test / refactor / chore / ci

## Business Questions & KPIs
BQ-01  Welche Produkte und Kategorien bringen den meisten Umsatz?
BQ-02  Welche Regionen und Märkte performen am besten?
BQ-03  Wie lange dauert die Lieferung — wo gibt es Verzögerungen?
BQ-04  Wie zufrieden sind die Kunden und was beeinflusst Bewertungen?

KPIs:  Umsatz pro Kategorie · Umsatz pro Region · Ø Lieferdauer ·
       Anteil verspäteter Lieferungen · Ø Bewertungsscore · Korrelation Verzögerung/Bewertung

## Aktuelle Prioritäten
# Diesen Abschnitt nach jeder Session selbst aktualisieren
- [x] Project Brief v1 erstellt
- [x] CRISP-DM Projektplan erstellt
- [x] Technischer Pipeline-Aufbauplan erstellt
- [x] Notion Sprint Backlog aufgesetzt
- [x] GitHub Repository angelegt (ecomm_pipeline)
- [x] AWS-Account + Billing Alert konfigurieren
- [x] Kaggle API einrichten + Olist-Datensatz heruntergeladen
- [x] **Phase 1: EDA abgeschlossen**
  - [x] Jupyter-Umgebung einrichten (requirements.txt / .venv)
  - [x] EDA-Notebook je Tabelle: Shape, dtypes, Nulls, Duplikate
  - [x] Joins & Beziehungen zwischen Tabellen prüfen
  - [x] Befunde dokumentiert (notebooks/01_eda.ipynb, Zelle 12)
  - [x] Datenbeschaffenheit für Pipeline-Design abgeleitet
- [x] **Phase 2: Bronze Layer abgeschlossen**
  - [x] Projektstruktur anlegen (airflow/, glue/, dbt/, terraform/)
  - [x] AWS Infrastruktur mit Terraform aufsetzen (S3, IAM, Glue)
  - [x] Airflow DAG: olist_bronze_upload (CSV → S3 Bronze)
  - [x] Glue Job: Bronze → Silver (Cleaning, Parquet)
  - [ ] Redshift Serverless (ausstehend — Aktivierungsproblem)
- [x] **Phase 3: Silver → Gold (dbt) abgeschlossen**
  - [x] dbt Projekt initialisieren (dbt-duckdb lokal, Redshift ausstehend)
  - [x] Staging Modelle (8x stg_*) — inkl. Deduplizierung stg_order_reviews
  - [x] Intermediate Modelle (int_orders_enriched, int_delivery_times)
  - [x] Marts Modelle (fct_sales, fct_regional_performance, fct_delivery, fct_reviews)
  - [x] .yml Tests: 42/42 PASS (not_null, unique, relationships)
  - [x] dbt docs generate
- [x] **Phase 4: Datenqualität & CI/CD**
  - [x] Great Expectations Validierung (validate_silver.py — 5 Tabellen, 42 Checks)
  - [x] Pipeline Runner (run_pipeline.py — GE → dbt run → dbt test)
  - [ ] GitHub Actions Pipeline (dbt run + dbt test bei PR)
  - [ ] Redshift Serverless aktivieren + dbt auf Redshift umstellen

## Was ich NICHT will
- Keine überkomplexen Lösungen für ein Portfolio-Projekt
- Keine Libraries oder Services außerhalb des definierten Stacks
- Kein ClickhouseDB, kein Kafka, kein Kubernetes in dieser Pipeline
- Immer erklären WARUM, nicht nur WAS
- Keine Spekulationen — wenn etwas unklar ist, nachfragen
