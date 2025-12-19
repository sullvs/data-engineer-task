import time
import redis
import psycopg2
import requests
import argparse

EXTERNAL_ENDPOINT = "https://example.com/engagement-events"


def send_to_external_system(payload):
    try:
        response = requests.post(
            EXTERNAL_ENDPOINT,
            json=payload,
            timeout=2
        )
        response.raise_for_status()
    except Exception as e:
        print(f"External system failed: {e}")


DB_CONFIG = {
    "host": "postgres",
    "dbname": "app_db",
    "user": "app_user",
    "password": "app_password"
}

redis_client = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True
)

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

OFFSET_FILE = "offset.txt"


def load_offset():
    try:
        with open(OFFSET_FILE, "r") as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return 0


def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        f.write(str(offset))

REDIS_KEY = "content_engagement_last_10_min"


def update_redis_aggregation(content_id, engagement_seconds):
    if engagement_seconds is None:
        return

    redis_client.zincrby(
        REDIS_KEY,
        engagement_seconds,
        str(content_id)
    )


def update_redis_aggregation(content_id, engagement_seconds):
    if engagement_seconds is None:
        return

    redis_client.zincrby(
        REDIS_KEY,
        engagement_seconds,
        str(content_id)
    )

def insert_into_analytics_db(event):
    query = """
        INSERT INTO analytics_engagement_events
        (event_id, content_id, content_type, user_id, event_type, event_ts,
         engagement_seconds, engagement_pct)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO NOTHING
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, event)

def parse_args():
    parser = argparse.ArgumentParser(description="Engagement events processor")
    parser.add_argument(
        "--from-id",
        type=int,
        help="Backfill mode: start processing from a specific event id"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    backfill_mode = args.from_id is not None

    if args.from_id is not None:

        last_offset = args.from_id
        print(f"Starting BACKFILL from event id {last_offset}")
        backfill_mode = True
    else:
        last_offset = load_offset()
        print(f"Starting STREAMING from offset {last_offset}")
        backfill_mode = False



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

            update_redis_aggregation(content_id, engagement_seconds)

            print(
                f"event_id={event_id}, "
                f"type={content_type}, "
                f"duration_ms={duration_ms}, "
                f"engagement_seconds={engagement_seconds}, "
                f"engagement_pct={engagement_pct}"
            )

            last_offset = event_id
            if not backfill_mode:
                save_offset(last_offset)


            analytics_event = (
                event_id,
                content_id,
                content_type,
                user_id,
                event_type,
                event_ts,
                engagement_seconds,
                engagement_pct
            )

            insert_into_analytics_db(analytics_event)
            
            external_payload = {
                "event_id": event_id,
                "content_id": str(content_id),
                "content_type": content_type,
                "event_type": event_type,
                "event_ts": event_ts.isoformat(),
                "engagement_seconds": engagement_seconds,
                "engagement_pct": engagement_pct,
            }

            send_to_external_system(external_payload)
        
        if backfill_mode:
            print("Backfill completed")
            break

        if not events:
            print("No new events")

            time.sleep(5)
        else:
            print("No new events")

        time.sleep(5)

if __name__ == "__main__":
    main()
