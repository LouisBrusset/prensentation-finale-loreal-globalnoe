"""Tests de fumée : valident que la plomberie tient debout, pas le contenu.

Les activités de référence utilisées dans ces tests :
  - poll-prompt-warmup (poll) : pw1 single, pw2 scale, pw3 multi
  - quiz-companions (quiz)    : qc1..qc4, qc1's correct option is "qc1b"
  - quiz-ai-literacy (quiz)   : qa1..qa4
  - wordcloud-1 (wordcloud)   : wc1q1, wc1q2 — voir test_wordcloud.py
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


def test_health(client: TestClient) -> None:
    assert client.get("/api/health").json()["status"] == "ok"


def test_content_shape(client: TestClient) -> None:
    content = client.get("/api/content").json()
    assert len(content["slides"]) >= 20

    kinds = [a["kind"] for a in content["activities"]]
    assert kinds.count("poll") == 1
    assert kinds.count("quiz") == 2
    assert kinds.count("wordcloud") == 1

    wordcloud = next(a for a in content["activities"] if a["kind"] == "wordcloud")
    assert len(wordcloud["questions"]) == 2
    for question in wordcloud["questions"]:
        assert question["kind"] == "words"
        assert question["options"] == []
        assert 1 <= question["min_words"] <= question["max_words"]

    # La bonne reponse ne doit jamais fuiter vers les telephones.
    for activity in content["activities"]:
        for question in activity["questions"]:
            assert "correct_option_id" not in question


def test_full_poll_roundtrip(client: TestClient) -> None:
    participant = client.post("/api/participants/join", json={"nickname": "Louis"}).json()
    pid = participant["participant"]["id"]

    # Fermé par défaut : le vote est refusé.
    refused = client.post(
        "/api/activities/poll-prompt-warmup/questions/pw1/answer",
        json={"participant_id": pid, "option_ids": ["pw1a"]},
    ).json()
    assert refused["accepted"] is False

    client.post(
        "/api/admin/activity/open", json={"activity_id": "poll-prompt-warmup"}, headers=ADMIN
    )
    accepted = client.post(
        "/api/activities/poll-prompt-warmup/questions/pw1/answer",
        json={"participant_id": pid, "option_ids": ["pw1a"]},
    ).json()
    assert accepted["accepted"] is True

    # Un seul vote par participant et par question.
    twice = client.post(
        "/api/activities/poll-prompt-warmup/questions/pw1/answer",
        json={"participant_id": pid, "option_ids": ["pw1b"]},
    ).json()
    assert twice["accepted"] is False

    results = client.get("/api/results/poll-prompt-warmup").json()
    first = next(q for q in results["questions"] if q["question_id"] == "pw1")
    assert first["total_answers"] == 1
    assert next(b for b in first["buckets"] if b["option_id"] == "pw1a")["pct"] == 100.0


def test_quiz_scores_only_correct_answers(client: TestClient) -> None:
    """Bonne reponse = des points, mauvaise reponse = zero.

    L'effet du temps est teste separement dans
    `test_quiz_score_decreases_with_real_elapsed_time` : ici les deux reponses
    arrivent a quelques millisecondes d'ecart, donc leurs scores se valent.
    """
    right = client.post("/api/participants/join", json={"nickname": "Juste"}).json()["participant"]
    wrong = client.post("/api/participants/join", json={"nickname": "Faux"}).json()["participant"]

    client.post("/api/admin/activity/open", json={"activity_id": "quiz-companions"}, headers=ADMIN)
    good = client.post(
        "/api/activities/quiz-companions/questions/qc1/answer",
        json={"participant_id": right["id"], "option_ids": ["qc1b"]},
    ).json()
    bad = client.post(
        "/api/activities/quiz-companions/questions/qc1/answer",
        json={"participant_id": wrong["id"], "option_ids": ["qc1a"]},
    ).json()

    assert good["awarded_points"] > 0
    assert bad["awarded_points"] == 0

    board = client.get("/api/leaderboard").json()
    assert board[0]["nickname"] == "Juste"
    assert board[1]["score"] == 0


def test_admin_requires_token(client: TestClient) -> None:
    assert client.post("/api/admin/activity/close").status_code == 403


def test_seed_generates_a_plausible_room(client: TestClient) -> None:
    client.post("/api/admin/seed", json={"participants": 20}, headers=ADMIN)
    assert client.get("/api/session").json()["participants_count"] == 20

    poll_results = client.get("/api/results/poll-prompt-warmup").json()
    assert sum(q["total_answers"] for q in poll_results["questions"]) > 0

    # Le seeder doit aussi savoir remplir un nuage de mots (kind="words").
    cloud_results = client.get("/api/results/wordcloud-1").json()
    assert sum(len(q["buckets"]) for q in cloud_results["questions"]) > 0


def test_qr_png_is_a_png(client: TestClient) -> None:
    response = client.get("/api/qr.png")
    assert response.status_code == 200
    assert response.content.startswith(b"\x89PNG")


def test_websocket_pushes_initial_state(client: TestClient) -> None:
    with client.websocket_connect("/ws?role=deck") as ws:
        message = ws.receive_json()
        assert message["type"] == "state"
        assert message["payload"]["status"] == "idle"


def test_join_url_points_at_the_app_not_a_dead_port(client: TestClient) -> None:
    """Le QR doit envoyer sur une URL reellement servie, joignable par un telephone."""
    urls = client.get("/api/join-url").json()

    # L'app participant est servie par le backend sur /app en local.
    assert urls["app_url"].endswith("/app")
    # Et surtout pas sur le port du serveur statique, qui ne tourne pas avec `dev`.
    assert ":5173" not in urls["app_url"]
    # localhost serait inutilisable depuis un telephone.
    assert "localhost" not in urls["app_url"]
    assert "127.0.0.1" not in urls["app_url"]


def test_qr_encodes_the_join_url(client: TestClient) -> None:
    app_url = client.get("/api/join-url").json()["app_url"]
    response = client.get("/api/qr.png")
    assert response.headers["X-QR-Target"] == app_url


def test_quiz_score_decreases_with_real_elapsed_time(client: TestClient) -> None:
    """Le temps retenu est celui du serveur, pas celui annonce par le telephone.

    Regression : un telephone re-rendait sa question a chaque reponse d'un
    voisin, donc son `elapsed_ms` repartait de zero et les plus lents
    marquaient le plus de points.
    """
    import time as _time

    first = client.post("/api/participants/join", json={"nickname": "Premier"}).json()
    second = client.post("/api/participants/join", json={"nickname": "Second"}).json()

    client.post("/api/admin/activity/open", json={"activity_id": "quiz-companions"}, headers=ADMIN)

    early = client.post(
        "/api/activities/quiz-companions/questions/qc1/answer",
        # elapsed_ms client volontairement absurde : il doit etre ignore.
        json={"participant_id": first["participant"]["id"], "option_ids": ["qc1b"],
              "elapsed_ms": 19_000},
    ).json()

    _time.sleep(0.35)

    late = client.post(
        "/api/activities/quiz-companions/questions/qc1/answer",
        # Celui-ci pretend avoir repondu instantanement.
        json={"participant_id": second["participant"]["id"], "option_ids": ["qc1b"],
              "elapsed_ms": 0},
    ).json()

    assert early["elapsed_ms"] < late["elapsed_ms"], "le serveur doit chronometrer lui-meme"
    assert early["awarded_points"] > late["awarded_points"], "repondre plus tot doit rapporter plus"

    board = client.get("/api/leaderboard").json()
    assert board[0]["nickname"] == "Premier"


def test_next_question_advances_and_stops_at_the_last(client: TestClient) -> None:
    client.post(
        "/api/admin/activity/open", json={"activity_id": "poll-prompt-warmup"}, headers=ADMIN
    )
    assert client.get("/api/session").json()["question_index"] == 0

    for expected in (1, 2):
        state = client.post("/api/admin/activity/next", headers=ADMIN).json()
        assert state["question_index"] == expected
        assert state["status"] == "open"

    # Au bout, on reste sur la derniere question : c'est ce qui permet de
    # revenir en arriere ensuite. Le retour au repos se fait en changeant de
    # slide.
    state = client.post("/api/admin/activity/next", headers=ADMIN).json()
    assert state["activity_id"] == "poll-prompt-warmup"
    assert state["question_index"] == 2


def test_next_question_works_after_close_and_reveal(client: TestClient) -> None:
    """`next` doit rester utilisable quel que soit le statut courant."""
    client.post("/api/admin/activity/open", json={"activity_id": "quiz-companions"}, headers=ADMIN)
    client.post("/api/admin/activity/close", headers=ADMIN)
    client.post("/api/admin/activity/reveal", headers=ADMIN)

    state = client.post("/api/admin/activity/next", headers=ADMIN).json()
    assert state["question_index"] == 1
    assert state["status"] == "open"


def test_participants_get_an_emoji(client: TestClient) -> None:
    chosen = client.post(
        "/api/participants/join", json={"nickname": "Choisi", "emoji": "\U0001F984"}
    ).json()["participant"]
    assert chosen["emoji"] == "\U0001F984"

    # Sans choix, le serveur en attribue un depuis la palette.
    palette = client.get("/api/content").json()["avatar_emojis"]
    assert len(palette) >= 12

    auto = client.post("/api/participants/join", json={"nickname": "Auto"}).json()["participant"]
    assert auto["emoji"] in palette


def test_emojis_are_distinct_while_the_palette_lasts(client: TestClient) -> None:
    palette = client.get("/api/content").json()["avatar_emojis"]
    emojis = [
        client.post("/api/participants/join", json={"nickname": f"P{i}"}).json()["participant"][
            "emoji"
        ]
        for i in range(len(palette))
    ]
    assert len(set(emojis)) == len(palette), "chacun doit avoir un emoji different"


def test_emoji_follows_the_participant_into_results_and_leaderboard(client: TestClient) -> None:
    me = client.post(
        "/api/participants/join", json={"nickname": "Suivi", "emoji": "\U0001F680"}
    ).json()["participant"]

    client.post("/api/admin/activity/open", json={"activity_id": "quiz-companions"}, headers=ADMIN)
    client.post(
        "/api/activities/quiz-companions/questions/qc1/answer",
        json={"participant_id": me["id"], "option_ids": ["qc1b"]},
    )

    results = client.get("/api/results/quiz-companions").json()
    first = results["questions"][0]
    good = next(b for b in first["buckets"] if b["option_id"] == "qc1b")
    assert good["voters"] == [{"nickname": "Suivi", "emoji": "\U0001F680"}]

    assert client.get("/api/leaderboard").json()[0]["emoji"] == "\U0001F680"


def test_seeded_participants_also_get_emojis(client: TestClient) -> None:
    client.post("/api/admin/seed", json={"participants": 15}, headers=ADMIN)
    board = client.get("/api/leaderboard?limit=15").json()
    assert all(entry["emoji"] for entry in board)


def test_next_question_is_a_no_op_when_nothing_is_open(client: TestClient) -> None:
    """Appuyer deux fois sur N en fin d'activite ne doit pas produire d'erreur."""
    response = client.post("/api/admin/activity/next", headers=ADMIN)
    assert response.status_code == 200
    assert response.json()["status"] == "idle"


def test_elapsed_s_lets_a_latecomer_see_the_same_countdown(client: TestClient) -> None:
    """Un telephone qui rejoint en cours de question doit voir le temps restant reel."""
    import time as _time

    assert client.get("/api/session").json()["elapsed_s"] == 0.0

    client.post("/api/admin/activity/open", json={"activity_id": "quiz-companions"}, headers=ADMIN)
    _time.sleep(0.4)

    session = client.get("/api/session").json()
    assert session["elapsed_s"] >= 0.35

    # Un retardataire recoit le meme compteur dans sa reponse de join.
    joined = client.post("/api/participants/join", json={"nickname": "Tardif"}).json()
    assert joined["session"]["elapsed_s"] >= 0.35

    # Une fois les votes fermes, le compteur retombe : plus de decompte a afficher.
    client.post("/api/admin/activity/close", headers=ADMIN)
    assert client.get("/api/session").json()["elapsed_s"] == 0.0


def test_deck_ends_on_a_podium_somewhere_near_the_close(client: TestClient) -> None:
    slides = client.get("/api/content").json()["slides"]
    assert len(slides) >= 20
    assert any("podium" in s["id"] for s in slides)
    # Le podium doit venir apres les deux quiz, pas avant.
    ids = [s["id"] for s in slides]
    assert ids.index([i for i in ids if "podium" in i][0]) > ids.index(
        [i for i in ids if "quiz" in i][-1]
    )


def test_voters_are_listed_in_order_of_arrival(client: TestClient) -> None:
    client.post(
        "/api/admin/activity/open", json={"activity_id": "poll-prompt-warmup"}, headers=ADMIN
    )
    for name in ("Un", "Deux", "Trois"):
        pid = client.post("/api/participants/join", json={"nickname": name}).json()["participant"][
            "id"
        ]
        client.post(
            "/api/activities/poll-prompt-warmup/questions/pw1/answer",
            json={"participant_id": pid, "option_ids": ["pw1a"]},
        )

    results = client.get("/api/results/poll-prompt-warmup").json()
    bucket = next(b for b in results["questions"][0]["buckets"] if b["option_id"] == "pw1a")
    assert [v["nickname"] for v in bucket["voters"]] == ["Un", "Deux", "Trois"]


def test_multi_choice_answer_lists_the_voter_under_each_option(client: TestClient) -> None:
    pid = client.post("/api/participants/join", json={"nickname": "Multi"}).json()["participant"][
        "id"
    ]
    client.post(
        "/api/admin/activity/open",
        json={"activity_id": "poll-prompt-warmup", "question_index": 2},
        headers=ADMIN,
    )
    client.post(
        "/api/activities/poll-prompt-warmup/questions/pw3/answer",
        json={"participant_id": pid, "option_ids": ["pw3a", "pw3c"]},
    )

    questions = client.get("/api/results/poll-prompt-warmup").json()["questions"]
    question = next(q for q in questions if q["question_id"] == "pw3")
    chosen = {b["option_id"] for b in question["buckets"] if b["voters"]}
    assert chosen == {"pw3a", "pw3c"}
    # Une seule personne a repondu, meme si elle a coche deux cases.
    assert question["total_answers"] == 1
