from pathlib import Path

from pydantic_settings import BaseSettings

CONFIG_DIR = Path(__file__).parent.parent / "config"


class Settings(BaseSettings):
    whoop_access_token: str
    whoop_refresh_token: str = ""
    whoop_client_id: str = ""
    whoop_client_secret: str = ""
    whoop_api_base_url: str = "https://api.prod.whoop.com/developer"
    whoop_token_url: str = "https://api.prod.whoop.com/oauth/oauth2/token"

    model_config = {"env_file": CONFIG_DIR / ".env", "env_file_encoding": "utf-8"}


settings = Settings()
