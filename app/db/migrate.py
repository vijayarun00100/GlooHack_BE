import os
import sys
import psycopg2
from app.core.config import settings

def run_migrations():
    print("[Python Migration] Connecting to PostgreSQL database...")
    db_url = settings.DATABASE_URL
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()

        sql_file_path = os.path.join(os.path.dirname(__file__), "migrations", "001_initial_schema.sql")
        with open(sql_file_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        print(f"[Python Migration] Executing 001_initial_schema.sql DDL script...")
        cursor.execute(sql_script)
        print("[Python Migration] Database schema migration executed successfully!")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[Python Migration] Migration error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
