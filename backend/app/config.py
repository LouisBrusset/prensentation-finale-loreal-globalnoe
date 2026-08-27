"""Configuration centralisee, lue depuis l'environnement / le fichier .env."""

from __future__ import annotations

import socket
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .../presentation_finale_loreal
ROOT_DIR = Path(__file__).resolve().parents[2]


@lru_cache
def detect_lan_ip() -> str:
    """IP de la machine sur le réseau local.

    C'est elle que les téléphones doivent viser : `localhost` ne veut rien dire
    depuis un autre appareil. Aucun paquet n'est réellement envoyé — on ouvre un
    socket UDP pour laisser l'OS choisir l'interface sortante.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


class Settings(BaseSettings):
    """Toutes les variables sont prefixees par `FP_` (cf. .env.example)."""

    model_config = SettingsConfigDict(
        env_prefix="FP_",
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8010

    # Laisser vide en local : les URLs sont alors construites depuis l'IP LAN
    # detectee, ce qui est la seule chose qu'un telephone puisse joindre.
    # A renseigner en production (URL Netlify / Render).
    public_api_url: str = ""
    public_app_url: str = ""

    cors_origins: str = "*"

    admin_token: str = "loreal2026"
    reset_on_start: bool = True

    # Chemins utiles
    root_dir: Path = ROOT_DIR
    static_dir: Path = ROOT_DIR / "static"
    frontend_main_dir: Path = ROOT_DIR / "frontend_main"
    frontend_user_dir: Path = ROOT_DIR / "frontend_user"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def api_url(self) -> str:
        """URL publique de l'API : celle configuree, sinon l'IP LAN."""
        return self.public_api_url or f"http://{detect_lan_ip()}:{self.port}"

    @property
    def app_url(self) -> str:
        """URL publique de l'app participant — c'est elle qui finit dans le QR code.

        En local, le backend sert lui-meme le front sur `/app` : on encode donc
        `http://<ip-lan>:<port>/app`, joignable depuis un telephone du meme wifi.
        En production, `FP_PUBLIC_APP_URL` pointe vers le site Netlify.
        """
        return self.public_app_url or f"http://{detect_lan_ip()}:{self.port}/app"


@lru_cache
def get_settings() -> Settings:
    return Settings()
