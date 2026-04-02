import sqlite3

def get_db():
    conn = sqlite3.connect("database.db")
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    # JOBS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        company TEXT,
        role TEXT,
        jd TEXT
    )
    """)

    # TOPICS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        topic TEXT,
        status TEXT DEFAULT 'not started',
        priority TEXT DEFAULT 'medium'
    )
    """)

    conn.commit()