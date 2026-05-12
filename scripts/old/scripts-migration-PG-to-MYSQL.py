#!/usr/bin/env python3

"""
Migrate all rows from PostgreSQL to MySQL.

Features:
- Skips:
      id
      created_by_id
- Avoids duplicates using:
      fecha + nombre

Requirements:
    pip install psycopg2-binary mysql-connector-python
"""

import psycopg2
import mysql.connector


# =========================================================
# PostgreSQL Config
# =========================================================

PG_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "crue_remisiones_db",
    "user": "postgres",
    "password": "postgres2026",
}

PG_TABLE = "crueremisiones_remision"


# =========================================================
# MySQL Config
# =========================================================

MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "GestorInstitucional",
    "user": "apantoja",
    "password": "ConsultasPantojaHUDN_2026$"
}

MYSQL_TABLE = "crueremisiones_remision"


# =========================================================
# Main
# =========================================================

def main():

    # -----------------------------------------------------
    # Connect PostgreSQL
    # -----------------------------------------------------

    print("+++ Connecting to PostgreSQL...")

    pg_conn = psycopg2.connect(**PG_CONFIG)
    pg_cursor = pg_conn.cursor()

    # -----------------------------------------------------
    # Connect MySQL
    # -----------------------------------------------------

    print("+++ Connecting to MySQL...")

    mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
    mysql_cursor = mysql_conn.cursor()

    # -----------------------------------------------------
    # Read rows from PostgreSQL
    # -----------------------------------------------------

    print(f"+++ Reading rows from PG table: {PG_TABLE}")

    pg_cursor.execute(f"SELECT * FROM {PG_TABLE}")

    rows = pg_cursor.fetchall()

    total = len(rows)

    print(f"+++ Rows found: {total}")

    if total == 0:
        print("+++ No rows to migrate.")
        return

    # -----------------------------------------------------
    # Columns
    # -----------------------------------------------------

    all_columns = [desc[0] for desc in pg_cursor.description]

    columns = [
        col
        for col in all_columns
        if col.lower() not in (
            "id",
            "created_by_id",
        )
    ]

    print("\n+++ Columns:")
    print(columns)

    # -----------------------------------------------------
    # INSERT SQL
    # -----------------------------------------------------

    col_names = ", ".join(columns)

    placeholders = ", ".join(["%s"] * len(columns))

    insert_sql = f"""
        INSERT INTO {MYSQL_TABLE}
        ({col_names})
        VALUES ({placeholders})
    """

    # -----------------------------------------------------
    # Duplicate check
    # -----------------------------------------------------

    check_sql = f"""
        SELECT COUNT(*)
        FROM {MYSQL_TABLE}
        WHERE fecha = %s
        AND nombre = %s
    """

    print("\n+++ Starting migration...\n")

    inserted = 0
    skipped = 0

    # -----------------------------------------------------
    # Migration loop
    # -----------------------------------------------------

    for i, row in enumerate(rows, start=1):

        try:

            row_dict = dict(zip(all_columns, row))

            # ---------------------------------------------
            # Duplicate check
            # ---------------------------------------------

            mysql_cursor.execute(
                check_sql,
                (
                    row_dict["fecha"],
                    row_dict["nombre"]
                )
            )

            exists = mysql_cursor.fetchone()[0]

            if exists:

                skipped += 1

                print(
                    f"--- Skipping existing row: "
                    f"{row_dict['fecha']} | "
                    f"{row_dict['nombre']}"
                )

                continue

            # ---------------------------------------------
            # Values
            # ---------------------------------------------

            values = []

            for col in columns:

                value = row_dict[col]

                # Remove timezone info preserving hour
                try:
                    if hasattr(value, "tzinfo") and value.tzinfo:
                        value = value.replace(tzinfo=None)
                except:
                    pass

                values.append(value)

            # ---------------------------------------------
            # Insert
            # ---------------------------------------------

            mysql_cursor.execute(insert_sql, values)

            inserted += 1

            # Commit every 100 rows
            if i % 100 == 0:

                mysql_conn.commit()

                print(
                    f"+++ Processed: {i}/{total} | "
                    f"Inserted: {inserted} | "
                    f"Skipped: {skipped}"
                )

        except Exception as e:

            print(f"\n--- ERROR on row {i}")
            print(f"--- Exception: {e}")

    # -----------------------------------------------------
    # Final commit
    # -----------------------------------------------------

    mysql_conn.commit()

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print("\n+++ Migration completed")

    print(f"+++ Total rows read: {total}")
    print(f"+++ Inserted rows:  {inserted}")
    print(f"+++ Skipped rows:   {skipped}")

    # -----------------------------------------------------
    # Close
    # -----------------------------------------------------

    pg_cursor.close()
    pg_conn.close()

    mysql_cursor.close()
    mysql_conn.close()

    print("\n+++ Connections closed")


# =========================================================

if __name__ == "__main__":
    main()
