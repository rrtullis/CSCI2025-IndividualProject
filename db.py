import sqlite3

def init_db():
    conn = sqlite3.connect("mastodon_posts.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            created_at DATETIME NOT NULL,
            query TEXT NOT NULL,
            instance TEXT NOT NULL,
            content TEXT NOT NULL,
            sentiment TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()