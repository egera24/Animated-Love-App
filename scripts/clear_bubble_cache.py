"""Delete today's cached bubble so LLM can regenerate."""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "app.db"

if not DB.exists():
    print("No database at data/app.db — nothing to clear.")
    sys.exit(0)

conn = sqlite3.connect(DB)
cur = conn.execute("DELETE FROM daily_content WHERE module='bubble'")
conn.commit()
print(f"Cleared {cur.rowcount} bubble cache row(s). Reload /api/today or refresh the app.")
conn.close()
