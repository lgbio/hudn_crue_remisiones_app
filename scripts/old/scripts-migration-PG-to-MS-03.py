#!/usr/bin/env python3

"""
Migrate all rows from PostgreSQL to MSSQL.

Features:
- Avoids duplicate rows using:
      fecha + nombre
- Skips:
      id
      created_by_id
- Preserves exact datetime values (no timezone shifts)

Requirements:
    pip install psycopg2-binary pyodbc
"""

import psycopg2
import pyodbc


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
    # Connect MSSQL
    # -----------------------------------------------------

    print("+++ Connecting to MSSQL...")

    ms_conn = pyodbc.connect(MSSQL_CONN_STR)
    ms_cursor = ms_conn.cursor()

    # -----------------------------------------------------
    # Read rows from PostgreSQL
    # -----------------------------------------------------

    print(f"+++ Reading rows from PG table: {PG_TABLE}")

    pg_cursor.execute(f"""
        SELECT

            id,

            TO_CHAR(fecha, 'YYYY-MM-DD HH24:MI:SS') AS fecha,

            nombre,
            tipo_doc,
            doc,
            gest,
            sexo,
            edad,
            especialidad,
            diagnostico,
            ta,
            fc,
            fr,
            tm,
            spo2,
            glasg,
            eps,
            institucion_reporta,
            municipio,
            medico_refiere,
            medico_hudn,
            radio_operador,
            observacion,
            aceptado,

            TO_CHAR(fecha_res, 'YYYY-MM-DD HH24:MI:SS') AS fecha_res,

            TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') AS created_at,

            TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI:SS') AS updated_at,

            created_by_id

        FROM {PG_TABLE}
    """)

    rows = pg_cursor.fetchall()

    total = len(rows)

    print(f"+++ Rows found: {total}")

    if total == 0:
        print("+++ No rows to migrate.")
        return

    # -----------------------------------------------------
    # Column names
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

    print("\n+++ Columns to migrate:")
    print(columns)

    # -----------------------------------------------------
    # INSERT SQL
    # -----------------------------------------------------

    col_names = ", ".join(columns)

    placeholders = ", ".join(["?"] * len(columns))

    insert_sql = f"""
        INSERT INTO {MSSQL_TABLE}
        ({col_names})
        VALUES ({placeholders})
    """

    # -----------------------------------------------------
    # Duplicate check
    # -----------------------------------------------------

    check_sql = f"""
        SELECT COUNT(*)
        FROM {MSSQL_TABLE}
        WHERE fecha = ?
        AND nombre = ?
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

            ms_cursor.execute(
                check_sql,
                row_dict["fecha"],
                row_dict["nombre"]
            )

            exists = ms_cursor.fetchone()[0]

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

            values = [
                row_dict[col]
                for col in columns
            ]

            # ---------------------------------------------
            # Insert
            # ---------------------------------------------

            ms_cursor.execute(insert_sql, values)

            inserted += 1

            if i % 100 == 0:

                ms_conn.commit()

                print(
                    f"+++ Processed: {i}/{total} | "
                    f"Inserted: {inserted} | "
                    f"Skipped: {skipped}"
                )

        except Exception as e:

            print(f"\n--- ERROR on row {i}")
            print(f"--- Exception: {e}")

            try:
                print(f"--- fecha: {row_dict['fecha']}")
                print(f"--- nombre: {row_dict['nombre']}")
            except:
                pass

    # -----------------------------------------------------
    # Final commit
    # -----------------------------------------------------

    ms_conn.commit()

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

    ms_cursor.close()
    ms_conn.close()

    print("\n+++ Connections closed")


# =========================================================

if __name__ == "__main__":
    main()
