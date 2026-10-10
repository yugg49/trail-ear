import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / ".trailear" / "trailear.db"


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY,
        date TEXT NOT NULL,
        place TEXT NOT NULL,
        journal_text TEXT
    );
    CREATE TABLE IF NOT EXISTS detections (
        id INTEGER PRIMARY KEY,
        session_id INTEGER NOT NULL REFERENCES sessions(id),
        species TEXT NOT NULL,
        scientific_name TEXT,
        count INTEGER,
        best_confidence REAL
    );
    """)
    return conn


def save_session(place, species, journal_text):
    conn = connect()
    cur = conn.execute(
        "INSERT INTO sessions (date, place, journal_text) VALUES (?, ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), place, journal_text),
    )
    sid = cur.lastrowid
    conn.executemany(
        "INSERT INTO detections (session_id, species, scientific_name, count, "
        "best_confidence) VALUES (?, ?, ?, ?, ?)",
        [(sid, s["common_name"], s["scientific_name"], s["count"],
          s["best_confidence"]) for s in species],
    )
    conn.commit()
    conn.close()
    return sid


def life_list(min_conf=0.5):
    conn = connect()
    rows = conn.execute("""
        SELECT d.species, d.scientific_name, MIN(s.date), SUM(d.count),
               MAX(d.best_confidence)
        FROM detections d JOIN sessions s ON s.id = d.session_id
        WHERE d.best_confidence >= ?
        GROUP BY d.species ORDER BY MIN(s.date)
    """, (min_conf,)).fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    from trailear.identify import identify, summarize
    from trailear.journal import write_entry

    path = sys.argv[1]
    place = sys.argv[2] if len(sys.argv) > 2 else "Pune"
    species = summarize(identify(path))
    if species:
        entry = write_entry(species, place)
        sid = save_session(place, species, entry)
        print(f"\nSaved session {sid}.\n{entry}\n")
    print("Life list (confidence 50%+):")
    for name, sci, first, total, best in life_list():
        print(f"  {name} ({sci}) - first {first[:10]}, "
              f"{total} detections, best {best:.0%}")
