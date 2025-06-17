-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create enum types for OddsEvent
CREATE TYPE odds_source AS ENUM (
    'BETFAIR',
    'FANDUEL',
    'PINNACLE',
    'POLYMARKET'
);

CREATE TYPE odds_type AS ENUM (
    'DECIMAL',
    'AMERICAN',
    'FRACTIONAL',
    'EXCHANGE'
);

-- Create enum types for OrderEvent
CREATE TYPE order_signal AS ENUM (
    'LIMIT_BUY',
    'LIMIT_SELL'
);