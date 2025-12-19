# Data Engineering Take-Home Task

## Overview

This project implements a simplified data streaming pipeline for processing user engagement events.

The goal is not to build a production-ready system, but to demonstrate:

* Understanding of streaming concepts
* Incremental data processing
* Basic transformations and enrichment
* Fan-out to multiple downstream systems
* Practical design trade-offs

The pipeline reads engagement events from PostgreSQL, enriches and transforms them, and then sends the processed data to multiple destinations including Redis, an analytics database, and a mock external system.

---

## High-Level Architecture

**Source**

* PostgreSQL database containing raw engagement events and content metadata.

**Processing Layer**

* A Python service that:

  * Reads new events incrementally
  * Enriches events with content information
  * Calculates derived engagement metrics
  * Fans out events to multiple sinks

**Sinks**

* **Redis** for real-time aggregation
* **Analytics database** (PostgreSQL table) as a stand-in for a data warehouse
* **External system** simulated via HTTP requests

---

## Data Model

### `content`

Stores metadata about content items.

Key fields:

* `id` – unique content identifier
* `content_type` – podcast, video, or newsletter
* `length_seconds` – used to calculate engagement percentage

### `engagement_events`

Stores raw user interaction events.

Key fields:

* `id` – auto-incremented identifier used as a streaming offset
* `content_id` – foreign key to content
* `event_ts` – event timestamp
* `duration_ms` – engagement duration when applicable

---

## Transformations & Enrichment

For each event:

1. Join with the `content` table to enrich with content metadata.
2. Compute:

   * `engagement_seconds = duration_ms / 1000`
   * `engagement_pct = engagement_seconds / length_seconds`
3. Handle missing values safely (e.g. NULL durations).

---

## Streaming Logic

* Events are read incrementally using:

  ```sql
  WHERE id > last_offset
  ```
* The last processed event ID is persisted locally to avoid reprocessing.
* The service polls for new events every few seconds, keeping latency below the required threshold.

---

## Redis Real-Time Aggregation

* Redis is used to maintain a near-real-time view of engagement.
* A Sorted Set stores cumulative engagement seconds per content item.
* This provides a fast approximation of “most engaged content in the last 10 minutes”.

This approach prioritizes simplicity and low latency over perfectly precise windowing.

---

## Analytics Sink (Warehouse-Like Storage)

* Processed events are written to an analytics table in PostgreSQL.
* `event_id` is the primary key to ensure idempotent inserts.
* This simulates how data would be stored in a columnar warehouse such as BigQuery.

---

## External System Integration

* Events are also sent via HTTP to a mock external endpoint.
* Failures are logged but do not block processing.
* This reflects real-world scenarios where downstream systems are outside our control.

---

## Backfill Mode

The pipeline supports reprocessing historical data using a backfill mode.

Example:

```bash
python read_events.py --from-id 100
```

Behavior:

* Starts processing from a specified event ID
* Does not update the streaming offset
* Runs once and exits

This allows historical reprocessing without affecting real-time ingestion state.

---

## Exactly-Once Semantics (Practical)

This project achieves practical exactly-once behavior through:

* Incremental reads using ordered IDs
* Persisted offsets for streaming mode
* Idempotent writes to the analytics sink

Redis and external systems use best-effort delivery, which is acceptable for their intended use cases.

---

## Running the Project

### Prerequisites

* Docker
* Docker Compose

### Start the environment

```bash
docker compose up --build
```

This will:

* Initialize the database schema automatically
* Insert sample data
* Start PostgreSQL, Redis, and the app service

### Run the processor

```bash
docker compose exec app python read_events.py
```

### Run backfill

```bash
docker compose exec app python read_events.py --from-id 0
```

---

## Testing & Validation

The system was validated using end-to-end testing:

* Fresh startup to verify reproducibility
* Incremental event ingestion
* Redis aggregation inspection via Redis CLI
* Analytics table verification via SQL queries
* Backfill runs without affecting streaming state

---

## Design Decisions & Trade-Offs

* PostgreSQL is used instead of BigQuery to keep the project fully reproducible.
* Redis aggregation is approximate rather than perfectly windowed.
* Offset persistence is file-based for simplicity.
* External system integration is mocked to avoid unnecessary setup complexity.

---

## Future Improvements

Given more time, the following could be added:

* Proper time-windowed aggregation in Redis
* Message broker (e.g. Kafka) for stronger delivery guarantees
* Centralized offset storage
* Metrics and monitoring
* Real BigQuery integration

---

## Conclusion

This project demonstrates a simple but complete data streaming pipeline with clear design decisions and practical trade-offs. The focus is on correctness, clarity, and reproducibility rather than over-engineering.