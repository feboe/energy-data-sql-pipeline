DROP VIEW IF EXISTS missing_hourly_measurements;
DROP VIEW IF EXISTS measurement_quality_issues;


CREATE OR REPLACE VIEW measurement_quality_issues AS
SELECT
    id,
    raw_import_id,
    source_system,
    source_series_id,
    series_name,
    region,
    resolution,
    unit,
    observation_timestamp_ms,
    observation_timestamp,
    value,
    CASE
        WHEN value IS NULL THEN 'missing_value'
        WHEN series_name LIKE '%generation' AND value < 0 THEN 'negative_generation'
        WHEN series_name = 'grid_load' AND value < 0 THEN 'negative_load'
        ELSE NULL
    END AS quality_issue
FROM measurements
WHERE
    series_name <> 'nuclear_generation'
    AND (
        value IS NULL
        OR (series_name LIKE '%generation' AND value < 0)
        OR (series_name = 'grid_load' AND value < 0)
    );


CREATE OR REPLACE VIEW missing_hourly_measurements AS
WITH expected_series AS (
    SELECT DISTINCT
        source_system,
        source_series_id,
        series_name,
        region,
        resolution
    FROM measurements
    WHERE region = 'DE-LU'
        AND resolution = 'hour'
        AND series_name <> 'nuclear_generation'
),
bounds AS (
    SELECT
        MIN(observation_timestamp) AS min_ts,
        MAX(observation_timestamp) AS max_ts
    FROM measurements
    WHERE region = 'DE-LU'
        AND resolution = 'hour'
),
expected_hours AS (
    SELECT generate_series(
        min_ts,
        max_ts,
        INTERVAL '1 hour'
    ) AS observation_timestamp
    FROM bounds
),
expected AS (
    SELECT
        s.source_system,
        s.source_series_id,
        s.series_name,
        s.region,
        s.resolution,
        h.observation_timestamp
    FROM expected_series s
    CROSS JOIN expected_hours h
)
SELECT
    e.source_system,
    e.source_series_id,
    e.series_name,
    e.region,
    e.resolution,
    e.observation_timestamp
FROM expected e
LEFT JOIN measurements m
    ON m.source_system = e.source_system
    AND m.source_series_id = e.source_series_id
    AND m.region = e.region
    AND m.resolution = e.resolution
    AND m.observation_timestamp = e.observation_timestamp
WHERE m.id IS NULL;
