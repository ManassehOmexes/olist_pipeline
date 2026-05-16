# DPaaS — Data Intelligence as a Service

## Positionierung

Wir bauen und betreiben datengetriebene Entscheidungssysteme für KMU.

Unternehmen, die ihre Entscheidungen auf Daten stützen, sind nachweislich schneller, präziser und widerstandsfähiger als solche, die auf Bauchgefühl und reaktives Handeln setzen. Genau dieser Vorteil ist bisher nur Großunternehmen mit eigenen Data Teams vorbehalten.

**Unser Angebot:** Derselbe Industriestandard — schlüsselfertig, wartbar, DSGVO-konform — für KMU ohne eigenes Data Team.

---

## Problem — Datenparalyse (3 Ebenen)

**Ebene 1 — Datenchaos:**
Daten liegen verstreut in Shopify, CRM, ERP, Excel-Tabellen und Datenbanken. Kein einheitliches System, keine gemeinsame Datenbasis. Abteilungen arbeiten mit unterschiedlichen Zahlen.

**Ebene 2 — Datenparalyse:**
Die Daten sind technisch vorhanden, aber nicht nutzbar. Es fehlen Infrastruktur, Fachwissen und Personal, um aus Rohdaten verwertbare Informationen zu machen. KI-Projekte scheitern an der Datenqualität, bevor sie starten.

**Ebene 3 — Verpasster Wert:**
Das Unternehmen erkennt, dass KI und Analytics möglich wären — aber weiß nicht wo anfangen. Entscheidungen werden reaktiv und aus dem Bauchgefühl getroffen statt proaktiv und datenbasiert. Der Wettbewerb zieht davon.

**Typische Aussagen unserer Zielkunden:**
- *"Wir haben Unmengen von Daten, aber keine Ahnung was wir damit anfangen sollen."*
- *"Wir wollen KI einsetzen, aber unsere Daten sind ein Chaos."*
- *"Wir nutzen noch Excel für unsere monatlichen Auswertungen."*
- *"Wir wissen nicht mal wo alle unsere Daten überhaupt liegen."*

---

## Zielkunden

**Primäre Zielgruppe:**
- KMU mit 10–500 Mitarbeitern
- Branchen: E-Commerce, Retail, SaaS, Logistik, Dienstleistungen
- Mindestens 1 operative Datenquelle (Shopify, CRM, ERP, PostgreSQL, REST API)
- Wachstumsambition + erste KI- oder Analytics-Überlegungen
- Kein internes Data Team oder Data Engineer

**Sekundäre Zielgruppe:**
- Größere Unternehmen mit veralteter Infrastruktur (Excel, Legacy BI)
- Unternehmen nach Datenschutzvorfällen auf der Suche nach sicherer Infrastruktur
- Startups, die von Beginn an skalierbare Datenpipelines aufbauen wollen

**Qualifizierungsfragen (Sales):**
1. Haben Sie eine operative Datenquelle mit > 1.000 Datensätzen?
2. Treffen Sie aktuell Entscheidungen ohne Datenbasis oder mit manuellen Excel-Reports?
3. Haben Sie konkrete Fragen, die Sie mit Daten beantworten möchten?
4. Haben Sie Datenschutzanforderungen (DSGVO) die aktuell nicht vollständig erfüllt sind?

---

## Lösung — Was wir liefern

Eine vollständige, wartbare Datenpipeline nach Industriestandard — von der Rohdatenquelle bis zum Entscheidungs-Dashboard.

```
Datenquellen         Ingestion          Transformation       Analyse
(Shopify, CRM,  →   (Airbyte,      →   (AWS Glue,       →  (Power BI,
 ERP, Postgres,      automatisch)        dbt, Tests)         KI-Abfragen,
 REST APIs)                                                   Reverse ETL)
```

**Was der Kunde bekommt:**
- Tägliche, automatische Datenpipeline — ohne manuellen Eingriff
- Einheitliche Datenbasis (Single Source of Truth)
- Power BI Dashboard mit definierten KPIs
- DSGVO-konforme Infrastruktur ab Tag 1
- Monitoring + Alerting bei Ausfällen
- Runbook — klare Anleitung für Selbst-Diagnose und Betrieb

---

## Service-Tiers

### Tier 1 — Foundation *(Einstieg, 2–4 Wochen)*

**Für wen:** KMU, die aus Datenchaos ausbrechen und eine verlässliche Datenbasis aufbauen wollen.

**Was ist enthalten:**
- Discovery Workshop (Business Questions + KPIs definieren, CRISP-DM Phase 0–1)
- Airbyte-Ingestion: Alle Datenquellen automatisch in S3 Bronze laden
- AWS Glue: Rohdaten bereinigen, validieren, nach Silver transformieren
- dbt: Staging → Intermediate → Mart-Modelle mit automatischen Tests
- Power BI Dashboard: 4 Business Questions, 6 KPIs
- Monitoring: AWS CloudWatch + SNS E-Mail-Alerts
- DSGVO-Grundschutz: Encryption at rest + in transit, IAM Least Privilege
- Runbook + Übergabedokumentation

**Ergebnis:** Jeden Morgen aktuelle, verlässliche KPIs — ohne manuellen Aufwand.

---

### Tier 2 — Intelligence *(+2 Wochen nach Foundation)*

**Für wen:** Kunden, die über Dashboards hinaus KI-gestützte Analysen nutzen wollen.

**Was ist enthalten (zusätzlich zu Tier 1):**
- dbt Semantic Layer (MetricFlow): KPIs als abfragbare Metriken definiert
- KI-Abfragen (NLP): Natürlichsprachliche Fragen → automatische KPI-Antworten
  *(Beispiel: "Welches Produkt hatte letzten Monat den höchsten Umsatz?")*
- Privacy Layer: PII-Maskierung in Staging-Modellen, Column-Level Security
- DSGVO Art. 25 Compliance-Nachweis: Privacy by Design dokumentiert

**Ergebnis:** Das Team kann Datenfragen ohne SQL-Kenntnisse direkt stellen und bekommt sofort Antworten.

---

### Tier 3 — Enterprise *(+4 Wochen nach Intelligence)*

**Für wen:** Kunden mit operativen Teams, die Echtzeit-Informationen direkt in ihren Arbeitswerkzeugen brauchen.

**Was ist enthalten (zusätzlich zu Tier 2):**
- Reverse ETL: KPIs automatisch in Slack, E-Mail oder CRM pushen
  *(Beispiel: Wöchentlicher KPI-Report direkt im Slack-Kanal)*
- Erweitertes Monitoring: Grafana Dashboard für technische Teams
- Optionaler Speed Layer: Kafka-basiertes Streaming für Echtzeit-KPIs
- Multi-Environment: Dev → Staging → Prod Pipeline

**Ergebnis:** KPIs kommen zu den Menschen — nicht umgekehrt.

---

## Differenzierungsmerkmale

### 1. Privacy by Design (DSGVO Art. 25) — eingebaut, kein Add-on
Datenschutz ist keine nachträgliche Checkbox, sondern architektonisch verankert:
- PII-Maskierung in dbt-Makros
- Column-Level Security in Redshift
- AWS Macie für automatischen PII-Scan in S3
- Vollständiger Compliance-Nachweis im Runbook

### 2. Ransomware-Resilienz
Besonders relevant für KMU: Angriffe auf kleine und mittelständische Unternehmen nehmen zu.
- S3 Object Lock (COMPLIANCE-Modus, 30 Tage) — Bronze-Daten sind unveränderbar
- Cross-Region Replication — Daten in zwei AWS-Regionen repliziert
- RPO = 24h, RTO = 4h — schriftlich dokumentiert

### 3. CRISP-DM-Methodik — messbare, wiederholbare Ergebnisse
Kein "Big Bang"-Projekt. Iterative, phasenbasierte Lieferung:
- Phase 0–1: Business Understanding + Data Understanding (gemeinsam mit Kunden)
- Phase 2–4: Vorbereitung, Modellierung, Testing
- Phase 5–6: Deployment, Übergabe, Dokumentation
- Messbare Meilensteine — kein Projektstau

### 4. Ready-Ready in 4 Schritten
Neue Kundenumgebung in < 1 Tag aufgesetzt — kein manueller Klick:
```bash
# 1. Bootstrap: S3 + DynamoDB für Terraform State
bash bootstrap.sh <customer-id> eu-central-1 <project>

# 2. Variablen anpassen (einmalig)
cp terraform.tfvars.example terraform.tfvars

# 3. Infrastructure deployen
terraform init && terraform apply

# 4. Airbyte Connections deployen
python scripts/airbyte_deploy.py
```

### 5. Cloud-Agnostik, Vendor-unabhängig
- Terraform + dbt laufen auf AWS, Azure und GCP
- Kein Lock-in an proprietäre BI-Tools
- Open-Source Kern: dbt Core, Airbyte, Airflow

---

## Liefermethodik (CRISP-DM Hybrid)

Wir liefern nach einem modifizierten CRISP-DM-Framework — agil, iterativ, phasenbasiert.

| Phase | Name | Dauer | Output |
|-------|------|-------|--------|
| 0 | Project Kickoff / Discovery | 1–2 Tage | Project Brief, Business Questions, KPI-Definition |
| 1 | Data Understanding | 2–3 Tage | EDA, Datenqualitäts-Memo, Quellen-Inventar |
| 2 | Data Preparation | 3–5 Tage | Bronze/Silver/Gold Schema, Glue Jobs |
| 3 | Modellierung / Pipeline | 5–7 Tage | dbt-Modelle, Airflow DAGs, Airbyte Connections |
| 4 | Testing + Validierung | 2–3 Tage | 100% dbt Tests grün, Great Expectations Checkpoint |
| 5 | Deployment / DataOps | 2–3 Tage | Prod-Deployment, Monitoring, Alerting |
| 6 | Übergabe + Abschluss | 1–2 Tage | Runbook, Dashboard-Walkthrough, Dokumentation |

**Kernprinzip:** Keine Überraschungen. Jede Phase hat definierte Inputs, Outputs und Abnahmekriterien.

---

## Datenschutz & Sicherheit (DSGVO Art. 25 + PETs)

### DSGVO Art. 25 — Privacy by Design und by Default

Art. 25 DSGVO verpflichtet Unternehmen, Datenschutz von Anfang an in technische Systeme einzubauen — nicht nachträglich. Unsere Pipeline ist nach diesem Prinzip gebaut:

| Anforderung | Unsere Umsetzung |
|-------------|------------------|
| Datenminimierung | Nur notwendige Felder werden weitergegeben; PII in Staging maskiert |
| Zweckbindung | Bronze-Daten unveränderbar (Object Lock), Audit-Trail via CloudTrail |
| Vertraulichkeit | Encryption at rest (KMS/AES-256) + in transit (TLS 1.2+) |
| Integrität | dbt Tests + Great Expectations Checkpoints auf Silver Layer |
| Zugriffssteuerung | IAM Least Privilege, Column-Level Security in Redshift |
| Rechenschaftspflicht | Compliance-Nachweis im Runbook, auditierbare Logs |

### Privacy-Enhancing Technologies (PETs)

Technologien, die sicherstellen dass Daten auch bei KI-Nutzung datenschutzkonform bleiben:

- **Datenmaskierung** (`dbt mask_pii()` Makro): Namen, E-Mails, Adressen werden in Staging-Modellen durch Hashes ersetzt — KPIs bleiben korrekt, PII ist weg
- **Column-Level Security** (Redshift): BI-Rollen sehen nur freigegebene Spalten
- **AWS Macie**: Automatischer PII-Scan in S3 Bronze — Alert wenn neue PII-Felder auftauchen
- **Anonymisierung für AI**: Daten, die an LLM-APIs gesendet werden, sind vor dem API-Call anonymisiert

### Ransomware-Schutz

- S3 Bronze Bucket: Object Lock (COMPLIANCE, 30 Tage) — kein Admin kann Bronze löschen
- Cross-Region Replication: Bronze automatisch in eu-west-1 gespiegelt
- RTO = 4h, RPO = 24h — schriftlich im Runbook definiert und getestet

---

## Technischer Stack

| Komponente | Technologie | Zweck |
|------------|-------------|-------|
| Orchestrierung | Apache Airflow (MWAA) | DAG-Scheduling, Monitoring |
| Ingestion | Airbyte (self-hosted Docker) | 300+ Konnektoren, API-deploybar |
| Transformation | AWS Glue + dbt Core | Bronze→Silver (Glue), Silver→Gold (dbt) |
| Warehouse | AWS Redshift Serverless | OLAP, Column-Store, BI-Anbindung |
| Storage | AWS S3 (Medallion) | Bronze / Silver / Gold (Parquet) |
| Datenqualität | Great Expectations + dbt Tests | Validierung auf Silver + Gold |
| IaC | Terraform ≥ 1.5 | Reproduzierbare Cloud-Infrastruktur |
| CI/CD | GitHub Actions | Kein Code live ohne grüne Tests |
| Monitoring | AWS CloudWatch + Grafana | Alerts bei DAG/Job-Fehlern |
| Visualisierung | Power BI Desktop | ODBC → Redshift, 4 BQ, 6 KPIs |
| Reverse ETL | AWS Lambda + SNS | KPIs → Slack / E-Mail / CRM |
| AI Layer | dbt Semantic Layer + Claude API | NLP-Abfragen auf maskierten Daten |
| PETs | AWS Macie + dbt mask_pii() | DSGVO Art. 25 Compliance |
| Sicherheit | VPC, IAM, KMS, TLS | CIS AWS Foundations Benchmark |

**Deployment-Prinzip:** Terraform + Airbyte API = kein manueller Klick. Neue Kundenumgebung in < 1 Tag.
