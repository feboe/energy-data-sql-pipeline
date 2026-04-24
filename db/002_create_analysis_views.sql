CREATE OR REPLACE VIEW hourly_market_features AS
SELECT
    observation_timestamp,
    MAX(value) FILTER (WHERE series_name = 'day_ahead_price') AS day_ahead_price,
    MAX(value) FILTER (WHERE series_name = 'lignite_generation') AS lignite_generation,
    MAX(value) FILTER (WHERE series_name = 'nuclear_generation') AS nuclear_generation,
    MAX(value) FILTER (WHERE series_name = 'offshore_wind_generation') AS offshore_wind_generation,
    MAX(value) FILTER (WHERE series_name = 'hydropower_generation') AS hydropower_generation,
    MAX(value) FILTER (WHERE series_name = 'other_conventional_generation') AS other_conventional_generation,
    MAX(value) FILTER (WHERE series_name = 'other_renewable_generation') AS other_renewable_generation,
    MAX(value) FILTER (WHERE series_name = 'biomass_generation') AS biomass_generation,
    MAX(value) FILTER (WHERE series_name = 'onshore_wind_generation') AS onshore_wind_generation,
    MAX(value) FILTER (WHERE series_name = 'photovoltaics_generation') AS photovoltaics_generation,
    MAX(value) FILTER (WHERE series_name = 'hard_coal_generation') AS hard_coal_generation,
    MAX(value) FILTER (WHERE series_name = 'natural_gas_generation') AS natural_gas_generation,
    MAX(value) FILTER (WHERE series_name = 'pumped_storage_generation') AS pumped_storage_generation,
    MAX(value) FILTER (WHERE series_name = 'grid_load') AS grid_load,
    MAX(value) FILTER (WHERE series_name = 'residual_load') AS residual_load,
    MAX(value) FILTER (WHERE series_name = 'pumped_storage_consumption') AS pumped_storage_consumption,
    MAX(value) FILTER (WHERE series_name = 'forecasted_offshore_wind_generation') AS forecasted_offshore_wind_generation,
    MAX(value) FILTER (WHERE series_name = 'forecasted_onshore_wind_generation') AS forecasted_onshore_wind_generation,
    MAX(value) FILTER (WHERE series_name = 'forecasted_photovoltaics_generation') AS forecasted_photovoltaics_generation,
    MAX(value) FILTER (WHERE series_name = 'forecasted_other_generation') AS forecasted_other_generation,
    MAX(value) FILTER (WHERE series_name = 'forecasted_wind_and_photovoltaics_generation') AS forecasted_wind_and_photovoltaics_generation,
    MAX(value) FILTER (WHERE series_name = 'forecasted_total_generation') AS forecasted_total_generation,
    MAX(value) FILTER (WHERE series_name = 'forecasted_grid_load') AS forecasted_grid_load
FROM measurements
WHERE resolution = 'hour'
GROUP BY observation_timestamp;
