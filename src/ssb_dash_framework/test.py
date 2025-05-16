import psycopg2

# Connection parameters
conn = psycopg2.connect(
    host="localhost",  # Service name from docker-compose
    port=5432,
    user="dev",
    password="devpwd",
    dbname="devdb",
)

cur = conn.cursor()
cur.execute("SELECT version();")
print(cur.fetchone())
