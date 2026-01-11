import os
from dataclasses import dataclass

@dataclass
class MLServiceConfig():
    auth_token: str | None = os.getenv("MLPS_AUTH_TOKEN")
