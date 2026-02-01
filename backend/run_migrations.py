import psycopg2
import os
import glob
from pathlib import Path

DB_URL = os.getenv("DATABASE_URL")

def run_migrations():
    """Run all migration files in order"""
    # Wait for database to be ready
    import time
    retries = 20
    while retries > 0:
        try:
            conn = psycopg2.connect(DB_URL)
            break
        except psycopg2.OperationalError:
            print(f"Database not ready yet. Retrying in 2 seconds... ({retries} left)")
            time.sleep(2)
            retries -= 1
            if retries == 0:
                raise Exception("Could not connect to the Database after multiple attempts.")
    
    conn.autocommit = True
    cur = conn.cursor()
    
    # Get migrations directory (same level as this script in Docker)
    migrations_dir = Path(__file__).parent / "migrations"
    
    # Get all SQL files and sort them
    migration_files = sorted(glob.glob(str(migrations_dir / "*.sql")))
    
    print("--- RUNNING MIGRATIONS ---")
    for migration_file in migration_files:
        print(f"Running: {Path(migration_file).name}")
        try:
            with open(migration_file, 'r') as f:
                sql = f.read()
                cur.execute(sql)
            print(f"  ✓ Success")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            # Continue with other migrations
            pass
    
    cur.close()
    conn.close()
    print("--- MIGRATIONS COMPLETE ---\n")

if __name__ == "__main__":
    run_migrations()
