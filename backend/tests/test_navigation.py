"""Navigation libre dans une activité, et réinitialisation d'une question.

Deux besoins de présentation :
  - revenir sur n'importe quelle question pour en réafficher les résultats ;
  - reprendre un sondage laissé en plan, sans que ceux qui ont déjà voté
    restent bloqués sur « trop tard ».
"""

from __future__ import annotations

import pytest
from app.config import get_settings
from app.main import app
from app.state import store
from fastapi.testclient import TestClient

ADMIN = {"X-Admin-Token": get_settings().admin_token}


@pytest.fixture()
def client() -> TestClient:
    store.reset()
    with TestClient(app) as c:
        yield c
    store.reset()


def _join(client: TestClient, nickname: str) -> dict:
    return client.post("/api/participants/join", json={"nickname": nickname}).json()[
        "participant"
    ]


# --------------------------------------------------------------------------- #
# Aller-retour dans une activite
# --------------------------------------------------------------------------- #
def test_prev_goes_back_and_shows_results_without_reopening(client: TestClient) -> None:
    me = _join(client, "Louis")

    client.post(
        "/api/admin/activity/open", json={"activity_id": "poll-prompt-warmup"}, headers=ADMIN
    )
    client.post(
        "/api/activities/poll-prompt-warmup/questions/pw1/answer",
        json={"participant_id": me["id"], "option_ids": ["pw1a"]},
    )
    client.post("/api/admin/activity/next", headers=ADMIN)
    assert client.get("/api/session").json()["question_index"] == 1

    back = client.post("/api/admin/activity/prev", headers=ADMIN).json()
    assert back["question_index"] == 0
    # La question avait deja des reponses : on les reaffiche, on ne rouvre pas
    # les votes dans le dos de la salle.
    assert back["status"] == "closed"

    results = client.get("/api/results/poll-prompt-warmup").json()
    assert results["questions"][0]["total_answers"] == 1


def test_prev_is_a_no_op_on_the_first_question(client: TestClient) -> None:
    client.post(
        "/api/admin/activity/open", json={"activity_id": "poll-prompt-warmup"}, headers=ADMIN
    )
    state = client.post("/api/admin/activity/prev", headers=ADMIN).json()
    assert state["question_index"] == 0


def test_navigation_reaches_every_question_both_ways(client: TestClient) -> None:
    client.post("/api/admin/activity/open", json={"activity_id": "quiz-companions"}, headers=ADMIN)

    seen_forward = [client.get("/api/session").json()["question_index"]]
    for _ in range(5):  # plus que le nombre de questions : ca doit buter, pas boucler
        seen_forward.append(client.post("/api/admin/activity/next", headers=ADMIN).json()[
            "question_index"
        ])
    assert seen_forward == [0, 1, 2, 3, 3, 3]

    seen_back = []
    for _ in range(5):
        seen_back.append(client.post("/api/admin/activity/prev", headers=ADMIN).json()[
            "question_index"
        ])
    assert seen_back == [2, 1, 0, 0, 0]


def test_goto_jumps_to_any_question(client: TestClient) -> None:
    client.post("/api/admin/activity/open", json={"activity_id": "quiz-companions"}, headers=ADMIN)
    state = client.post(
        "/api/admin/activity/goto",
        json={"activity_id": "quiz-companions", "question_index": 3},
        headers=ADMIN,
    ).json()
    assert state["question_index"] == 3
    assert state["status"] == "open", "une question vierge ouvre les votes"


def test_resume_returns_to_where_the_room_was(client: TestClient) -> None:
    """Quitter la slide puis y revenir ne doit pas relancer le sondage a zero."""
    client.post(
        "/api/admin/activity/open", json={"activity_id": "poll-prompt-warmup"}, headers=ADMIN
    )
    client.post("/api/admin/activity/next", headers=ADMIN)
    client.post("/api/admin/activity/next", headers=ADMIN)
    assert client.get("/api/session").json()["question_index"] == 2

    # Le deck passe sur une slide sans activite...
    client.post("/api/admin/activity/idle", headers=ADMIN)
    assert client.get("/api/session").json()["activity_id"] is None

    # ... puis revient.
    state = client.post(
        "/api/admin/activity/resume", json={"activity_id": "poll-prompt-warmup"}, headers=ADMIN
    ).json()
    assert state["activity_id"] == "poll-prompt-warmup"
    assert state["question_index"] == 2, "on reprend a la 3e question, pas a la 1re"


# --------------------------------------------------------------------------- #
# Reinitialisation d'une seule question
# --------------------------------------------------------------------------- #
def test_reset_question_clears_only_that_question(client: TestClient) -> None:
    me = _join(client, "Louis")

    client.post(
        "/api/admin/activity/open", json={"activity_id": "poll-prompt-warmup"}, headers=ADMIN
    )
    client.post(
        "/api/activities/poll-prompt-warmup/questions/pw1/answer",
        json={"participant_id": me["id"], "option_ids": ["pw1a"]},
    )
    client.post("/api/admin/activity/next", headers=ADMIN)
    client.post(
        "/api/activities/poll-prompt-warmup/questions/pw2/answer",
        json={"participant_id": me["id"], "option_ids": ["pw2a"]},
    )

    client.post("/api/admin/activity/prev", headers=ADMIN)
    body = client.post("/api/admin/activity/reset-question", headers=ADMIN).json()
    assert body["cleared"] == 1
    assert body["question_id"] == "pw1"
    assert body["session"]["status"] == "open", "les votes doivent se rouvrir"

    results = client.get("/api/results/poll-prompt-warmup").json()
    assert results["questions"][0]["total_answers"] == 0, "question 1 effacee"
    assert results["questions"][1]["total_answers"] == 1, "question 2 intacte"


def test_reset_question_lets_the_same_person_vote_again(client: TestClient) -> None:
    me = _join(client, "Louis")
    client.post(
        "/api/admin/activity/open", json={"activity_id": "poll-prompt-warmup"}, headers=ADMIN
    )

    payload = {"participant_id": me["id"], "option_ids": ["pw1a"]}
    url = "/api/activities/poll-prompt-warmup/questions/pw1/answer"

    assert client.post(url, json=payload).json()["accepted"] is True
    assert client.post(url, json=payload).json()["accepted"] is False, "pas deux fois"

    client.post("/api/admin/activity/reset-question", headers=ADMIN)

    assert client.post(url, json=payload).json()["accepted"] is True, "apres reset, on revote"


def test_reset_question_gives_back_the_quiz_points(client: TestClient) -> None:
    me = _join(client, "Louis")
    client.post("/api/admin/activity/open", json={"activity_id": "quiz-companions"}, headers=ADMIN)
    client.post(
        "/api/activities/quiz-companions/questions/qc1/answer",
        json={"participant_id": me["id"], "option_ids": ["qc1b"]},
    )
    assert client.get("/api/leaderboard").json()[0]["score"] > 0

    client.post("/api/admin/activity/reset-question", headers=ADMIN)

    entry = client.get("/api/leaderboard").json()[0]
    assert entry["score"] == 0, "un tour annule ne laisse pas de points"
    assert entry["answers_count"] == 0


def test_reset_question_needs_an_open_activity(client: TestClient) -> None:
    assert client.post("/api/admin/activity/reset-question", headers=ADMIN).status_code == 409


# --------------------------------------------------------------------------- #
# Le jeton qui dit aux telephones d'oublier leur reponse
# --------------------------------------------------------------------------- #
def test_question_token_changes_only_on_reset(client: TestClient) -> None:
    client.post(
        "/api/admin/activity/open", json={"activity_id": "poll-prompt-warmup"}, headers=ADMIN
    )
    first = client.get("/api/session").json()["question_token"]
    assert first

    # Refermer puis rouvrir ne change rien : ceux qui ont vote restent bloques.
    client.post("/api/admin/activity/close", headers=ADMIN)
    client.post(
        "/api/admin/activity/open", json={"activity_id": "poll-prompt-warmup"}, headers=ADMIN
    )
    assert client.get("/api/session").json()["question_token"] == first

    client.post("/api/admin/activity/reset-question", headers=ADMIN)
    assert client.get("/api/session").json()["question_token"] != first


def test_question_token_is_unique_per_question(client: TestClient) -> None:
    client.post(
        "/api/admin/activity/open", json={"activity_id": "poll-prompt-warmup"}, headers=ADMIN
    )
    first = client.get("/api/session").json()["question_token"]
    client.post("/api/admin/activity/next", headers=ADMIN)
    assert client.get("/api/session").json()["question_token"] != first
