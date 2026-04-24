from dataclasses import dataclass
from src.smard_client import SmardConfig


@dataclass(frozen=True)
class SmardSeries:
    series_name: str
    display_name: str
    category: str
    config: SmardConfig
    unit: str = "MWh"


DEFAULT_REGION = "DE"
DEFAULT_RESOLUTION = "hour"


LIGNITE_GENERATION = SmardSeries(
    series_name="lignite_generation",
    display_name="Lignite generation",
    category="actual_generation",
    config=SmardConfig(
        smard_filter_id="1223",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

NUCLEAR_GENERATION = SmardSeries(
    series_name="nuclear_generation",
    display_name="Nuclear generation",
    category="actual_generation",
    config=SmardConfig(
        smard_filter_id="1224",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

OFFSHORE_WIND_GENERATION = SmardSeries(
    series_name="offshore_wind_generation",
    display_name="Offshore wind generation",
    category="actual_generation",
    config=SmardConfig(
        smard_filter_id="1225",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

HYDROPOWER_GENERATION = SmardSeries(
    series_name="hydropower_generation",
    display_name="Hydropower generation",
    category="actual_generation",
    config=SmardConfig(
        smard_filter_id="1226",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

OTHER_CONVENTIONAL_GENERATION = SmardSeries(
    series_name="other_conventional_generation",
    display_name="Other conventional generation",
    category="actual_generation",
    config=SmardConfig(
        smard_filter_id="1227",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

OTHER_RENEWABLE_GENERATION = SmardSeries(
    series_name="other_renewable_generation",
    display_name="Other renewable generation",
    category="actual_generation",
    config=SmardConfig(
        smard_filter_id="1228",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

BIOMASS_GENERATION = SmardSeries(
    series_name="biomass_generation",
    display_name="Biomass generation",
    category="actual_generation",
    config=SmardConfig(
        smard_filter_id="4066",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

ONSHORE_WIND_GENERATION = SmardSeries(
    series_name="onshore_wind_generation",
    display_name="Onshore wind generation",
    category="actual_generation",
    config=SmardConfig(
        smard_filter_id="4067",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

PHOTOVOLTAICS_GENERATION = SmardSeries(
    series_name="photovoltaics_generation",
    display_name="Photovoltaics generation",
    category="actual_generation",
    config=SmardConfig(
        smard_filter_id="4068",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

HARD_COAL_GENERATION = SmardSeries(
    series_name="hard_coal_generation",
    display_name="Hard coal generation",
    category="actual_generation",
    config=SmardConfig(
        smard_filter_id="4069",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

NATURAL_GAS_GENERATION = SmardSeries(
    series_name="natural_gas_generation",
    display_name="Natural gas generation",
    category="actual_generation",
    config=SmardConfig(
        smard_filter_id="4071",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

PUMPED_STORAGE_GENERATION = SmardSeries(
    series_name="pumped_storage_generation",
    display_name="Pumped storage generation",
    category="actual_generation",
    config=SmardConfig(
        smard_filter_id="4070",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

GRID_LOAD = SmardSeries(
    series_name="grid_load",
    display_name="Grid load",
    category="actual_consumption",
    config=SmardConfig(
        smard_filter_id="410",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

RESIDUAL_LOAD = SmardSeries(
    series_name="residual_load",
    display_name="Residual load",
    category="actual_consumption",
    config=SmardConfig(
        smard_filter_id="4359",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

PUMPED_STORAGE_CONSUMPTION = SmardSeries(
    series_name="pumped_storage_consumption",
    display_name="Pumped storage consumption",
    category="actual_consumption",
    config=SmardConfig(
        smard_filter_id="4387",
        region=DEFAULT_REGION,
        resolution=DEFAULT_RESOLUTION,
    ),
)

SMARD_SERIES = (
    LIGNITE_GENERATION,
    NUCLEAR_GENERATION,
    OFFSHORE_WIND_GENERATION,
    HYDROPOWER_GENERATION,
    OTHER_CONVENTIONAL_GENERATION,
    OTHER_RENEWABLE_GENERATION,
    BIOMASS_GENERATION,
    ONSHORE_WIND_GENERATION,
    PHOTOVOLTAICS_GENERATION,
    HARD_COAL_GENERATION,
    NATURAL_GAS_GENERATION,
    PUMPED_STORAGE_GENERATION,
    GRID_LOAD,
    RESIDUAL_LOAD,
    PUMPED_STORAGE_CONSUMPTION,
)

SMARD_SERIES_CATALOG = {series.series_name: series for series in SMARD_SERIES}
