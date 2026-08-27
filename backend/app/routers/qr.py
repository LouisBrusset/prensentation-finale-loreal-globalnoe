"""Route QR code : l'image affichée sur la slide "Rejoignez la session"."""

from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.config import get_settings
from app.qrcodes import build_qr_png

router = APIRouter(prefix="/api", tags=["qr"])


@router.get("/qr.png")
async def qr_png(
    url: str | None = Query(default=None, description="URL a encoder (defaut : l'app participant)"),
    box_size: int = Query(default=12, ge=4, le=40),
) -> Response:
    target = url or get_settings().app_url
    png = build_qr_png(target, box_size=box_size)
    return Response(
        content=png,
        media_type="image/png",
        headers={"Cache-Control": "no-store", "X-QR-Target": target},
    )


@router.get("/join-url")
async def join_url() -> dict:
    """Le deck affiche cette URL en clair sous le QR code (plan B si le scan rate)."""
    settings = get_settings()
    return {"app_url": settings.app_url, "api_url": settings.api_url}
