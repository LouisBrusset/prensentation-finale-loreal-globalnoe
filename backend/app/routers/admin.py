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
from app.models import (
    OpenActivityRequest,
    ResumeRequest,
    SeedRequest,
    SessionState,
    SlideRequest,
)
from app.state import store

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def require_admin(x_admin_token: str = Header(default="")) -> None:
    if x_admin_token != get_settings().admin_token:
        raise HTTPException(403, "Invalid admin token")


@router.post("/activity/open", response_model=SessionState, dependencies=[Depends(require_admin)])
async def open_activity(payload: OpenActivityRequest) -> SessionState:
    if payload.activity_id not in ACTIVITIES_BY_ID:
        raise HTTPException(404, f"Unknown activity: {payload.activity_id}")
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
    """Passe à la question suivante ; reste sur la dernière une fois au bout.

    Sans effet — et sans erreur — s'il n'y a plus rien d'ouvert. Appuyer deux
    fois sur `N` en fin d'activité est un geste normal en présentation : ça ne
    doit pas remplir les logs de 409. On ne repasse plus en idle au bout, sinon
    le bouton « précédent » n'aurait plus rien à quoi se raccrocher ; c'est le
    changement de slide qui remet la session au repos.
    """
    activity = store.current_activity()
    if activity is None:
        return store.snapshot()
    store.goto(activity.id, store.question_index + 1)
    await push_all(activity.id)
    return store.snapshot()


@router.post("/activity/prev", response_model=SessionState, dependencies=[Depends(require_admin)])
async def previous_question() -> SessionState:
    """Revient sur la question précédente pour en réafficher les résultats.

    Sans effet sur la première question — pas de bouclage, ce serait déroutant
    en pleine présentation.
    """
    activity = store.current_activity()
    if activity is None:
        return store.snapshot()
    store.goto(activity.id, store.question_index - 1)
    await push_all(activity.id)
    return store.snapshot()


@router.post("/activity/goto", response_model=SessionState, dependencies=[Depends(require_admin)])
async def goto_question(payload: OpenActivityRequest) -> SessionState:
    """Saute directement sur n'importe quelle question d'une activité."""
    if payload.activity_id not in ACTIVITIES_BY_ID:
        raise HTTPException(404, f"Unknown activity: {payload.activity_id}")
    store.goto(payload.activity_id, payload.question_index)
    await push_all(payload.activity_id)
    return store.snapshot()


@router.post("/activity/resume", response_model=SessionState, dependencies=[Depends(require_admin)])
async def resume_activity(payload: ResumeRequest) -> SessionState:
    """Reprend une activité là où elle en était.

    Appelé par le deck quand il revient sur une slide de sondage : sans ça, on
    repartait de la question 1 alors que la salle en était à la 3ᵉ.
    """
    if payload.activity_id not in ACTIVITIES_BY_ID:
        raise HTTPException(404, f"Unknown activity: {payload.activity_id}")
    store.resume(payload.activity_id)
    await push_all(payload.activity_id)
    return store.snapshot()


@router.post("/activity/reset-question", dependencies=[Depends(require_admin)])
async def reset_question() -> dict:
    """Efface les réponses de la SEULE question courante et rouvre les votes.

    Les points éventuellement accordés sont repris. Les téléphones qui avaient
    déjà répondu peuvent voter de nouveau : le `question_token` change, ce qui
    leur fait oublier leur réponse précédente.
    """
    activity = store.current_activity()
    question = store.current_question()
    if activity is None or question is None:
        raise HTTPException(409, "No question currently open")

    cleared = store.reset_question(activity.id, question.id)
    await push_all(activity.id)
    return {
        "cleared": cleared,
        "activity_id": activity.id,
        "question_id": question.id,
        "session": store.snapshot().model_dump(),
    }


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
