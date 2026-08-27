"""Routes publiques : consommées par le deck ET par les téléphones."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.data.content import (
    ACTIVITIES,
    ACTIVITIES_BY_ID,
    AVATAR_EMOJIS,
    SESSION_TITLE,
    SLIDES,
)
from app.events import push_leaderboard, push_results, push_state
from app.models import (
    ActivityResults,
    AnswerRequest,
    AnswerResponse,
    JoinRequest,
    JoinResponse,
    LeaderboardEntry,
    SessionState,
)
from app.realtime import manager
from app.state import store

router = APIRouter(prefix="/api", tags=["public"])


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "participants": len(store.participants),
        "sockets": manager.count_by_role(),
    }


@router.get("/content")
async def get_content() -> dict:
    """Manifeste complet du contenu (sans les bonnes réponses du quiz)."""
    return {
        "session_title": SESSION_TITLE,
        "slides": SLIDES,
        "activities": [a.public(reveal=False) for a in ACTIVITIES],
        "avatar_emojis": AVATAR_EMOJIS,
    }


@router.get("/session", response_model=SessionState)
async def get_session() -> SessionState:
    return store.snapshot()


@router.post("/participants/join", response_model=JoinResponse)
async def join(payload: JoinRequest) -> JoinResponse:
    participant = store.join(payload.nickname, payload.emoji)
    await manager.broadcast(
        "participant_joined",
        {
            "nickname": participant.nickname,
            "emoji": participant.emoji,
            "total": len(store.participants),
        },
    )
    await push_state()
    return JoinResponse(participant=participant, session=store.snapshot())


@router.get("/activities/{activity_id}")
async def get_activity(activity_id: str) -> dict:
    activity = ACTIVITIES_BY_ID.get(activity_id)
    if activity is None:
        raise HTTPException(404, f"Unknown activity: {activity_id}")
    reveal = store.activity_id == activity_id and store.status == "revealed"
    return activity.public(reveal=reveal)


@router.post(
    "/activities/{activity_id}/questions/{question_id}/answer",
    response_model=AnswerResponse,
)
async def answer(activity_id: str, question_id: str, payload: AnswerRequest) -> AnswerResponse:
    activity = ACTIVITIES_BY_ID.get(activity_id)
    if activity is None:
        raise HTTPException(404, f"Unknown activity: {activity_id}")
    question = next((q for q in activity.questions if q.id == question_id), None)
    if question is None:
        raise HTTPException(404, f"Unknown question: {question_id}")

    participant = store.participants.get(payload.participant_id)
    if participant is None:
        raise HTTPException(401, "Unknown participant, please rejoin the session")

    if store.status != "open" or store.activity_id != activity_id:
        return AnswerResponse(
            accepted=False,
            reason="Voting is closed for this question",
            total_score=participant.score,
        )
    if store.has_answered(activity_id, question_id, payload.participant_id):
        return AnswerResponse(
            accepted=False,
            reason="You already answered this question",
            total_score=participant.score,
        )

    if question.kind == "words":
        words = [w.strip() for w in payload.words if w.strip()]
        if not (question.min_words <= len(words) <= question.max_words):
            return AnswerResponse(
                accepted=False,
                reason=f"Submit between {question.min_words} and {question.max_words} words",
                total_score=participant.score,
            )
    else:
        words = []

    awarded, elapsed_ms = store.record_answer(
        activity_id,
        question_id,
        payload.participant_id,
        payload.option_ids,
        payload.elapsed_ms,
        words=words,
    )

    await push_state()
    await push_results(activity_id)
    if activity.kind == "quiz":
        await push_leaderboard()

    return AnswerResponse(
        accepted=True,
        awarded_points=awarded,
        total_score=participant.score,
        elapsed_ms=elapsed_ms,
    )


@router.get("/results/{activity_id}", response_model=ActivityResults)
async def results(activity_id: str) -> ActivityResults:
    if activity_id not in ACTIVITIES_BY_ID:
        raise HTTPException(404, f"Unknown activity: {activity_id}")
    return store.results_for(activity_id)


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def leaderboard(limit: int = 10) -> list[LeaderboardEntry]:
    return store.leaderboard(limit=limit)
