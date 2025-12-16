import time
import psycopg2

DB_CONFIG = {
    "host": "postgres",
    "dbname": "app_db",
    "user": "app_user",
    "password": "app_password"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def read_events(last_offset):
    query = """
        SELECT
            e.id,
            e.content_id,
            c.content_type,
            c.length_seconds,
            e.user_id,
            e.event_type,
            e.event_ts,
            e.duration_ms
        FROM engagement_events e
        JOIN content c ON e.content_id = c.id
        WHERE e.id > %s
        ORDER BY e.id
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (last_offset,))
            rows = cur.fetchall()
    return rows

def calculate_engagement_seconds(duration_ms):
    if duration_ms is None:
        return None
    return duration_ms / 1000


def calculate_engagement_pct(engagement_seconds, length_seconds):
    if engagement_seconds is None or length_seconds is None:
        return None
    return round(engagement_seconds / length_seconds, 2)


def main():
    last_offset = 0
    print("Starting event reader...")

    while True:
        events = read_events(last_offset)


        for event in events:
            (
                event_id,
                content_id,
                content_type,
                length_seconds,
                user_id,
                event_type,
                event_ts,
                duration_ms
            ) = event

            engagement_seconds = calculate_engagement_seconds(duration_ms)
            engagement_pct = calculate_engagement_pct(
                engagement_seconds, length_seconds
            )

            print(
                f"event_id={event_id}, "
                f"type={content_type}, "
                f"duration_ms={duration_ms}, "
                f"engagement_seconds={engagement_seconds}, "
                f"engagement_pct={engagement_pct}"
            )

            last_offset = event_id
        else:
            print("No new events")

        time.sleep(5)

if __name__ == "__main__":
    main()
