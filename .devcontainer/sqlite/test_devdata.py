from sqlalchemy import text

from ssb_dash_framework import create_database_engine

engine = create_database_engine(
    "sqlite", sqlite_path=".devcontainer/sqlite/mydb.sqlite"
)
query = text("SELECT * FROM enheter")
with engine.connect() as conn:
    result = conn.execute(query)
    rows = result.fetchall()
print(rows)
