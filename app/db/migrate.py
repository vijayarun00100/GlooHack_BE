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

        migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
        migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith(".sql")])

        for filename in migration_files:
            sql_file_path = os.path.join(migrations_dir, filename)
            print(f"[Python Migration] Executing {filename}...")
            with open(sql_file_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
            cursor.execute(sql_script)

        print(f"[Python Migration] All {len(migration_files)} migrations executed successfully!")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[Python Migration] Migration error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()

