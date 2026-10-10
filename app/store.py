import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB = Path(__file__).resolve().parents[1] / "chat_history.db"

def init_db():
    with sqlite3.connect(DB) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          session_id TEXT NOT NULL,
          role TEXT NOT NULL,
          content TEXT NOT NULL,
          created_at TEXT NOT NULL
        )''')

def save(session_id, role, content):
    with sqlite3.connect(DB) as db:
        db.execute("INSERT INTO messages(session_id,role,content,created_at) VALUES(?,?,?,?)",
                   (session_id, role, content, datetime.now(timezone.utc).isoformat()))

def history(session_id):
    with sqlite3.connect(DB) as db:
        return [{"role":r,"content":c} for r,c in db.execute(
            "SELECT role,content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT 20",
            (session_id,)).fetchall()[::-1]]
