"""Diffusion temps réel vers le deck et les téléphones (WebSocket).

Le deck (frontend_main) et chaque téléphone (frontend_user) ouvrent une
WebSocket sur /ws. Le serveur pousse un événement à chaque changement d'état.
Les deux front-ends savent aussi retomber sur du polling HTTP si la WebSocket
ne s'établit pas (proxy d'entreprise, wifi capricieux) — voir docs/ARCHITECTURE.md.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Any, Literal

from fastapi import WebSocket

logger = logging.getLogger(__name__)

Role = Literal["deck", "phone", "unknown"]

EventType = Literal[
    "state",  # état de session (slide, activité ouverte, compteurs)
    "results",  # résultats agrégés d'une activité
    "leaderboard",  # classement du mini-jeu
    "participant_joined",
    "reset",
]


class ConnectionManager:
    """Garde la liste des sockets ouvertes et sait diffuser un message à tous."""

    def __init__(self) -> None:
        self._connections: dict[WebSocket, Role] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, role: Role = "unknown") -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[websocket] = role
        logger.info("WS connectee (role=%s, total=%d)", role, len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.pop(websocket, None)
        logger.info("WS fermee (total=%d)", len(self._connections))

    async def send(self, websocket: WebSocket, event: EventType, payload: Any) -> None:
        with contextlib.suppress(Exception):
            await websocket.send_text(json.dumps({"type": event, "payload": payload}))

    async def broadcast(self, event: EventType, payload: Any, role: Role | None = None) -> None:
        """Diffuse à tout le monde, ou seulement aux sockets d'un rôle donné."""
        message = json.dumps({"type": event, "payload": payload})
        async with self._lock:
            targets = [ws for ws, r in self._connections.items() if role is None or r == role]

        dead: list[WebSocket] = []
        for websocket in targets:
            try:
                await websocket.send_text(message)
            except Exception:  # socket morte : on nettoie
                dead.append(websocket)

        if dead:
            async with self._lock:
                for websocket in dead:
                    self._connections.pop(websocket, None)

    @property
    def count(self) -> int:
        return len(self._connections)

    def count_by_role(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for role in self._connections.values():
            counts[role] = counts.get(role, 0) + 1
        return counts


manager = ConnectionManager()
