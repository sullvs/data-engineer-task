-- ================================
-- Enable extensions
-- ================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ================================
-- Content catalog (dimension table)
-- ================================
CREATE TABLE IF NOT EXISTS content (
  id UUID PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  content_type TEXT CHECK (content_type IN ('podcast', 'newsletter', 'video')),
  length_seconds INTEGER,
  publish_ts TIMESTAMPTZ NOT NULL
);

-- ================================
-- Engagement events (fact table)
-- ================================
CREATE TABLE IF NOT EXISTS engagement_events (
  id BIGSERIAL PRIMARY KEY,
  content_id UUID REFERENCES content(id),
  user_id UUID,
  event_type TEXT CHECK (event_type IN ('play', 'pause', 'finish', 'click')),
  event_ts TIMESTAMPTZ NOT NULL,
  duration_ms INTEGER,
  device TEXT,
  raw_payload JSONB
);

-- ================================
-- Destenation table (BigQuery replacement)
-- ================================

CREATE TABLE IF NOT EXISTS analytics_engagement_events (
  event_id BIGINT PRIMARY KEY,
  content_id UUID,
  content_type TEXT,
  user_id UUID,
  event_type TEXT,
  event_ts TIMESTAMPTZ,
  engagement_seconds DOUBLE PRECISION,
  engagement_pct DOUBLE PRECISION
);


-- ================================
-- Indexes (performance)
-- ================================
CREATE INDEX IF NOT EXISTS idx_engagement_events_ts
ON engagement_events (event_ts);

CREATE INDEX IF NOT EXISTS idx_engagement_events_content
ON engagement_events (content_id);

-- ================================
-- Dummy content data
-- ================================
INSERT INTO content (id, slug, title, content_type, length_seconds, publish_ts)
VALUES
  ('11111111-1111-1111-1111-111111111111', 'ai-podcast-1', 'AI Podcast Ep 1', 'podcast', 1800, now() - interval '10 days'),
  ('22222222-2222-2222-2222-222222222222', 'data-video-1', 'Data Engineering Intro', 'video', 900, now() - interval '5 days'),
  ('33333333-3333-3333-3333-333333333333', 'ml-newsletter-1', 'ML Weekly #1', 'newsletter', NULL, now() - interval '2 days')
ON CONFLICT (id) DO NOTHING;

-- ================================
-- Dummy engagement events
-- ================================
INSERT INTO engagement_events
  (content_id, user_id, event_type, event_ts, duration_ms, device, raw_payload)
VALUES
  (
    '11111111-1111-1111-1111-111111111111',
    gen_random_uuid(),
    'play',
    now() - interval '3 minutes',
    60000,
    'ios',
    '{"volume": 80}'
  ),
  (
    '11111111-1111-1111-1111-111111111111',
    gen_random_uuid(),
    'finish',
    now() - interval '2 minutes',
    1800000,
    'web',
    '{}'
  ),
  (
    '22222222-2222-2222-2222-222222222222',
    gen_random_uuid(),
    'click',
    now() - interval '1 minute',
    NULL,
    'android',
    '{"button": "subscribe"}'
  );
