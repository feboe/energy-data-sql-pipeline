import os
from pathlib import Path
from dataclasses import dataclass


def load_env_file(env_path: Path = Path(".env")) -> None:
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()

        if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
            continue

        key, value = stripped_line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "energy_data"
    user: str = "user"
    password: str = "password"


def load_database_config() -> DatabaseConfig:
    load_env_file()
    return DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "energy_data"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
    )
