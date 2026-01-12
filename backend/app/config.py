import os
import secrets
from typing import Dict

import structlog

LOGGER = structlog.get_logger()

class MLServiceConfig():
    def __init__(self, dotenv: bool = False, dotenv_path: str = ".env") -> None:
        self.dotenv: bool = dotenv
        self.dotenv_path = dotenv_path
        self.auth_user: str
        self.auth_password: str
        self.session_secret: str
        self.db_path: str

        if self.dotenv:
            if os.path.exists(dotenv_path):
                self._read_from_dotenv()
            else:
                LOGGER.warning("Dotenv file does not exist. Switching to ENV", dotenv_path=self.dotenv_path)
                self._read_from_env()
        else:
            self._read_from_env()
        
        LOGGER.info("Config loaded", auth_user=bool(self.auth_user), auth_password=bool(self.auth_password))

        if not self._is_valid_credentials():
            raise RuntimeError("Auth credentials are not configured")

    def _is_valid_credentials(self) -> bool:
        is_auth_user = True if self.auth_user else False
        is_auth_password = True if self.auth_password else False
        is_session_secret = True if self.session_secret else False
        is_db = True if self.db_path else False
        return is_auth_user and is_auth_password and is_session_secret and is_db

    def _read_from_env(self) -> None:
            self.auth_user = os.getenv("MLPS_AUTH_USER", "")
            self.auth_password = os.getenv("MLPS_AUTH_PASSWORD", "")
            self.session_secret = os.getenv("MLPS_AUTH_SESSION_SECRET", "")
            self.db_path = os.getenv("MLPS_DB_PATH", "")

    def _read_from_dotenv(self) -> None:
        with open(self.dotenv_path, "r") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                if secrets.compare_digest(key, "MLPS_AUTH_USER"):
                    self.auth_user = value
                if secrets.compare_digest(key, "MLPS_AUTH_PASSWORD"):
                    self.auth_password = value
                if secrets.compare_digest(key, "MLPS_AUTH_SESSION_SECRET"):
                    self.session_secret = value
                if secrets.compare_digest(key, "MLPS_DB_PATH"):
                    self.db_path = value


if __name__ == "__main__":
    config = MLServiceConfig(dotenv=True)
    print(f"User: {config.auth_user}\nPassword: {config.auth_password}")
