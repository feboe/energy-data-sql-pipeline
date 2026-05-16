DROP VIEW IF EXISTS yearly_negative_price_event_summary;
DROP VIEW IF EXISTS negative_price_event_forecast_errors;
DROP VIEW IF EXISTS negative_price_events;
DROP VIEW IF EXISTS negative_price_event_hours;
DROP VIEW IF EXISTS hourly_negative_price_features;
DROP VIEW IF EXISTS hourly_system_features;
DROP VIEW IF EXISTS hourly_calendar_features;
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

    MAX(value) FILTER (WHERE series_name = 'grid_load') AS actual_grid_load,
    MAX(value) FILTER (WHERE series_name = 'offshore_wind_generation') AS actual_offshore_wind_generation,
    MAX(value) FILTER (WHERE series_name = 'onshore_wind_generation') AS actual_onshore_wind_generation,
    MAX(value) FILTER (WHERE series_name = 'photovoltaics_generation') AS actual_solar_generation,

    MAX(value) FILTER (WHERE series_name = 'forecasted_grid_load') AS forecasted_grid_load,
    MAX(value) FILTER (WHERE series_name = 'forecasted_offshore_wind_generation') AS forecasted_offshore_wind_generation,
    MAX(value) FILTER (WHERE series_name = 'forecasted_onshore_wind_generation') AS forecasted_onshore_wind_generation,
    MAX(value) FILTER (WHERE series_name = 'forecasted_photovoltaics_generation') AS forecasted_solar_generation

FROM cleaned_measurements
WHERE resolution = 'hour' AND region = 'DE-LU'
GROUP BY
    region,
    resolution,
    observation_timestamp;


CREATE OR REPLACE VIEW hourly_calendar_features AS
WITH market_with_local_time AS (
    SELECT
        m.*,
        m.observation_timestamp AT TIME ZONE 'Europe/Berlin' AS local_timestamp,
        (m.observation_timestamp AT TIME ZONE 'Europe/Berlin')::date AS local_date
    FROM hourly_market_features m
),

holiday_flags AS (
    SELECT
        h.holiday_date,
        BOOL_OR(h.is_nationwide) AS is_holiday_de_lu,
        STRING_AGG(DISTINCT h.holiday_name, ', ' ORDER BY h.holiday_name) AS holiday_name
    FROM holidays h
    WHERE h.region = 'DE' OR h.region = 'LU'
    GROUP BY h.holiday_date
)

SELECT
    m.*,

    EXTRACT(HOUR FROM m.local_timestamp)::int AS local_hour,
    EXTRACT(ISODOW FROM m.local_timestamp)::int AS day_of_week,
    EXTRACT(WEEK FROM m.local_timestamp)::int AS calendar_week,
    EXTRACT(MONTH FROM m.local_timestamp)::int AS month,
    EXTRACT(YEAR FROM m.local_timestamp)::int AS year,

    CASE
        WHEN EXTRACT(ISODOW FROM m.local_timestamp)::int IN (6, 7)
        THEN TRUE
        ELSE FALSE
    END AS is_weekend,

    COALESCE(h.is_holiday_de_lu, FALSE) AS is_holiday_de_lu,
    h.holiday_name,

    CASE
        WHEN EXTRACT(HOUR FROM m.local_timestamp)::int BETWEEN 6 AND 21
        THEN 'day'
        ELSE 'night'
    END AS day_night,

    CASE
        WHEN EXTRACT(MONTH FROM m.local_timestamp)::int IN (12, 1, 2) THEN 'winter'
        WHEN EXTRACT(MONTH FROM m.local_timestamp)::int IN (3, 4, 5) THEN 'spring'
        WHEN EXTRACT(MONTH FROM m.local_timestamp)::int IN (6, 7, 8) THEN 'summer'
        WHEN EXTRACT(MONTH FROM m.local_timestamp)::int IN (9, 10, 11) THEN 'autumn'
    END AS season

FROM market_with_local_time m
LEFT JOIN holiday_flags h
    ON m.local_date = h.holiday_date;


CREATE OR REPLACE VIEW hourly_system_features AS
WITH base AS (
    SELECT
        -- identifiers
        m.region,
        m.resolution,
        m.observation_timestamp,
        m.local_timestamp,
        m.local_date,

        -- calendar features
        m.year,
        m.month,
        m.calendar_week,
        m.day_of_week,
        m.local_hour,
        m.season,
        m.is_weekend,
        m.is_holiday_de_lu,
        m.holiday_name,
        m.day_night,

        -- market price
        m.day_ahead_price,

        -- actual values
        m.actual_grid_load,
        m.actual_onshore_wind_generation,
        m.actual_offshore_wind_generation,
        m.actual_solar_generation,

        -- forecast values
        m.forecasted_grid_load,
        m.forecasted_onshore_wind_generation,
        m.forecasted_offshore_wind_generation,
        m.forecasted_solar_generation,

        -- wind totals
        (
            m.actual_onshore_wind_generation
            + m.actual_offshore_wind_generation
        ) AS actual_wind_generation,

        (
            m.forecasted_onshore_wind_generation
            + m.forecasted_offshore_wind_generation
        ) AS forecasted_wind_generation

    FROM hourly_calendar_features m
),

system_features AS (
    SELECT
        b.*,

        -- wind + solar generation
        (
            b.actual_wind_generation
            + b.actual_solar_generation
        ) AS actual_wind_solar_generation,

        (
            b.forecasted_wind_generation
            + b.forecasted_solar_generation
        ) AS forecasted_wind_solar_generation,

        -- residual load based on wind + solar only
        (
            b.actual_grid_load
            - b.actual_wind_generation
            - b.actual_solar_generation
        ) AS actual_residual_load,

        (
            b.forecasted_grid_load
            - b.forecasted_wind_generation
            - b.forecasted_solar_generation
        ) AS forecasted_residual_load,

        -- wind + solar / load ratios
        (
            b.actual_wind_generation
            + b.actual_solar_generation
        ) / NULLIF(b.actual_grid_load, 0) AS actual_wind_solar_load_ratio,

        (
            b.forecasted_wind_generation
            + b.forecasted_solar_generation
        ) / NULLIF(b.forecasted_grid_load, 0) AS forecasted_wind_solar_load_ratio,

        -- solar / wind shares within wind + solar generation
        b.actual_solar_generation
            / NULLIF(b.actual_wind_generation + b.actual_solar_generation, 0)
            AS actual_solar_share_of_wind_solar,

        b.actual_wind_generation
            / NULLIF(b.actual_wind_generation + b.actual_solar_generation, 0)
            AS actual_wind_share_of_wind_solar,

        b.forecasted_solar_generation
            / NULLIF(b.forecasted_wind_generation + b.forecasted_solar_generation, 0)
            AS forecasted_solar_share_of_wind_solar,

        b.forecasted_wind_generation
            / NULLIF(b.forecasted_wind_generation + b.forecasted_solar_generation, 0)
            AS forecasted_wind_share_of_wind_solar

    FROM base b
)

SELECT
    sf.*,

    -- forecast errors: actual - forecast
    (
        sf.actual_grid_load
        - sf.forecasted_grid_load
    ) AS forecast_error_grid_load,

    (
        sf.actual_wind_generation
        - sf.forecasted_wind_generation
    ) AS forecast_error_wind_generation,

    (
        sf.actual_solar_generation
        - sf.forecasted_solar_generation
    ) AS forecast_error_solar_generation,

    (
        sf.actual_residual_load
        - sf.forecasted_residual_load
    ) AS forecast_error_residual_load,

    -- absolute forecast errors
    ABS(
        sf.actual_grid_load
        - sf.forecasted_grid_load
    ) AS abs_forecast_error_grid_load,

    ABS(
        sf.actual_wind_generation
        - sf.forecasted_wind_generation
    ) AS abs_forecast_error_wind_generation,

    ABS(
        sf.actual_solar_generation
        - sf.forecasted_solar_generation
    ) AS abs_forecast_error_solar_generation,

    ABS(
        sf.actual_residual_load
        - sf.forecasted_residual_load
    ) AS abs_forecast_error_residual_load

FROM system_features sf;


CREATE OR REPLACE VIEW hourly_negative_price_features AS
SELECT *
FROM hourly_system_features
WHERE day_ahead_price < 0;


CREATE OR REPLACE VIEW negative_price_event_hours AS
WITH marked AS (
    SELECT
        m.*,

        CASE
            WHEN LAG(m.observation_timestamp) OVER (
                PARTITION BY m.region, m.resolution
                ORDER BY m.observation_timestamp
            ) = m.observation_timestamp - INTERVAL '1 hour'
            THEN 0
            ELSE 1
        END AS starts_new_event

    FROM hourly_negative_price_features m
),

event_ids AS (
    SELECT
        marked.*,

        SUM(starts_new_event) OVER (
            PARTITION BY region, resolution
            ORDER BY observation_timestamp
        ) AS event_id

    FROM marked
)

SELECT
    e.region,
    e.resolution,
    e.event_id,

    ROW_NUMBER() OVER (
        PARTITION BY e.region, e.resolution, e.event_id
        ORDER BY e.observation_timestamp
    ) AS event_hour_index,

    e.observation_timestamp,
    e.local_timestamp,
    e.local_date,

    e.year,
    e.month,
    e.calendar_week,
    e.day_of_week,
    e.local_hour,
    e.season,
    e.is_weekend,
    e.is_holiday_de_lu,
    e.holiday_name,
    e.day_night,

    e.day_ahead_price,

    -- actual values
    e.actual_grid_load,
    e.actual_onshore_wind_generation,
    e.actual_offshore_wind_generation,
    e.actual_wind_generation,
    e.actual_solar_generation,
    e.actual_wind_solar_generation,
    e.actual_residual_load,
    e.actual_wind_solar_load_ratio,
    e.actual_solar_share_of_wind_solar,
    e.actual_wind_share_of_wind_solar,

    -- forecast values
    e.forecasted_grid_load,
    e.forecasted_onshore_wind_generation,
    e.forecasted_offshore_wind_generation,
    e.forecasted_wind_generation,
    e.forecasted_solar_generation,
    e.forecasted_wind_solar_generation,
    e.forecasted_residual_load,
    e.forecasted_wind_solar_load_ratio,
    e.forecasted_solar_share_of_wind_solar,
    e.forecasted_wind_share_of_wind_solar,

    -- forecast errors
    e.forecast_error_grid_load,
    e.forecast_error_wind_generation,
    e.forecast_error_solar_generation,
    e.forecast_error_residual_load,

    e.abs_forecast_error_grid_load,
    e.abs_forecast_error_wind_generation,
    e.abs_forecast_error_solar_generation,
    e.abs_forecast_error_residual_load

FROM event_ids e;


CREATE OR REPLACE VIEW negative_price_events AS
SELECT
    m.region,
    m.resolution,
    m.event_id,

    MIN(m.observation_timestamp) AS event_start_utc,
    MAX(m.observation_timestamp) AS event_last_hour_utc,
    MAX(m.observation_timestamp) + INTERVAL '1 hour' AS event_end_utc_exclusive,

    MIN(m.local_timestamp) AS event_start_local,
    MAX(m.local_timestamp) AS event_last_hour_local,
    MAX(m.local_timestamp) + INTERVAL '1 hour' AS event_end_local_exclusive,

    COUNT(*) AS duration_hours,

    -- start-based calendar attributes
    (ARRAY_AGG(m.year ORDER BY m.observation_timestamp))[1] AS start_year,
    (ARRAY_AGG(m.month ORDER BY m.observation_timestamp))[1] AS start_month,
    (ARRAY_AGG(m.calendar_week ORDER BY m.observation_timestamp))[1] AS start_calendar_week,
    (ARRAY_AGG(m.season ORDER BY m.observation_timestamp))[1] AS start_season,
    (ARRAY_AGG(m.day_of_week ORDER BY m.observation_timestamp))[1] AS start_day_of_week,
    (ARRAY_AGG(m.local_hour ORDER BY m.observation_timestamp))[1] AS start_local_hour,

    BOOL_OR(m.is_weekend) AS contains_weekend,
    BOOL_OR(m.is_holiday_de_lu) AS contains_holiday,

    -- price metrics
    AVG(m.day_ahead_price) AS avg_day_ahead_price,
    MIN(m.day_ahead_price) AS min_day_ahead_price,
    MAX(m.day_ahead_price) AS max_day_ahead_price,
    SUM(m.day_ahead_price) AS price_integral_eur_per_mwh_hour,

    -- actual system state during event
    AVG(m.actual_grid_load) AS avg_actual_grid_load,
    AVG(m.actual_wind_generation) AS avg_actual_wind_generation,
    AVG(m.actual_solar_generation) AS avg_actual_solar_generation,
    AVG(m.actual_wind_solar_generation) AS avg_actual_wind_solar_generation,
    AVG(m.actual_residual_load) AS avg_actual_residual_load,
    MIN(m.actual_residual_load) AS min_actual_residual_load,
    AVG(m.actual_wind_solar_load_ratio) AS avg_actual_wind_solar_load_ratio,
    AVG(m.actual_solar_share_of_wind_solar) AS avg_actual_solar_share_of_wind_solar,
    AVG(m.actual_wind_share_of_wind_solar) AS avg_actual_wind_share_of_wind_solar,

    -- forecasted system state during event
    AVG(m.forecasted_grid_load) AS avg_forecasted_grid_load,
    AVG(m.forecasted_wind_generation) AS avg_forecasted_wind_generation,
    AVG(m.forecasted_solar_generation) AS avg_forecasted_solar_generation,
    AVG(m.forecasted_wind_solar_generation) AS avg_forecasted_wind_solar_generation,
    AVG(m.forecasted_residual_load) AS avg_forecasted_residual_load,
    MIN(m.forecasted_residual_load) AS min_forecasted_residual_load,
    AVG(m.forecasted_wind_solar_load_ratio) AS avg_forecasted_wind_solar_load_ratio,
    AVG(m.forecasted_solar_share_of_wind_solar) AS avg_forecasted_solar_share_of_wind_solar,
    AVG(m.forecasted_wind_share_of_wind_solar) AS avg_forecasted_wind_share_of_wind_solar,

    -- event-level forecast errors
    AVG(m.forecast_error_grid_load) AS avg_forecast_error_grid_load,
    AVG(m.abs_forecast_error_grid_load) AS mae_forecast_error_grid_load,
    MAX(m.abs_forecast_error_grid_load) AS max_abs_forecast_error_grid_load,

    AVG(m.forecast_error_wind_generation) AS avg_forecast_error_wind_generation,
    AVG(m.abs_forecast_error_wind_generation) AS mae_forecast_error_wind_generation,
    MAX(m.abs_forecast_error_wind_generation) AS max_abs_forecast_error_wind_generation,

    AVG(m.forecast_error_solar_generation) AS avg_forecast_error_solar_generation,
    AVG(m.abs_forecast_error_solar_generation) AS mae_forecast_error_solar_generation,
    MAX(m.abs_forecast_error_solar_generation) AS max_abs_forecast_error_solar_generation,

    AVG(m.forecast_error_residual_load) AS avg_forecast_error_residual_load,
    AVG(m.abs_forecast_error_residual_load) AS mae_forecast_error_residual_load,
    MAX(m.abs_forecast_error_residual_load) AS max_abs_forecast_error_residual_load

FROM negative_price_event_hours m
GROUP BY
    m.region,
    m.resolution,
    m.event_id;


CREATE OR REPLACE VIEW yearly_negative_price_event_summary AS
SELECT
    e.region,
    e.resolution,
    e.start_year AS year,

    COUNT(*) AS number_of_negative_price_events,
    SUM(e.duration_hours) AS negative_price_hours,

    AVG(e.duration_hours) AS avg_event_duration_hours,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e.duration_hours) AS median_event_duration_hours,
    MIN(e.duration_hours) AS min_event_duration_hours,
    MAX(e.duration_hours) AS max_event_duration_hours,

    AVG(e.avg_day_ahead_price) AS avg_event_avg_day_ahead_price,
    MIN(e.min_day_ahead_price) AS yearly_min_day_ahead_price,
    AVG(e.min_day_ahead_price) AS avg_event_min_day_ahead_price,

    AVG(e.avg_forecasted_residual_load) AS avg_event_forecasted_residual_load,
    AVG(e.avg_forecasted_wind_solar_load_ratio) AS avg_event_forecasted_wind_solar_load_ratio,
    AVG(e.avg_forecasted_solar_share_of_wind_solar) AS avg_event_forecasted_solar_share_of_wind_solar,
    AVG(e.avg_forecasted_wind_share_of_wind_solar) AS avg_event_forecasted_wind_share_of_wind_solar,

    AVG(e.avg_forecast_error_residual_load) AS avg_event_forecast_error_residual_load,
    AVG(e.mae_forecast_error_residual_load) AS avg_event_mae_forecast_error_residual_load,
    MAX(e.max_abs_forecast_error_residual_load) AS max_event_abs_forecast_error_residual_load

FROM negative_price_events e
GROUP BY
    e.region,
    e.resolution,
    e.start_year;