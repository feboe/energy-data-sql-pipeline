CREATE TABLE IF NOT EXISTS raw_imports (
    id BIGSERIAL PRIMARY KEY,
    source_system TEXT NOT NULL,
    source_series_id TEXT NOT NULL,
    series_name TEXT NOT NULL,
    region TEXT NOT NULL,
    resolution TEXT NOT NULL,
    unit TEXT NOT NULL,
    chunk_timestamp_ms BIGINT NOT NULL,
    chunk_timestamp TIMESTAMPTZ NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_url TEXT NOT NULL,
    raw_payload JSONB NOT NULL,
    CONSTRAINT uq_raw_import_identity
        UNIQUE (source_system, source_series_id, region, resolution, chunk_timestamp_ms)
);

CREATE TABLE IF NOT EXISTS measurements (
    id BIGSERIAL PRIMARY KEY,
    raw_import_id BIGINT NOT NULL,
    source_system TEXT NOT NULL,
    source_series_id TEXT NOT NULL,
    series_name TEXT NOT NULL,
    region TEXT NOT NULL,
    resolution TEXT NOT NULL,
    unit TEXT NOT NULL,
    observation_timestamp_ms BIGINT NOT NULL,
    observation_timestamp TIMESTAMPTZ NOT NULL,
    value NUMERIC,
    CONSTRAINT fk_measurements_raw_import
        FOREIGN KEY (raw_import_id) REFERENCES raw_imports(id) ON DELETE CASCADE,
    CONSTRAINT uq_measurement_identity
        UNIQUE (source_system, source_series_id, region, resolution, observation_timestamp_ms)
);

CREATE INDEX IF NOT EXISTS idx_raw_imports_chunk_timestamp_ms
    ON raw_imports (chunk_timestamp_ms);

CREATE INDEX IF NOT EXISTS idx_measurements_raw_import_id
    ON measurements (raw_import_id);

CREATE INDEX IF NOT EXISTS idx_measurements_observation_timestamp
    ON measurements (observation_timestamp);
