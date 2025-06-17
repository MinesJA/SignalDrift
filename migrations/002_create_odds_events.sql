-- Create OddsEvent table
CREATE TABLE odds_events (
    id BIGSERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ,
    og_odds DECIMAL NOT NULL,
    impl_prob DECIMAL NOT NULL CHECK (impl_prob >= 0 AND impl_prob <= 1),
    fair_odds DECIMAL NOT NULL,
    source odds_source NOT NULL,
    odds_type odds_type NOT NULL,
    question TEXT NOT NULL,
    meta JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to TimescaleDB hypertable (partitioned by timestamp)
SELECT create_hypertable('odds_events', 'timestamp');

-- Create indexes for common queries
CREATE INDEX idx_odds_events_request_id ON odds_events (request_id);
CREATE INDEX idx_odds_events_source ON odds_events (source);
CREATE INDEX idx_odds_events_question ON odds_events (question);
CREATE INDEX idx_odds_events_timestamp_source ON odds_events (timestamp, source);

-- Create index on meta JSONB column for efficient metadata queries
CREATE INDEX idx_odds_events_meta ON odds_events USING GIN (meta);