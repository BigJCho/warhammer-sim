import attack

with attack.get_db() as conn:
    conn.execute("""
                    INSERT INTO keywords (name) VALUES ('Blast')
                        """)
    