"""Helpers de diffusion : un seul endroit qui sait quoi pousser après une mutation."""

from __future__ import annotations

from app.realtime import manager
from app.state import store


async def push_state() -> None:
    await manager.broadcast("state", store.snapshot().model_dump())


async def push_results(activity_id: str | None = None) -> None:
    activity_id = activity_id or store.activity_id
    if not activity_id:
        return
    await manager.broadcast("results", store.results_for(activity_id).model_dump())


async def push_leaderboard() -> None:
    await manager.broadcast(
        "leaderboard",
        [entry.model_dump() for entry in store.leaderboard()],
    )


async def push_all(activity_id: str | None = None) -> None:
    """État + résultats + classement : utilisé après les actions admin."""
    await push_state()
    await push_results(activity_id)
    await push_leaderboard()
