"""
Erstellt das External Schema 'silver' in Redshift Serverless.
Dieses Schema zeigt auf den Glue Data Catalog und ermöglicht
Redshift Spectrum den Zugriff auf die S3 Silver Parquet-Dateien.

Einmalig ausführen nachdem der Glue Crawler gelaufen ist.
"""

import os
import redshift_connector

HOST = "olist-workgroup-dev.710220507619.eu-central-1.redshift-serverless.amazonaws.com"
PORT = 5439
DATABASE = "olist"
USER = "admin"
PASSWORD = os.environ["REDSHIFT_PASSWORD"]
IAM_ROLE = "arn:aws:iam::710220507619:role/olist-redshift-role-dev"
GLUE_DATABASE = "olist_silver_dev"

SQL = f"""
CREATE EXTERNAL SCHEMA IF NOT EXISTS silver
FROM DATA CATALOG
DATABASE '{GLUE_DATABASE}'
IAM_ROLE '{IAM_ROLE}';
"""

def main() -> None:
    print("Verbinde mit Redshift...")
    conn = redshift_connector.connect(
        host=HOST,
        port=PORT,
        database=DATABASE,
        user=USER,
        password=PASSWORD,
    )
    conn.autocommit = True
    cursor = conn.cursor()

    print("Erstelle External Schema 'silver'...")
    cursor.execute(SQL)
    print("External Schema erfolgreich erstellt.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
