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
rows_left = conn.execute(
    "SELECT COUNT(*) FROM daily_content WHERE module='bubble'"
).fetchone()[0]
# #region agent log
import json
import time

_log = ROOT / "debug-397eeb.log"
try:
    with _log.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "sessionId": "397eeb",
                    "runId": "pre-fix",
                    "hypothesisId": "A",
                    "location": "clear_bubble_cache.py",
                    "message": "cache_cleared",
                    "data": {
                        "db_path": str(DB),
                        "deleted_rows": cur.rowcount,
                        "rows_remaining": rows_left,
                    },
                    "timestamp": int(time.time() * 1000),
                },
                ensure_ascii=False,
            )
            + "\n"
        )
except OSError:
    pass
# #endregion
print(f"Cleared {cur.rowcount} bubble cache row(s). Reload /api/today or refresh the app.")
conn.close()
