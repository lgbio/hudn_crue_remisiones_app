#!/usr/bin/env python3

"""
Migrate all rows from MSSQL to PostgreSQL.

Requirements:
    pip install psycopg2-binary pyodbc

Notes:
- Tables must already exist.
- Column names must match.
- PostgreSQL identity column "id" is ignored automatically.
"""

import psycopg2
import pyodbc


# =========================================================
# MSSQL Config
# =========================================================

MSSQL_CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=172.20.100.209;"
    "DATABASE=GestorInstitucional;"
    "UID=apantoja;"
    "PWD=ConsultasPantojaHUDN_2026$;"
    "TrustServerCertificate=yes;"
)

MSSQL_TABLE = "crueremisiones_remision"


# =========================================================
# PostgreSQL Config
# =========================================================

PG_CONFIG = {
    "host": "172.20.10.250",
    "port": 5432,
    "dbname": "crue_remisiones_db",
    "user": "postgres",
    "password": "postgres2026",
}

PG_TABLE = "crueremisiones_remision"


# =========================================================
# Main
# =========================================================

def main():

    # -----------------------------------------------------
    # Connect MSSQL
    # -----------------------------------------------------

    print("+++ Connecting to MSSQL...")

    ms_conn = pyodbc.connect(MSSQL_CONN_STR)
    ms_cursor = ms_conn.cursor()

    # -----------------------------------------------------
    # Connect PostgreSQL
    # -----------------------------------------------------

    print("+++ Connecting to PostgreSQL...")

    pg_conn = psycopg2.connect(**PG_CONFIG)
    pg_cursor = pg_conn.cursor()

    # -----------------------------------------------------
    # Read all rows from MSSQL
    # -----------------------------------------------------

    print(f"+++ Reading rows from MSSQL table: {MSSQL_TABLE}")

    ms_cursor.execute(f"SELECT * FROM {MSSQL_TABLE}")

    rows = ms_cursor.fetchall()

    total = len(rows)

    print(f"+++ Rows found: {total}")

    if total == 0:
        print("+++ No rows to migrate.")
        return

    # -----------------------------------------------------
    # Get column names
    # -----------------------------------------------------

    all_columns = [desc[0] for desc in ms_cursor.description]

    # Skip identity column
    columns = [
        col
        for col in all_columns
        if col.lower() != "id"
    ]

    print(f"+++ Columns to migrate:")
    print(columns)

    # -----------------------------------------------------
    # Build INSERT SQL
    # -----------------------------------------------------

    col_names = ", ".join(columns)

    placeholders = ", ".join(["%s"] * len(columns))

    insert_sql = f"""
        INSERT INTO {PG_TABLE}
        ({col_names})
        VALUES ({placeholders})
    """

    print("\n+++ INSERT SQL:")
    print(insert_sql)

    # -----------------------------------------------------
    # Insert into PostgreSQL
    # -----------------------------------------------------

    print("\n+++ Starting migration...\n")

    inserted = 0

    for i, row in enumerate(rows, start=1):

        try:

            row_dict = dict(zip(all_columns, row))

            values = [
                row_dict[col]
                for col in columns
            ]

            pg_cursor.execute(insert_sql, values)

            inserted += 1

            # Commit every 100 rows
            if i % 100 == 0:
                pg_conn.commit()
                print(f"+++ {i}/{total}")

        except Exception as e:

            print(f"\n--- ERROR on row {i}")
            print(f"--- Exception: {e}")
            print(f"--- Values: {values}")

    # Final commit
    pg_conn.commit()

    print("\n+++ Migration completed")
    print(f"+++ Inserted rows: {inserted}")

    # -----------------------------------------------------
    # Close connections
    # -----------------------------------------------------

    ms_cursor.close()
    ms_conn.close()

    pg_cursor.close()
    pg_conn.close()

    print("+++ Connections closed")


# =========================================================

if __name__ == "__main__":
    main()
