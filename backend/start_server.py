import psycopg2
import os
import subprocess
import sys

DB_URL = os.getenv("DATABASE_URL")

def check_data_exists():
    """Check if database already has seeded data"""
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Check if shipments table has data
        cur.execute("SELECT COUNT(*) FROM shipments")
        shipment_count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        # If we have a reasonable amount of data, skip seeding
        return shipment_count > 1000
    except Exception as e:
        print(f"Error checking data: {e}")
        return False

def main():
    print("--- STARTING SERVER ---")
    
    # Run migrations first
    print("Running migrations...")
    try:
        import run_migrations
        run_migrations.run_migrations()
    except Exception as e:
        print(f"Migration error: {e}")
    
    # Check if we need to seed
    if check_data_exists():
        print("✓ Database already has data, skipping seed...")
    else:
        print("Database is empty, seeding data...")
        try:
            import seed
            seed.seed_everything()
        except Exception as e:
            print(f"Seeding error: {e}")
    
    # Start the server
    print("Starting Uvicorn server...")
    os.execvp("uvicorn", ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    main()
