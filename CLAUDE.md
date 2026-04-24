# CLAUDE.md — olist-analytics-pipeline

## Projektübersicht

Cloud-basierte ELT-Pipeline auf dem Olist Brazilian E-Commerce Dataset (Kaggle, CC BY-NC-SA 4.0).
Ziel: End-to-end Datenpipeline als Portfolio-Projekt nach Industriestandard und Best Practices.
Finales Deliverable: Power BI Dashboard mit 4 Business Questions und 6 SMART-KPIs.
Langfristiges Ziel: Pipeline als reproduzierbares Asset — Data Pipeline as a Service (DPaaS).

## Stack

- Orchestrierung:   Apache Airflow 2.x (lokal Docker, Prod Amazon MWAA)
- Transformation:   AWS Glue (Bronze→Silver) · dbt Core (Silver→Gold, Redshift)
- Warehouse:        AWS Redshift Serverless (lokal: DuckDB)
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
          DAG-Namensschema: olist_<schicht>_<aktion>
Python:   Type hints + Docstrings + Error handling + nur os.environ[] für Credentials
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

## CRISP-DM Phasen — Aktueller Stand

Phase 0  Project Kickoff / Discovery      Abgeschlossen
Phase 1  Data Understanding               Abgeschlossen
Phase 2  Data Preparation                 Abgeschlossen
Phase 3  Modellierung / Pipeline          Abgeschlossen
Phase 4  Testing und Validierung          Abgeschlossen
Phase 5  Deployment / DataOps             In Arbeit
Phase 6  Übergabe und Abschluss           In Arbeit

## Roadmap — Block 1: Projekt fertigstellen

Diesen Abschnitt nach jeder Session selbst aktualisieren.

- [x] Project Brief v1, CRISP-DM Plan, Technischer Pipeline-Plan
- [x] Notion Sprint Backlog
- [x] EDA + Data Understanding Memo
- [x] GitHub Repository + Projektstruktur
- [x] Terraform: S3, IAM, Glue, Redshift Serverless
- [x] Airflow DAG: olist_bronze_upload (CSV → S3 Bronze)
- [x] AWS Glue Job: Bronze → Silver (Cleaning, Parquet)
- [x] dbt Staging (8x), Intermediate (2x), Marts (4x) — lokal DuckDB
- [x] dbt Tests: 42/42 PASS (not_null, unique, relationships)
- [x] Great Expectations: Silver Layer Validation (5 Tabellen, 42 Checks)
- [x] Pipeline Runner: run_pipeline.py (GE → dbt run → dbt test)
- [x] CI/CD: GitHub Actions
- [x] Power BI Dashboard (4 Seiten, 4 Business Questions, 6 KPIs)
- [x] End-to-End Pipeline-Test (DAG vollständig durchlaufen, alle Tasks grün)
- [x] README.md professionalisieren (Architekturdiagramm, Tech Stack)
- [x] Runbook schreiben (RUNBOOK.md)
- [x] Power BI Dashboard professionalisieren (Farbschema, KPI Cards)
- [x] Monitoring: CloudWatch Logs + SNS Alarm bei Glue Job Failure
- [x] Alerting: Email-Benachrichtigung via SNS konfiguriert
- [x] Redshift Migration: dbt läuft gegen Redshift Serverless (14 Modelle, 42 Tests)

## Roadmap — Block 2: Wissen vertiefen

- [x] Redshift: Distribution Keys, Sort Keys, Columnar Storage
- [x] dbt Advanced: Snapshots, Macros, Exposures
- [x] Terraform: State Management, Remote Backend
- [x] Airflow: XComs, Sensors, TaskGroups, Connections
- [x] Power BI: ODBC-Verbindung direkt zu Redshift Serverless
- [x] Data Lineage: OpenLineage, Marquez
- [x] Streaming: Kafka Grundprinzip, Batch vs. Stream
- [x] Airbyte: self-hosted (abctl), S3→S3 Connection, erster Sync (99k Records, Parquet Bronze)

## DPaaS Masterplan — Reproduzierbare Pipeline

### Phase 1 — Business Logic & Semantic Layer

- **Airbyte** (self-hosted Docker): generischer Ingestion-Layer mit 300+ Konnektoren (Shopify, Salesforce, SAP, REST APIs, Datenbanken, Files) → ersetzt manuelle CSV-Uploads und API-DAGs
- Kimball Star Schema: fct_ + dim_ in dbt, keine Logik in Power BI
- DAX nur für Visualisierung, nie für Berechnungen
- KPIs im Semantic Layer — Single Source of Truth
- CAC/LTV nur als optionales Add-on (erfordert Marketingkosten-Daten)

### Phase 2 — Transformation & Qualität

- dbt: stg_ → int_ → fct_/dim_/kpi_, jedes Modell mit schema.yml
- Pflicht-Tests: not_null + unique auf PK, relationships auf FK
- Custom Tests: revenue > 0, keine negativen Lieferdauern
- dbt docs generate: Lineage-Dokumentation für Kunden
- dbt Snapshots: historische Zustände festhalten
- Great Expectations: Checkpoint auf Silver Layer

### Phase 3 — Infrastructure as Code & Cloud

- ClickOps verboten: kein manueller Klick in AWS-Konsole
- Least Privilege: jede IAM-Rolle nur die Rechte die sie braucht
- Verschlüsselung: at rest (KMS) + in transit (TLS)k
- Multi-Environment: dev → staging → prod
- Terraform Remote State: S3 Backend + DynamoDB State Locking
- common_tags auf allen Ressourcen: project, environment, owner, cost_center

### Phase 4 — DataOps & Orchestrierung

- Idempotenz: jeder DAG-Lauf ohne manuelle Korrektur wiederholbar
- SLA/SLO: "Daten sind jeden Morgen um 08:00 Uhr aktuell"
- Airflow: retries=3, retry_delay=5min
- Alerting: Slack/E-Mail bei DAG-Failure, dbt Test Failure
- CI/CD: kein Code live ohne grüne Tests
- Monitoring: Grafana + CloudWatch
- Runbook: RUNBOOK.md im Repository

### Phase 5 — Observability & Data Contracts

- Strukturiertes Logging: Kontext pro Schritt (Tabelle, Zeilenanzahl, Job-ID)
- OpenTelemetry: Tracing über alle Pipeline-Schritte
- Data Contracts: Soda Core oder Great Expectations für Contract Enforcement
- Kosten-Tracking: AWS Cost Explorer + Tagging pro Kunde

### Lambda-Architektur — Optionales Add-on (Speed Layer)

Standard-Stack = Batch Layer. Kunden die Echtzeit benötigen erhalten zusätzlich den Speed Layer:

```text
Datenquelle
     ├──→ Batch Layer (Airflow → Glue → dbt → Redshift)   ← Standard
     │         Tiefe Analysen, Bilanzen, historische Trends
     │
     └──→ Speed Layer (Kafka → Kafka Streams) [Add-on]
               Echtzeit-Dashboards, Alerts, Live-KPIs
                         │
               Serving Layer (Redshift + Materialized Views)
                         └── Power BI liest aus beiden
```

Wann Speed Layer sinnvoll ist:

- Live-Bestandsübersichten (Retail, Logistik)
- Echtzeit-Fraud-Detection (Payments)
- Live-KPIs auf Operations-Dashboards

Kappa als Alternative: Nur Kafka, Batch = Stream mit historischem Replay — weniger Doppelcode,
empfohlen wenn Echtzeit die Hauptanforderung ist und Batch sekundär.

### Reproduzierbarkeit — Template-Strategie

- Terraform Module parametrisiert: Bucket-Name, Region, Environment als Variable
- dbt als Template: nur sources.yml + Staging-Modelle pro Kunde tauschen
- Airflow DAG generisch: Konfiguration außerhalb des DAG-Codes
- Airbyte: Konnektoren per API konfigurierbar — kein Custom Code pro Datenquelle
- Onboarding-Dokument: neue Pipeline in < 1 Tag aufgesetzt

## Karrierevision

Ziel:    Senior Data Engineer + DPaaS-Anbieter
Stack:   AWS-first, aber Konzepte sind cloud-agnostisch übertragbar
Weg:     Junior → Wissen vertiefen → Asset aufbauen → Testkunde → Freelance

Was Senior bedeutet:

- Jede Architekturentscheidung begründen können
- Wissen was schiefgehen kann bevor es schiefgeht
- Systeme gestalten, nicht nur implementieren

## Was ich NICHT will

- Keine überkomplexen Lösungen für ein Portfolio-Projekt
- Keine Libraries oder Services außerhalb des definierten Stacks
- Kein ClickhouseDB, kein Kafka, kein Kubernetes in dieser Pipeline
- Immer erklären WARUM, nicht nur WAS
- Keine Spekulationen — wenn etwas unklar ist, nachfragen
