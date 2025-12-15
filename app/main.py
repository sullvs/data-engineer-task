import os
import time
import psycopg2

conn = psycopg2.connect(
    host=os.environ["DB_HOST"],
    port=os.environ["DB_PORT"],
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
)

print("Connected to PostgreSQL")

while True:
    with conn.cursor() as cur:
        cur.execute("SELECT NOW();")
        result = cur.fetchone()
        print("DB time:", result)

    time.sleep(5)
