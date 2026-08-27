"""Génération des QR codes qui envoient les participants vers frontend_user."""

from __future__ import annotations

import io
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_H
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer


def build_qr_png(
    data: str,
    box_size: int = 12,
    border: int = 2,
    rounded: bool = True,
) -> bytes:
    """Renvoie le PNG (bytes) du QR code encodant `data`.

    Correction d'erreur haute : le QR reste lisible même projeté de travers
    sur un écran de salle de réunion.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    if rounded:
        image = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            fill_color="black",
            back_color="white",
        )
    else:
        image = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def save_qr_png(data: str, destination: Path, **kwargs) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(build_qr_png(data, **kwargs))
    return destination
