import httpx
from dataclasses import dataclass

BASE_URL = "https://www.smard.de/app/chart_data"
TIMEOUT_SECONDS = 20.0


@dataclass(frozen=True)
class SmardConfig:
    smard_filter_id: str = "410"
    region: str = "DE"
    resolution: str = "hour"


def build_index_url(config: SmardConfig) -> str:
    return f"{BASE_URL}/{config.smard_filter_id}/{config.region}/index_{config.resolution}.json"


def build_payload_url(config: SmardConfig, timestamp: int) -> str:
    return f"{BASE_URL}/{config.smard_filter_id}/{config.region}/{config.smard_filter_id}_{config.region}_{config.resolution}_{timestamp}.json"


def get_timestamps(config: SmardConfig) -> list[int]:
    index_url = build_index_url(config)
    with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
        response = client.get(index_url)
        response.raise_for_status()
        index_data = response.json()
    return index_data["timestamps"]


def get_payload(config: SmardConfig, timestamp: int) -> dict:
    payload_url = build_payload_url(config, timestamp)
    with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
        response = client.get(payload_url)
        response.raise_for_status()
        payload = response.json()
    return payload
