## Evidence Folder (`docs/`)

Add these artifacts before final submission:

- **`before_benchmark.png`**: screenshot of baseline `python benchmark.py`
- **`after_benchmark.png`**: screenshot of final `python benchmark.py`
- **`explain_plans.txt`**: paste before/after `EXPLAIN (ANALYZE, BUFFERS)` for each benchmark query

### Notes

- Use **Ctrl+C** to stop `docker-compose logs -f api` safely (it exits log-follow, does not stop containers).
- When capturing EXPLAIN output, run each query **twice** and paste the **second** run (warm cache) to reduce noise.
