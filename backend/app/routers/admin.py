"""Routes de pilotage, appelées par le deck du présentateur.

Protection volontairement minimaliste (un token partagé dans l'en-tête
`X-Admin-Token`) : la seule chose à empêcher, c'est qu'un participant malin
ferme un sondage depuis son téléphone.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from app.config import get_settings
from app.data.content import ACTIVITIES_BY_ID, SLIDES
from app.events import push_all, push_state
from app.models import OpenActivityRequest, SeedRequest, SessionState, SlideRequest
from app.state import store

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def require_admin(x_admin_token: str = Header(default="")) -> None:
    if x_admin_token != get_settings().admin_token:
        raise HTTPException(403, "Token admin invalide")


@router.post("/activity/open", response_model=SessionState, dependencies=[Depends(require_admin)])
async def open_activity(payload: OpenActivityRequest) -> SessionState:
    if payload.activity_id not in ACTIVITIES_BY_ID:
        raise HTTPException(404, f"Activite inconnue : {payload.activity_id}")
    store.open_activity(payload.activity_id, payload.question_index)
    await push_all(payload.activity_id)
    return store.snapshot()


@router.post("/activity/close", response_model=SessionState, dependencies=[Depends(require_admin)])
async def close_activity() -> SessionState:
    store.close_activity()
    await push_all()
    return store.snapshot()


@router.post("/activity/reveal", response_model=SessionState, dependencies=[Depends(require_admin)])
async def reveal() -> SessionState:
    store.reveal()
    await push_all()
    return store.snapshot()


@router.post("/activity/next", response_model=SessionState, dependencies=[Depends(require_admin)])
async def next_question() -> SessionState:
    """Passe à la question suivante ; repasse en idle après la dernière.

    Sans effet — et sans erreur — s'il n'y a plus rien d'ouvert. Appuyer deux
    fois sur `N` à la fin d'une activité est un geste normal en présentation :
    ça ne doit pas remplir les logs de 409.
    """
    activity = store.current_activity()
    if activity is None:
        return store.snapshot()
    if store.question_index + 1 < len(activity.questions):
        store.open_activity(activity.id, store.question_index + 1)
    else:
        store.idle()
    await push_all(activity.id)
    return store.snapshot()


@router.post("/activity/idle", response_model=SessionState, dependencies=[Depends(require_admin)])
async def go_idle() -> SessionState:
    store.idle()
    await push_state()
    return store.snapshot()


@router.post("/slide", response_model=SessionState, dependencies=[Depends(require_admin)])
async def set_slide(payload: SlideRequest) -> SessionState:
    store.set_slide(payload.slide_index)
    await push_state()
    return store.snapshot()


@router.post("/seed", dependencies=[Depends(require_admin)])
async def seed(payload: SeedRequest) -> dict:
    """Injecte de faux participants + réponses (répétitions, captures, démos)."""
    created = store.seed_fake(payload.participants, payload.answer_everything)
    await push_all()
    return {"created": created, "participants": len(store.participants)}


@router.post("/reset", dependencies=[Depends(require_admin)])
async def reset() -> dict:
    store.reset()
    await push_all()
    return {"status": "reset", "slides": len(SLIDES)}
