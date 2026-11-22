import os
import psycopg2
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Headless mode so cron can render charts without a GUI
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
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

# Build absolute path so cron saves to the right folder regardless of working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, "charts", "system_metrics_latest.png")

def fetch_metrics():
    """Query the last 24 hours of system metrics from PostgreSQL."""
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = """
            SELECT recorded_at, cpu_percent, memory_percent, disk_percent
            FROM server_metrics
            WHERE recorded_at >= NOW() - INTERVAL '24 hours'
            ORDER BY recorded_at ASC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = ["recorded_at", "cpu_percent", "memory_percent", "disk_percent"]
        return pd.DataFrame(rows, columns=columns)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def generate_chart(df):
    """Plot CPU, RAM, and Disk percentages and save as a PNG."""
    if df.empty:
        print("No data found to plot.")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(df["recorded_at"], df["cpu_percent"], label="CPU %", marker="o", linewidth=2)
    plt.plot(df["recorded_at"], df["memory_percent"], label="Memory %", marker="s", linewidth=2)
    plt.plot(df["recorded_at"], df["disk_percent"], label="Disk %", marker="^", linewidth=2)

    plt.title("Ubuntu System Telemetry (Last 24 Hours)", fontsize=14, fontweight="bold")
    plt.xlabel("Timestamp")
    plt.ylabel("Usage (%)")
    plt.ylim(0, 100)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(loc="upper left")

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    plt.gcf().autofmt_xdate()

    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=150)
    plt.close()
    print(f"Chart saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    data = fetch_metrics()
    generate_chart(data)
