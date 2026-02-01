import time
import random
import json
import psycopg2
from faker import Faker
import os

DB_URL = os.getenv("DATABASE_URL")
fake = Faker()

# backend/seed.py

# CHANGE THESE VALUES
NUM_SHIPMENTS = 500_000   
NUM_TELEMETRY = 2_000_000 
NUM_INVOICES  = 200_000


def get_db():
    """
    Tries to connect to the DB. If it fails, it waits and retries.
    This fixes the 'Connection refused' error on startup.
    """
    retries = 20
    while retries > 0:
        try:
            conn = psycopg2.connect(DB_URL)
            print("Successfully connected to the Database!")
            return conn
        except psycopg2.OperationalError:
            print(f"Database not ready yet. Retrying in 2 seconds... ({retries} left)")
            time.sleep(2)
            retries -= 1
            
    raise Exception("Could not connect to the Database after multiple attempts.")

def seed_everything():
    conn = get_db()
    cur = conn.cursor()
    
    print("--- STARTING MEGA-SEED ---")

    # 1. SEED SHIPMENTS
    print(f"Seeding {NUM_SHIPMENTS} Shipments...")
    batch = []
    shipment_uuids = []
    
    for _ in range(NUM_SHIPMENTS):
        uuid = fake.uuid4()
        shipment_uuids.append(uuid)
        driver_name = fake.name()
        driver_details = f"{driver_name},{fake.phone_number()},{fake.license_plate()}"
        row = (
            uuid,
            fake.country_code(),
            fake.country_code(),
            driver_name,  # Extracted driver name for fast lookup
            driver_details,  # Keep original for compatibility
            f"{fake.license_plate()},{fake.year()} Volvo VNL,{random.randint(10,40)}T",
            random.choice(['NEW', 'IN_TRANSIT', 'DELIVERED']),
            fake.date_time_this_year()  # Already a datetime object, will be stored as TIMESTAMP
        )
        batch.append(row)
        if len(batch) >= 1000:
            cur.executemany("INSERT INTO shipments (tracking_uuid, origin_country, destination_country, driver_name, driver_details, truck_details, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", batch)
            batch = []
    if batch:
        cur.executemany("INSERT INTO shipments (tracking_uuid, origin_country, destination_country, driver_name, driver_details, truck_details, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", batch)
    conn.commit()

    # 2. SEED TELEMETRY (The Heavy Lifter)
    print(f"Seeding {NUM_TELEMETRY} Telemetry points (This simulates the 'Big Data' problem)...")
    batch = []
    truck_plates = [fake.license_plate() for _ in range(100)]
    
    for i in range(NUM_TELEMETRY):
        row = (
            random.choice(truck_plates),
            float(fake.latitude()),
            float(fake.longitude()),
            random.randint(0, 5000),
            random.randint(0, 120),
            random.uniform(80.0, 110.0),
            random.uniform(10.0, 100.0),
            fake.date_time_this_year()
        )
        batch.append(row)
        if len(batch) >= 5000: # Larger batch for speed
            cur.executemany("INSERT INTO truck_telemetry (truck_license_plate, latitude, longitude, elevation, speed, engine_temp, fuel_level, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", batch)
            batch = []
            if i % 100000 == 0: print(f"  {i} rows...")
    if batch:
        cur.executemany("INSERT INTO truck_telemetry (truck_license_plate, latitude, longitude, elevation, speed, engine_temp, fuel_level, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", batch)
    conn.commit()

    # 3. SEED INVOICES (The JSON Problem)
    print(f"Seeding {NUM_INVOICES} Invoices...")
    batch = []
    for _ in range(NUM_INVOICES):
        # Create a messy JSON object
        invoice_blob = {
            "customer_id": random.randint(1000, 9999),
            "amount_cents": random.randint(1000, 500000),
            "currency": random.choice(["USD", "EUR", "GBP"]),
            "items": [{"sku": fake.ean(), "qty": random.randint(1,10)} for _ in range(random.randint(1,5))]
        }
        row = (
            random.choice(shipment_uuids),
            json.dumps(invoice_blob),  # JSONB will automatically parse this
            fake.date_this_year()
        )
        batch.append(row)
        if len(batch) >= 1000:
            cur.executemany("INSERT INTO finance_invoices (shipment_uuid, raw_invoice_data, issued_date) VALUES (%s, %s, %s)", batch)
            batch = []
    if batch:
        cur.executemany("INSERT INTO finance_invoices (shipment_uuid, raw_invoice_data, issued_date) VALUES (%s, %s, %s)", batch)
    conn.commit()

    print("--- SEEDING COMPLETE ---")

if __name__ == "__main__":
    seed_everything()