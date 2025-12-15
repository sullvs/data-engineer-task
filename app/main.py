import os
import time
import psycopg2

def wait_for_db():
    while True:
        try:
            conn = psycopg2.connect(
                host=os.environ["DB_HOST"],
                port=os.environ["DB_PORT"],
                dbname=os.environ["DB_NAME"],
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"],
            )
            conn.close()
            print("Connected to PostgreSQL")
            break
        except Exception as e:
            print("Waiting for PostgreSQL...", e)
            time.sleep(2)

wait_for_db()

while True:
    time.sleep(5)
