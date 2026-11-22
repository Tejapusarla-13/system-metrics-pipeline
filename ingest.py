import psutil
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "system_monitor"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

def collect_metrics():
    """Extract live system telemetry using psutil."""
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    processes = len(psutil.pids())
    return cpu, memory, disk, processes

def load_metrics(cpu, memory, disk, processes):
    """Load collected metrics into PostgreSQL."""
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO server_metrics (cpu_percent, memory_percent, disk_percent, active_processes)
            VALUES (%s, %s, %s, %s);
        """
        cursor.execute(insert_query, (cpu, memory, disk, processes))
        conn.commit()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Inserted -> CPU: {cpu}% | RAM: {memory}% | Disk: {disk}% | Processes: {processes}")

    except Exception as e:
        print(f"Error inserting data: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    metrics = collect_metrics()
    load_metrics(*metrics)
