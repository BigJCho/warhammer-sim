import sqlite3

DB_FILE = 'warhammer.db'

# loop
# select and check if its in there
# if not add it

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

keys = input('Keywords separated by comma:\n> ')
keywords = [k.strip().lower() for k in keys.split(',')]

with get_db() as conn:
    for word in keywords:    
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO keywords
            (name)
            VALUES (?)
        """, (
            word,
        ))