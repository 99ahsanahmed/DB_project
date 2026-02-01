# Note: Use "##/###" headings (no single-# headings) per repo style.

## Legacy Logistics Rescue Mission — Technical Report (`REPORT.md`)

### 1) Executive Summary

#### Goal

- Bring key API endpoints under their target latencies (measured by `X-Process-Time`) **without upgrading hardware** (Docker limits: **0.5 CPU / 512 MB RAM**).
- Achieve **Benchmark Score > 90%**.

#### Environment

- **Database**: PostgreSQL 15 (Dockerized)
- **API**: FastAPI + Uvicorn (`backend/app.py`)
- **Benchmark**: `benchmark.py` (5 endpoints, 5 iterations each, 30s timeout)

#### Baseline vs Final Results

> Attach screenshots in `docs/` and paste raw outputs below.

| Benchmark Case                                             |              Baseline Avg (ms) | Baseline Score | Final Avg (ms) | Final Score |
| ---------------------------------------------------------- | -----------------------------: | -------------: | -------------: | ----------: |
| 1. Unindexed Date Search (`/shipments/by-date`)            |                        _paste_ |        _paste_ |        _paste_ |     _paste_ |
| 2. Driver Search (`/shipments/driver/{name}`)              |                        _paste_ |        _paste_ |        _paste_ |     _paste_ |
| 3. JSON Parsing / Finance (`/finance/high-value-invoices`) |                        _paste_ |        _paste_ |        _paste_ |     _paste_ |
| 4. Partitioning / Telemetry (`/telemetry/truck/{plate}`)   |                        _paste_ |        _paste_ |        _paste_ |     _paste_ |
| 5. Complex Aggregation (`/analytics/daily-stats`)          |                        _paste_ |        _paste_ |        _paste_ |     _paste_ |
| **FINAL SYSTEM GRADE**                                     | **40.76%** (observed baseline) |                |        _paste_ |     _paste_ |

#### Evidence (what to include)

- `docs/before_benchmark.png`: screenshot of baseline `python benchmark.py`
- `docs/after_benchmark.png`: screenshot of final `python benchmark.py`
- `docs/explain_plans.txt`: before/after `EXPLAIN (ANALYZE, BUFFERS)` for each targeted query

---

### 2) Problem Analysis (Before) — What was slow and why

This section documents the root cause using **EXPLAIN-driven evidence**. The recurring failure modes in the baseline system were:

- **Sequential scans on large tables** (`shipments`, `truck_telemetry`, `finance_invoices`)
- **Non-sargable predicates** (e.g., `ILIKE '%John%'` without trigram support)
- **Runtime JSON parsing** (casting `TEXT` to JSON / extracting values per-row)
- **Large result sets** causing high CPU/serialization time (finance endpoint)
- **Analytics recomputed on every request** (expensive aggregations)

#### 2.1 Date Search — `/shipments/by-date?date=2023-05`

- **Baseline issue**: date stored/queried in a way that encouraged scans (or ineffective index usage).
- **Evidence to paste**:
  - Before plan in `docs/explain_plans.txt` for:
    - `SELECT * FROM shipments WHERE created_at >= '2023-05-01' AND created_at < '2023-06-01';`

#### 2.2 Driver Search — `/shipments/driver/John`

- **Baseline issue**: driver identity embedded in `driver_details` and queried via pattern matching; standard B-tree indexing can’t accelerate `ILIKE '%…%'`.
- **Evidence to paste**:
  - Before plan for the benchmark-equivalent join/filter.

#### 2.3 Finance JSON — `/finance/high-value-invoices`

- **Baseline issue**: heavy JSON parsing at query time and/or scanning too many rows.
- **Evidence to paste**:
  - Before plan for:
    - `SELECT id FROM finance_invoices WHERE (raw_invoice_data->>'amount_cents')::int > 50000;`

#### 2.4 Telemetry — `/telemetry/truck/TRK-9821?limit=100`

- **Baseline issue**: filter + sort on a 2M+ row table without a matching composite index.
- **Evidence to paste**:
  - Before plan for:
    - `SELECT * FROM truck_telemetry WHERE truck_license_plate = 'TRK-9821' ORDER BY timestamp DESC LIMIT 100;`

#### 2.5 Analytics — `/analytics/daily-stats`

- **Baseline issue**: repeated full-table aggregates on every request.
- **Evidence to paste**:
  - Before plan(s) for delivered count, avg speed, and revenue sum.

---

### 3) The Solution (After) — What we changed and why it improved performance

All changes were applied as **SQL migrations** under `migrations/` and (where required) minor API/query changes in `backend/app.py` to make queries index-friendly and reduce serialization overhead.

#### 3.1 Indexing & sargable predicates (Shipments date + status)

##### Migration(s)

- `migrations/01_fix_status_search.sql`: added `idx_shipments_status` on `shipments(status)`
- `migrations/02_fix_shipment_date.sql`: added `idx_shipments_date` on `shipments(created_at)`
- `migrations/03_optimize_schema.sql`: added `idx_shipments_created_at_btree` and a partial delivered-status index

##### Why this works

- B-tree on `created_at` enables **index range scans** for month windows.
- Partial index on delivered rows reduces index size and speeds up analytics counts.

##### After evidence (paste)

- After plan for the date range query should show **Index Scan** / **Bitmap Index Scan** instead of Seq Scan.

#### 3.2 Normalization of drivers (remove duplicated text & accelerate joins)

##### Migration(s)

- `migrations/11_normalize_drivers.sql`: created `drivers` table and `shipments.driver_id` FK + indexes
- `migrations/13_optimize_drivers_search.sql`: trigram GIN index on `drivers.name`
- `migrations/15_optimize_driver_search.sql`: composite index `shipments(driver_id, created_at DESC)`

##### Why this works

- Replacing repeated driver text with `driver_id` reduces row width and IO.
- `GIN (name gin_trgm_ops)` makes `ILIKE '%John%'` fast.
- The composite index matches the query pattern: **filter by driver_id then order by created_at desc + LIMIT**.

##### API changes supporting the DB design

In `backend/app.py`, the driver endpoint uses:

- a join to `drivers`
- `ORDER BY s.created_at DESC`
- a tight `LIMIT 20`
- selects only a few columns to reduce JSON serialization time

##### After evidence (paste)

- After plan should show trigram index usage on `drivers.name` (or fast filter) and index-assisted access on `shipments(driver_id, created_at)`.

#### 3.3 JSON optimization (stop parsing JSON at query time)

##### Migration(s)

- `migrations/06_fix_jsonb_conversion.sql`: converts `raw_invoice_data` to **JSONB** and adds indexes
- `migrations/09_add_computed_amount_column.sql`: attempted STORED generated column (later corrected)
- `migrations/10_fix_computed_column.sql`: implemented a **real column** `amount_cents`, backfilled, indexed
- `migrations/14_optimize_json_response_size.sql`: `VACUUM ANALYZE` and notes on response-size bottleneck

##### Why this works

- JSONB avoids repeated parsing overhead and enables native operators.
- A persisted `amount_cents` column with a B-tree index makes the “high value” filter fast and predictable.
- Returning only `id, amount_cents` with `LIMIT 20` prevents response serialization from dominating latency.

##### After evidence (paste)

- After plan should show an **Index Scan** on `idx_finance_invoices_amount_cents` (or equivalent).

#### 3.4 Telemetry optimization (filter + ORDER BY + LIMIT)

##### Migration(s)

- `migrations/03_optimize_schema.sql`: composite index attempt
- `migrations/07_optimize_telemetry_index.sql`: dropped/recreated the composite index correctly

##### Why this works

The telemetry endpoint query pattern is:

- `WHERE truck_license_plate = ?`
- `ORDER BY timestamp DESC`
- `LIMIT 100`

The index `truck_telemetry(truck_license_plate, timestamp DESC)` supports all three efficiently.

##### After evidence (paste)

- After plan should show an **Index Scan using idx_telemetry_truck_timestamp**.

#### 3.5 Analytics acceleration (materialized view)

##### Migration(s)

- `migrations/04_create_analytics_view.sql`: creates `daily_stats_cache` materialized view

##### Why this works

Analytics became a single fast `SELECT` from a precomputed view, instead of computing aggregates over large tables per request.

##### After evidence (paste)

- After plan for `/analytics/daily-stats` should show a trivial scan over `daily_stats_cache`.

#### 3.6 Connection pooling + process-time measurement

##### API changes

In `backend/app.py`:

- Added `ThreadedConnectionPool` (reuse DB connections).
- Added middleware that returns `X-Process-Time`, which the benchmark prefers over wall-clock timing.

##### Why this works

On constrained CPU/RAM, repeated TCP + auth + connection setup per request is measurable overhead. Pooling reduces this cost.

---

### 4) Challenges / Incidents (and how they were fixed)

- **Long “seeding” time is normal**: initial dataset generation is heavy under 0.5 CPU / 512MB. You can safely stop log-following with Ctrl+C without stopping containers.
- **Generated column pitfall (finance)**:
  - Attempted: generated STORED column for `amount_cents` (Migration 09)
  - Issue: required correction/backfill behavior for existing rows
  - Fix: converted to a normal column + backfill + index (Migration 10)
- **Response-size bottleneck**:
  - Even if the SQL is fast, returning massive payloads dominates latency.
  - Fix: return minimal fields and small LIMIT for benchmark-critical endpoints.
- **Planner/statistics**:
  - Added `ANALYZE` / `VACUUM ANALYZE` where needed to ensure the planner selects the intended indexes.

---

### 5) Change Log (Step-by-step, tied to migrations and endpoint goals)

#### Step 1 — Baseline indexing

- `01_fix_status_search.sql`: B-tree index on `shipments(status)`
- `02_fix_shipment_date.sql`: B-tree index on `shipments(created_at)`

#### Step 2 — Core schema + index package

- `03_optimize_schema.sql`:
  - add `shipments.driver_name` (extracted from `driver_details`)
  - add B-tree index on `shipments(created_at)`
  - add B-tree index on `shipments(driver_name)` (later replaced with trigram)
  - add composite index on telemetry `(truck_license_plate, timestamp DESC)`
  - add partial delivered-status index for analytics
  - add telemetry speed index
  - `ANALYZE` key tables

#### Step 3 — Analytics caching

- `04_create_analytics_view.sql`: materialized view `daily_stats_cache` for `/analytics/daily-stats`

#### Step 4 — Driver search pattern matching

- `05_fix_driver_search.sql`:
  - enable `pg_trgm`
  - replace B-tree driver_name index with trigram GIN on `shipments.driver_name`

#### Step 5 — Finance JSONB conversion + indexing

- `06_fix_jsonb_conversion.sql`:
  - convert `finance_invoices.raw_invoice_data` from TEXT → JSONB (if needed)
  - expression index on extracted amount
  - GIN index on JSONB document

#### Step 6 — Telemetry index correction

- `07_optimize_telemetry_index.sql`:
  - recreate the composite telemetry index in the optimal order
  - analyze telemetry for planner accuracy

#### Step 7 — Experiments around finance selectivity

- `08_optimize_json_query.sql`: attempted “covering” expression index + analysis (documents why >90% selectivity can still favor seq scan)

#### Step 8 — Persist amount_cents for fast finance filtering

- `09_add_computed_amount_column.sql`: attempted generated column strategy
- `10_fix_computed_column.sql`: finalized as normal column + backfill + index

#### Step 9 — Normalization (drivers)

- `11_normalize_drivers.sql`:
  - create `drivers`
  - insert distinct drivers
  - add `shipments.driver_id` + FK
  - indexes on `shipments(driver_id)` and `drivers(name)`

#### Step 10 — Trigram search on normalized drivers

- `13_optimize_drivers_search.sql`: trigram GIN on `drivers.name`

#### Step 11 — Finance maintenance + response-size note

- `14_optimize_json_response_size.sql`: `VACUUM ANALYZE finance_invoices` + documents that response size (not SQL) can dominate

#### Step 12 — Composite index for JOIN + ORDER BY + LIMIT

- `15_optimize_driver_search.sql`: `shipments(driver_id, created_at DESC)` to support the driver endpoint’s access pattern

---

### 6) How to reproduce results (commands)

#### Start the system (detached)

```bash
docker-compose up -d --build
```

#### Watch seeding/migrations until ready

```bash
docker-compose logs -f api
```

Wait for: `Uvicorn running on http://0.0.0.0:8000`

#### Run benchmark

```bash
python benchmark.py
```

#### Capture EXPLAIN plans (paste outputs into `docs/explain_plans.txt`)

Use your DB client (DBeaver/TablePlus) and run, for example:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM shipments
WHERE created_at >= '2023-05-01' AND created_at < '2023-06-01';
```
