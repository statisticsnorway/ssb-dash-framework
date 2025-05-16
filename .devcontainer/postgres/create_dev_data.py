import os

import psycopg2

conn = psycopg2.connect(
    host=os.environ.get(
        "DB_HOST", "host.docker.internal"
    ),  # Use localhost for devcontainer access
    user=os.environ.get("DB_USER", "dev"),
    password=os.environ.get("DB_PASSWORD", "devpwd"),
    dbname=os.environ.get("DB_NAME", "devdb"),
)

cur = conn.cursor()
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS test_table (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL
    );
"""
)
cur.execute(
    "INSERT INTO test_table (name) VALUES (%s), (%s), (%s);",
    ("Alice", "Bob", "Charlie"),
)
conn.commit()
cur.close()
conn.close()
print("Test data inserted.")
