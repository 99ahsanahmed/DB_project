import time
import random
import json
import psycopg2
from faker import Faker
import os

DB_URL = os.getenv("DATABASE_URL")
fake = Faker()

# FAST SEEDING - Reduced numbers for quick testing
# Use this for development/testing, use seed.py for full benchmarks
NUM_SHIPMENTS = 50_000   # Reduced from 500k
NUM_TELEMETRY = 200_000  # Reduced from 2M
NUM_INVOICES  = 20_000   # Reduced from 200k


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
    
    print("--- STARTING FAST SEED (REDUCED DATA) ---")
    print(f"Shipments: {NUM_SHIPMENTS:,}")
    print(f"Telemetry: {NUM_TELEMETRY:,}")
    print(f"Invoices: {NUM_INVOICES:,}")
    print("This will take 2-5 minutes instead of 20-30 minutes\n")

    # 1. SEED SHIPMENTS
    print(f"Seeding {NUM_SHIPMENTS:,} Shipments...")
    batch = []
    shipment_uuids = []
    
    for i in range(NUM_SHIPMENTS):
        uuid = fake.uuid4()
        shipment_uuids.append(uuid)
        driver_name = fake.name()
        driver_details = f"{driver_name},{fake.phone_number()},{fake.license_plate()}"
        row = (
            uuid,
            fake.country_code(),
            fake.country_code(),
            driver_name,
            driver_details,
            f"{fake.license_plate()},{fake.year()} Volvo VNL,{random.randint(10,40)}T",
            random.choice(['NEW', 'IN_TRANSIT', 'DELIVERED']),
            fake.date_time_this_year()
        )
        batch.append(row)
        if len(batch) >= 1000:
            cur.executemany("INSERT INTO shipments (tracking_uuid, origin_country, destination_country, driver_name, driver_details, truck_details, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", batch)
            batch = []
            if i % 10000 == 0: print(f"  {i:,} rows...")
    if batch:
        cur.executemany("INSERT INTO shipments (tracking_uuid, origin_country, destination_country, driver_name, driver_details, truck_details, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", batch)
    conn.commit()
    print(f"✓ Seeded {NUM_SHIPMENTS:,} shipments\n")

    # 2. SEED TELEMETRY
    print(f"Seeding {NUM_TELEMETRY:,} Telemetry points...")
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
        if len(batch) >= 5000:
            cur.executemany("INSERT INTO truck_telemetry (truck_license_plate, latitude, longitude, elevation, speed, engine_temp, fuel_level, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", batch)
            batch = []
            if i % 50000 == 0: print(f"  {i:,} rows...")
    if batch:
        cur.executemany("INSERT INTO truck_telemetry (truck_license_plate, latitude, longitude, elevation, speed, engine_temp, fuel_level, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", batch)
    conn.commit()
    print(f"✓ Seeded {NUM_TELEMETRY:,} telemetry points\n")

    # 3. SEED INVOICES
    print(f"Seeding {NUM_INVOICES:,} Invoices...")
    batch = []
    for i in range(NUM_INVOICES):
        invoice_blob = {
            "customer_id": random.randint(1000, 9999),
            "amount_cents": random.randint(1000, 500000),
            "currency": random.choice(["USD", "EUR", "GBP"]),
            "items": [{"sku": fake.ean(), "qty": random.randint(1,10)} for _ in range(random.randint(1,5))]
        }
        row = (
            random.choice(shipment_uuids),
            json.dumps(invoice_blob),
            fake.date_this_year()
        )
        batch.append(row)
        if len(batch) >= 1000:
            cur.executemany("INSERT INTO finance_invoices (shipment_uuid, raw_invoice_data, issued_date) VALUES (%s, %s, %s)", batch)
            batch = []
            if i % 5000 == 0: print(f"  {i:,} rows...")
    if batch:
        cur.executemany("INSERT INTO finance_invoices (shipment_uuid, raw_invoice_data, issued_date) VALUES (%s, %s, %s)", batch)
    conn.commit()
    print(f"✓ Seeded {NUM_INVOICES:,} invoices\n")

    print("--- FAST SEEDING COMPLETE ---")
    print("Note: For accurate benchmarks, use seed.py with full dataset")

if __name__ == "__main__":
    seed_everything()
