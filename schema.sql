-- schema.sql
-- Run this against your PostgreSQL database BEFORE running ingest.py:
--   psql $PG_DSN -f schema.sql

CREATE TABLE IF NOT EXISTS subjects (
    subject_id  TEXT PRIMARY KEY,
    age         TEXT,
    sex         TEXT,
    species     TEXT,
    institution TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id     TEXT PRIMARY KEY,      -- nwb.identifier, e.g. "H09_5"
    subject_id     TEXT REFERENCES subjects (subject_id),
    session_date   TIMESTAMPTZ,
    nwb_asset_path TEXT
);

CREATE TABLE IF NOT EXISTS neurons (
    neuron_id        SERIAL PRIMARY KEY,
    session_id       TEXT REFERENCES sessions (session_id),
    unit_index       INT,
    brain_region     TEXT,
    n_spikes         INT,
    mean_firing_rate FLOAT,              -- Hz (spikes / recording duration)
    spike_times      FLOAT[]             -- all spike timestamps (seconds)
);

CREATE TABLE IF NOT EXISTS trials (
    trial_id         SERIAL PRIMARY KEY,
    session_id       TEXT REFERENCES sessions (session_id),
    trial_index      INT,
    phase            TEXT,               -- 'encoding' or 'recognition'
    start_time       FLOAT,
    stop_time        FLOAT,
    stimulus_label   TEXT,               -- category string, e.g. "face"
    is_old_stimulus  BOOLEAN,            -- TRUE = seen before (recognition phase)
    subject_response INT,                -- 1-6 confidence scale
    is_correct       BOOLEAN
);
