"""Génère le QR code de la session en PNG dans static/qr/.

Par défaut il encode exactement la même URL que celle affichée sur la slide 2 du
deck, c'est-à-dire l'app participant vue depuis le réseau local :

    uv run python scripts/gen_qr.py
    -> http://192.168.1.8:8010/app

Pour un QR de production (app déployée sur Netlify) :

    uv run python scripts/gen_qr.py --url https://ma-presentation.netlify.app
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.config import detect_lan_ip, get_settings  # noqa: E402
from app.qrcodes import save_qr_png  # noqa: E402


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Genere le QR code de la session")
    parser.add_argument(
        "--url",
        default=None,
        help="URL a encoder. Par defaut : l'app participant sur l'IP LAN detectee.",
    )
    parser.add_argument("--out", default="static/qr/join.png", help="Fichier PNG de sortie")
    parser.add_argument("--box-size", type=int, default=12, help="Taille des modules du QR")
    args = parser.parse_args()

    url = args.url or settings.app_url
    destination = save_qr_png(url, Path(args.out), box_size=args.box_size)

    print(f"QR code -> {destination}")
    print(f"encode  : {url}")
    print(f"IP LAN detectee : {detect_lan_ip()}")
    if "localhost" in url or "127.0.0.1" in url:
        print("\nATTENTION : cette URL n'est joignable que depuis cette machine.")
        print("Un telephone qui scanne ce QR n'arrivera nulle part.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
