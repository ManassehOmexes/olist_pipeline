# Olist E-Commerce Analytics Pipeline

**Ein E-Commerce-Datensatz mit 100.000 Bestellungen. Vier Geschäftsfragen. Heute beantwortet sie ein Dashboard automatisch - täglich, verifiziert, ohne manuelle Arbeit.**

---

## Das Problem

Umsatz nach Kategorie, Lieferperformance, Kundenzufriedenheit: Die Daten existierten, aber verteilt auf neun Quelltabellen ohne Verbindung. Keine gemeinsame Infrastruktur, keine automatische Aktualisierung, keine verifizierten Zahlen. Entscheidungen über Sortiment, Logistik und Servicequalität ließen sich nicht datenbasiert treffen.

---

## Die Lösung

Ich habe eine vollautomatische ELT-Pipeline auf AWS aufgebaut. Sie lädt täglich alle neun Quelltabellen, bereinigt die Daten in zwei Transformationsschritten und befüllt ein Power BI Dashboard mit vier Seiten und sechs KPIs. Jede Transformation ist automatisch getestet. Kein manueller Eingriff nach dem initialen Setup.

Technisch: Airbyte für die Ingestion in S3, AWS Glue für Bronze-zu-Silver, dbt Core für Silver-zu-Gold auf Redshift Serverless, Apache Airflow für die Orchestration, Terraform für die gesamte Infrastruktur.

---

## Die Ergebnisse

| Metrik | Wert |
|---|---|
| Analysierter Gesamtumsatz | 13,22 Mio. EUR |
| Verarbeitete Bestellungen | 110.197 |
| Durchschnittliche Lieferdauer | 18,26 Tage |
| Anteil verspäteter Lieferungen | 10,44 % |
| Durchschnittlicher Bewertungsscore | 4,08 / 5,0 |
| Automatisierte Datentests | 49 / 49 bestanden |
| dbt-Modelle | 17 |
| Quelltabellen | 9 |

---

## DataOps-Features

Kein Dashboard ohne Absicherung. Die Pipeline beinhaltet ein Bronze Validation Gate (Schema- und Primary-Key-Checks vor jeder Transformation), Volume Anomaly Detection (SNS-Alert bei >30% Abweichung im Row Count), 49 Great Expectations Checks auf dem Silver Layer, GitHub Actions CI/CD (dbt test bei jedem Push), S3 Cross-Region Replication nach eu-west-1 mit Object Lock sowie AWS Secrets Manager für alle Credentials.

---

## Stack

`Airbyte` → `S3 (Medallion)` → `AWS Glue` → `dbt Core` → `Redshift Serverless` → `Power BI`

IaC: Terraform. Orchestration: Apache Airflow. Lineage: OpenLineage + Marquez.

---

**GitHub:** [github.com/ManassehOmexes/olist-analytics-pipeline](https://github.com/ManassehOmexes/olist_pipeline) | **Manasseh - Omexes, D2C Data Engineering Consultant**
