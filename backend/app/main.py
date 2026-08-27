"""Point d'entrée FastAPI.

Lancement local :  uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
(ou simplement `make back`).

En local le backend sert aussi les deux front-ends statiques, ce qui évite de
lancer trois serveurs pendant les répétitions :
  http://localhost:8000/deck  -> la présentation (frontend_main)
  http://localhost:8000/app   -> l'app participant (frontend_user)
En production, Netlify sert les deux front-ends et ces montages ne servent plus.
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.realtime import manager
from app.routers import admin, public, qr
from app.state import store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s | %(message)s")
logger = logging.getLogger("final_presentation")

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.reset_on_start:
        store.reset()
    logger.info("Deck presentateur    -> http://localhost:%d/deck", settings.port)
    logger.info("App participant      -> http://localhost:%d/app", settings.port)
    logger.info("Depuis un telephone  -> %s", settings.app_url)
    logger.info("API                  -> %s", settings.api_url)
    yield


app = FastAPI(
    title="Final Presentation API",
    description="Backend temps reel de la presentation finale de stage (sondages + mini-jeux).",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(public.router)
app.include_router(admin.router)
app.include_router(qr.router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Canal temps réel. `?role=deck` ou `?role=phone` pour cibler les diffusions."""
    role = websocket.query_params.get("role", "unknown")
    role = role if role in ("deck", "phone") else "unknown"
    await manager.connect(websocket, role)  # type: ignore[arg-type]

    # Premier message : l'état courant, pour que le client s'aligne immédiatement.
    await manager.send(websocket, "state", store.snapshot().model_dump())
    if store.activity_id:
        await manager.send(websocket, "results", store.results_for(store.activity_id).model_dump())

    try:
        while True:
            # On ne consomme rien du client (hors "ping"), mais il faut lire pour
            # detecter la deconnexion.
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001 - on veut juste nettoyer proprement
        logger.debug("WS erreur : %s", exc)
    finally:
        await manager.disconnect(websocket)


@app.get("/")
async def root() -> RedirectResponse:
    return RedirectResponse("/deck")


# --------------------------------------------------------------------------- #
# Front-ends statiques (confort local uniquement)
# --------------------------------------------------------------------------- #
with contextlib.suppress(RuntimeError):
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

if settings.frontend_main_dir.exists():
    app.mount(
        "/deck",
        StaticFiles(directory=settings.frontend_main_dir, html=True),
        name="deck",
    )

if settings.frontend_user_dir.exists():
    app.mount(
        "/app",
        StaticFiles(directory=settings.frontend_user_dir, html=True),
        name="app",
    )
