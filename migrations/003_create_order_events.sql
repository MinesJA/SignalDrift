-- Create OrderEvent table
CREATE TABLE order_events (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    order_signal order_signal NOT NULL,
    price DECIMAL NOT NULL CHECK (price > 0),
    size INTEGER NOT NULL CHECK (size > 0),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to TimescaleDB hypertable (partitioned by timestamp)
SELECT create_hypertable('order_events', 'timestamp');

-- Create indexes for common queries
CREATE INDEX idx_order_events_order_signal ON order_events (order_signal);
CREATE INDEX idx_order_events_timestamp_signal ON order_events (timestamp, order_signal);
CREATE INDEX idx_order_events_price ON order_events (price);