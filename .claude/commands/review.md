Review the file or component passed as argument for pipeline best practices.

Check specifically:
1. **Airflow DAGs**: retries=3, retry_delay=5min, tags, doc_md, XComs statt return values, Sensor mode='reschedule'
2. **dbt Modelle**: config block mit dist/sort keys, schema.yml mit not_null+unique auf PK, relationships auf FK
3. **Python Skripte**: type hints, logging statt print, try/except, os.environ für credentials
4. **Allgemein**: keine hardcodierten Passwörter, keine magic strings, S3-Pfade folgen dem Schema

Argument: $ARGUMENTS

Fasse Findings als Tabelle zusammen: | Datei | Problem | Empfehlung |
