# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy backend files
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy migrations directory (needed for run_migrations.py)
COPY migrations/ /app/migrations/

# We run migrations, then seeder (if needed), then start the server
# start_server.py will check if data exists and skip seeding if it does
CMD ["python", "start_server.py"]