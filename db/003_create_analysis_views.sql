DROP VIEW IF EXISTS negative_price_events;
DROP VIEW IF EXISTS hourly_market_forecast_features;
DROP VIEW IF EXISTS hourly_market_calendar_features;
DROP VIEW IF EXISTS hourly_market_features;
DROP VIEW IF EXISTS cleaned_measurements;


CREATE OR REPLACE VIEW cleaned_measurements AS
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
    value
FROM measurements
WHERE value IS NOT NULL;


CREATE OR REPLACE VIEW hourly_market_features AS
SELECT
    region,
    resolution,
    observation_timestamp,
    MAX(value) FILTER (WHERE series_name = 'day_ahead_price') AS day_ahead_price,
    MAX(value) FILTER (WHERE series_name = 'offshore_wind_generation') AS offshore_wind_generation,
    MAX(value) FILTER (WHERE series_name = 'onshore_wind_generation') AS onshore_wind_generation,
    MAX(value) FILTER (WHERE series_name = 'photovoltaics_generation') AS solar_generation,
    MAX(value) FILTER (WHERE series_name = 'grid_load') AS grid_load,
    MAX(value) FILTER (WHERE series_name = 'residual_load') AS residual_load,
    MAX(value) FILTER (WHERE series_name = 'forecasted_offshore_wind_generation') AS forecasted_offshore_wind_generation,
    MAX(value) FILTER (WHERE series_name = 'forecasted_onshore_wind_generation') AS forecasted_onshore_wind_generation,
    MAX(value) FILTER (WHERE series_name = 'forecasted_photovoltaics_generation') AS forecasted_solar_generation,
    MAX(value) FILTER (WHERE series_name = 'forecasted_grid_load') AS forecasted_grid_load
FROM cleaned_measurements
WHERE resolution = 'hour'
GROUP BY  
    region,
    resolution,
    observation_timestamp;


CREATE OR REPLACE VIEW hourly_market_calendar_features AS
SELECT
    region,
    resolution,
    observation_timestamp,
    day_ahead_price,
    offshore_wind_generation,
    onshore_wind_generation,
    solar_generation,
    grid_load,
    residual_load,
    forecasted_offshore_wind_generation,
    forecasted_onshore_wind_generation,
    forecasted_solar_generation,
    forecasted_grid_load,
    observation_timestamp AT TIME ZONE 'Europe/Berlin' AS local_timestamp,
    (observation_timestamp AT TIME ZONE 'Europe/Berlin')::date AS local_date,

    EXTRACT(HOUR FROM observation_timestamp AT TIME ZONE 'Europe/Berlin')::int AS local_hour,
    EXTRACT(ISODOW FROM observation_timestamp AT TIME ZONE 'Europe/Berlin')::int AS day_of_week,
    EXTRACT(MONTH FROM observation_timestamp AT TIME ZONE 'Europe/Berlin')::int AS month,
    EXTRACT(YEAR FROM observation_timestamp AT TIME ZONE 'Europe/Berlin')::int AS year,

    CASE
        WHEN EXTRACT(ISODOW FROM observation_timestamp AT TIME ZONE 'Europe/Berlin') IN (6, 7)
        THEN TRUE
        ELSE FALSE
    END AS is_weekend,

    CASE
        WHEN EXTRACT(HOUR FROM observation_timestamp AT TIME ZONE 'Europe/Berlin') BETWEEN 6 AND 21
        THEN 'day'
        ELSE 'night'
    END AS day_night,

    CASE
        WHEN EXTRACT(MONTH FROM observation_timestamp AT TIME ZONE 'Europe/Berlin') IN (12, 1, 2) THEN 'winter'
        WHEN EXTRACT(MONTH FROM observation_timestamp AT TIME ZONE 'Europe/Berlin') IN (3, 4, 5) THEN 'spring'
        WHEN EXTRACT(MONTH FROM observation_timestamp AT TIME ZONE 'Europe/Berlin') IN (6, 7, 8) THEN 'summer'
        WHEN EXTRACT(MONTH FROM observation_timestamp AT TIME ZONE 'Europe/Berlin') IN (9, 10, 11) THEN 'autumn'
    END AS season
FROM hourly_market_features;


CREATE OR REPLACE VIEW hourly_market_forecast_features AS
SELECT
    region,
    resolution,
    observation_timestamp,
    day_ahead_price,
    offshore_wind_generation,
    onshore_wind_generation,
    solar_generation,
    grid_load,
    residual_load,
    forecasted_offshore_wind_generation,
    forecasted_onshore_wind_generation,
    forecasted_solar_generation,
    forecasted_grid_load,
    local_timestamp,
    local_date,
    local_hour,
    day_of_week,
    month,
    year,
    is_weekend,
    day_night,
    season,
    forecasted_onshore_wind_generation + forecasted_offshore_wind_generation AS forecasted_wind_generation,
    forecasted_onshore_wind_generation + forecasted_offshore_wind_generation + forecasted_solar_generation AS forecasted_wind_solar_generation,
    (
        forecasted_onshore_wind_generation
        + forecasted_offshore_wind_generation
        + forecasted_solar_generation
    ) / NULLIF(forecasted_grid_load, 0) AS forecasted_wind_solar_load_ratio,
    forecasted_solar_generation / NULLIF(
        forecasted_onshore_wind_generation
        + forecasted_offshore_wind_generation
        + forecasted_solar_generation,
        0
    ) AS forecasted_solar_share_of_wind_solar,
    (forecasted_onshore_wind_generation + forecasted_offshore_wind_generation) / NULLIF(
        forecasted_onshore_wind_generation
        + forecasted_offshore_wind_generation
        + forecasted_solar_generation,
        0
    ) AS forecasted_wind_share_of_wind_solar,
    forecasted_grid_load - (
        forecasted_onshore_wind_generation
        + forecasted_offshore_wind_generation
        + forecasted_solar_generation
    ) AS forecasted_residual_load
FROM hourly_market_calendar_features;


CREATE OR REPLACE VIEW negative_price_events AS
WITH negative_hours AS (
    SELECT
        region,
        resolution,
        observation_timestamp,
        local_timestamp,
        day_ahead_price,
        offshore_wind_generation,
        onshore_wind_generation,
        solar_generation,
        grid_load,
        residual_load,
        forecasted_grid_load,
        forecasted_wind_generation,
        forecasted_solar_generation,
        forecasted_wind_solar_generation,
        forecasted_wind_solar_load_ratio,
        forecasted_solar_share_of_wind_solar,
        forecasted_wind_share_of_wind_solar,
        forecasted_residual_load,
        CASE
            WHEN LAG(observation_timestamp) OVER (
                PARTITION BY region, resolution
                ORDER BY observation_timestamp
            ) = observation_timestamp - INTERVAL '1 hour'
            THEN 0
            ELSE 1
        END AS starts_new_event
    FROM hourly_market_forecast_features
    WHERE day_ahead_price < 0
),
event_groups AS (
    SELECT
        region,
        resolution,
        observation_timestamp,
        local_timestamp,
        day_ahead_price,
        offshore_wind_generation,
        onshore_wind_generation,
        solar_generation,
        grid_load,
        residual_load,
        forecasted_grid_load,
        forecasted_wind_generation,
        forecasted_solar_generation,
        forecasted_wind_solar_generation,
        forecasted_wind_solar_load_ratio,
        forecasted_solar_share_of_wind_solar,
        forecasted_wind_share_of_wind_solar,
        forecasted_residual_load,
        starts_new_event,
        SUM(starts_new_event) OVER (
            PARTITION BY region, resolution
            ORDER BY observation_timestamp
        ) AS event_id
    FROM negative_hours
)
SELECT
    region,
    resolution,
    event_id,
    MIN(observation_timestamp) AS event_start_utc,
    MAX(observation_timestamp) AS event_end_utc,
    MIN(local_timestamp) AS event_start_local,
    MAX(local_timestamp) AS event_end_local,
    COUNT(*) AS duration_hours,

    MIN(day_ahead_price) AS min_day_ahead_price,
    MAX(day_ahead_price) AS max_day_ahead_price,
    AVG(day_ahead_price) AS avg_day_ahead_price,

    AVG(forecasted_grid_load) AS avg_forecasted_grid_load,
    AVG(forecasted_wind_generation) AS avg_forecasted_wind_generation,
    AVG(forecasted_solar_generation) AS avg_forecasted_solar_generation,
    AVG(forecasted_wind_solar_generation) AS avg_forecasted_wind_solar_generation,
    AVG(forecasted_wind_solar_load_ratio) AS avg_forecasted_wind_solar_load_ratio,
    AVG(forecasted_solar_share_of_wind_solar) AS avg_forecasted_solar_share_of_wind_solar,
    AVG(forecasted_wind_share_of_wind_solar) AS avg_forecasted_wind_share_of_wind_solar,

    AVG(forecasted_wind_solar_generation - (onshore_wind_generation + offshore_wind_generation + solar_generation)) AS avg_forecast_error_wind_solar_generation,
    AVG(forecasted_grid_load - grid_load) AS avg_forecast_error_grid_load,
    AVG(forecasted_residual_load - residual_load) AS avg_forecast_error_residual_load

FROM event_groups
GROUP BY
    region,
    resolution,
    event_id;
