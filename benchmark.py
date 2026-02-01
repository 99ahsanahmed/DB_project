import requests
import time
import statistics
from datetime import datetime

# --- CONFIGURATION ---
BASE_URL = "http://localhost:8000"
ITERATIONS = 5  # Number of times to hit each endpoint (keep low initially, it's slow!)
# We use a timeout so the script doesn't hang forever on broken student code
TIMEOUT_SECONDS = 30 

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def run_benchmark():
    print(f"{YELLOW}--- STARTING LEGACY LOGISTICS BENCHMARK ---{RESET}")
    print(f"Target: {BASE_URL}")
    print(f"Iterations per endpoint: {ITERATIONS}\n")

    # The Test Suite
    # We define specific scenarios mapping to the weekly modules
# benchmark.py

    endpoints = [
        {
            "name": "1. Unindexed Date Search",
            "url": "/shipments/by-date?date=2023-05", 
            "target_ms": 10  
        },
        {
            "name": "2. Driver Search",
            "url": "/shipments/driver/John", 
            "target_ms": 20  
        },
        {
            "name": "3. JSON Parsing / Finance",
            "url": "/finance/high-value-invoices",
            "target_ms": 200
        },
        {
            "name": "4. Partitioning / Telemetry",
            "url": "/telemetry/truck/TRK-9821?limit=100", 
            "target_ms": 50 
        },
        {
            "name": "5. Complex Aggregation",
            "url": "/analytics/daily-stats",
            "target_ms": 100 
        }
    ]

    total_score = 0
    max_score = len(endpoints) * 100

    # Table Header
    print(f"{'TEST CASE':<40} | {'AVG TIME (ms)':<15} | {'STATUS':<10} | {'SCORE'}")
    print("-" * 85)

    for test in endpoints:
        times = []
        status = "OK"
        
        for i in range(ITERATIONS):
            try:
                start_real = time.time()
                response = requests.get(f"{BASE_URL}{test['url']}", timeout=TIMEOUT_SECONDS)
                end_real = time.time()
                
                # We prefer the internal X-Process-Time header if available (excludes network latency)
                # otherwise we fall back to wall-clock time
                if "X-Process-Time" in response.headers:
                    duration_ms = float(response.headers["X-Process-Time"]) * 1000
                else:
                    duration_ms = (end_real - start_real) * 1000
                
                times.append(duration_ms)
                
                # Simple progress indicator dot
                print(".", end="", flush=True)

            except requests.exceptions.Timeout:
                times.append(TIMEOUT_SECONDS * 1000)
                status = "TIMEOUT"
                print("T", end="", flush=True)
            except Exception as e:
                times.append(TIMEOUT_SECONDS * 1000)
                status = "ERROR"
                print("E", end="", flush=True)

        # Calculate Results
        avg_time = statistics.mean(times)
        
        # Grading Logic: 
        # If avg_time <= target, 100 points. 
        # If avg_time > target * 10, 0 points.
        # Linear scale in between.
        if avg_time <= test['target_ms']:
            points = 100
        elif avg_time >= test['target_ms'] * 10:
            points = 0
        else:
            # Linear decay
            overhead = avg_time - test['target_ms']
            max_overhead = (test['target_ms'] * 10) - test['target_ms']
            points = 100 - (overhead / max_overhead * 100)
        
        total_score += points
        
        # Color coding the output
        color = GREEN if points > 80 else RED if points < 30 else YELLOW
        
        print(f"\r{' ' * ITERATIONS}", end="\r") # Clear progress dots
        print(f"{test['name']:<40} | {avg_time:10.2f} ms   | {color}{status:<10}{RESET} | {int(points)}/100")

    print("-" * 85)
    
    final_grade = (total_score / max_score) * 100
    print(f"\n{YELLOW}FINAL SYSTEM GRADE: {final_grade:.2f}%{RESET}")
    
    if final_grade < 50:
        print(f"{RED}VERDICT: SYSTEM CRITICAL. DO NOT DEPLOY.{RESET}")
    elif final_grade < 90:
        print(f"{YELLOW}VERDICT: FUNCTIONAL BUT SLOW. NEEDS OPTIMIZATION.{RESET}")
    else:
        print(f"{GREEN}VERDICT: HIGH PERFORMANCE. READY FOR PRODUCTION.{RESET}")

if __name__ == "__main__":
    # Small delay to let user read the intro
    time.sleep(1)
    run_benchmark()