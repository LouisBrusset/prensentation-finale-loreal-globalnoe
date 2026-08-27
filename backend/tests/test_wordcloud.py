"""Nuage de mots : soumission libre, agrégation, bornes, et absence de score.

L'activité de référence est `wordcloud-1` (kind="wordcloud"), avec deux
questions kind="words" : wc1q1 (3 a 5 mots) et wc1q2 (3 a 5 mots).
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


def _answer(client: TestClient, participant_id: str, words: list[str], question: str = "wc1q1"):
    return client.post(
        f"/api/activities/wordcloud-1/questions/{question}/answer",
        json={"participant_id": participant_id, "words": words},
    ).json()


# --------------------------------------------------------------------------- #
# Bornes (min/max mots)
# --------------------------------------------------------------------------- #
def test_rejects_too_few_words(client: TestClient) -> None:
    me = _join(client, "Louis")
    client.post("/api/admin/activity/open", json={"activity_id": "wordcloud-1"}, headers=ADMIN)

    result = _answer(client, me["id"], ["ai", "future"])  # 2 mots, minimum 3
    assert result["accepted"] is False
    assert "3" in result["reason"] and "5" in result["reason"]


def test_rejects_too_many_words(client: TestClient) -> None:
    me = _join(client, "Louis")
    client.post("/api/admin/activity/open", json={"activity_id": "wordcloud-1"}, headers=ADMIN)

    result = _answer(client, me["id"], ["a", "b", "c", "d", "e", "f"])  # 6 mots, maximum 5
    assert result["accepted"] is False


def test_accepts_within_bounds(client: TestClient) -> None:
    me = _join(client, "Louis")
    client.post("/api/admin/activity/open", json={"activity_id": "wordcloud-1"}, headers=ADMIN)

    assert _answer(client, me["id"], ["ai", "future", "hype"])["accepted"] is True


def test_blank_words_are_ignored_when_counting_bounds(client: TestClient) -> None:
    """Des cases vides ne doivent pas compter comme des mots valides."""
    me = _join(client, "Louis")
    client.post("/api/admin/activity/open", json={"activity_id": "wordcloud-1"}, headers=ADMIN)

    result = _answer(client, me["id"], ["ai", "  ", "future", "", "hype"])
    assert result["accepted"] is True

    results = client.get("/api/results/wordcloud-1").json()
    buckets = results["questions"][0]["buckets"]
    assert sum(b["count"] for b in buckets) == 3, "les cases vides ne sont pas des mots"


# --------------------------------------------------------------------------- #
# Agregation et normalisation
# --------------------------------------------------------------------------- #
def test_aggregates_case_and_whitespace_variants_together(client: TestClient) -> None:
    alice = _join(client, "Alice")
    bob = _join(client, "Bob")
    client.post("/api/admin/activity/open", json={"activity_id": "wordcloud-1"}, headers=ADMIN)

    _answer(client, alice["id"], ["AI", "Prompting", "Future"])
    _answer(client, bob["id"], [" ai ", "prompting!", "hype"])

    results = client.get("/api/results/wordcloud-1").json()
    buckets = {b["label"].lower().strip(): b for b in results["questions"][0]["buckets"]}

    assert buckets["ai"]["count"] == 2, "AI et ai doivent fusionner"
    assert len(buckets["ai"]["voters"]) == 2
    assert buckets["prompting"]["count"] == 2, "la ponctuation de bord ne doit pas separer les mots"
    assert buckets["future"]["count"] == 1
    assert buckets["hype"]["count"] == 1


def test_buckets_are_sorted_by_frequency_descending(client: TestClient) -> None:
    people = [_join(client, f"P{i}") for i in range(4)]
    client.post("/api/admin/activity/open", json={"activity_id": "wordcloud-1"}, headers=ADMIN)

    for i, person in enumerate(people):
        words = ["chatbot", "shortcut", "hype"] if i < 3 else ["shortcut", "magic", "fast"]
        _answer(client, person["id"], words)

    buckets = client.get("/api/results/wordcloud-1").json()["questions"][0]["buckets"]
    counts = [b["count"] for b in buckets]
    assert counts == sorted(counts, reverse=True)
    assert buckets[0]["label"].lower() in ("chatbot", "shortcut")


def test_percentages_are_relative_to_total_words_not_participants(client: TestClient) -> None:
    """4 personnes x 3 mots = 12 mots soumis, pas 4 'réponses'."""
    people = [_join(client, f"P{i}") for i in range(4)]
    client.post("/api/admin/activity/open", json={"activity_id": "wordcloud-1"}, headers=ADMIN)
    for person in people:
        _answer(client, person["id"], ["same", "same", "unique"])

    question = client.get("/api/results/wordcloud-1").json()["questions"][0]
    assert question["total_answers"] == 4  # 4 participants ont repondu
    total_words = sum(b["count"] for b in question["buckets"])
    assert total_words == 12  # mais 12 mots ont ete comptes


# --------------------------------------------------------------------------- #
# Pas de score, pas de classement affecte
# --------------------------------------------------------------------------- #
def test_wordcloud_never_awards_points(client: TestClient) -> None:
    me = _join(client, "Louis")
    client.post("/api/admin/activity/open", json={"activity_id": "wordcloud-1"}, headers=ADMIN)

    result = _answer(client, me["id"], ["ai", "future", "hype"])
    assert result["awarded_points"] == 0
    assert result["total_score"] == 0

    board = client.get("/api/leaderboard").json()
    assert all(entry["score"] == 0 for entry in board if entry["nickname"] == "Louis")


# --------------------------------------------------------------------------- #
# Les deux tours (Generative AI, puis Companion)
# --------------------------------------------------------------------------- #
def test_moving_to_the_second_round_keeps_the_first_rounds_words(client: TestClient) -> None:
    me = _join(client, "Louis")
    client.post("/api/admin/activity/open", json={"activity_id": "wordcloud-1"}, headers=ADMIN)
    _answer(client, me["id"], ["chatbot", "future", "hype"], question="wc1q1")

    client.post("/api/admin/activity/next", headers=ADMIN)
    assert client.get("/api/session").json()["question_index"] == 1

    _answer(client, me["id"], ["assistant", "custom", "helper"], question="wc1q2")

    results = client.get("/api/results/wordcloud-1").json()
    first, second = results["questions"]
    assert sum(b["count"] for b in first["buckets"]) == 3
    assert sum(b["count"] for b in second["buckets"]) == 3
    first_words = {b["label"].lower() for b in first["buckets"]}
    second_words = {b["label"].lower() for b in second["buckets"]}
    assert first_words.isdisjoint(second_words)


# --------------------------------------------------------------------------- #
# Reinitialisation
# --------------------------------------------------------------------------- #
def test_reset_question_clears_words_and_allows_resubmission(client: TestClient) -> None:
    me = _join(client, "Louis")
    client.post("/api/admin/activity/open", json={"activity_id": "wordcloud-1"}, headers=ADMIN)
    _answer(client, me["id"], ["ai", "future", "hype"])

    assert _answer(client, me["id"], ["again", "nope", "blocked"])["accepted"] is False

    client.post("/api/admin/activity/reset-question", headers=ADMIN)

    results = client.get("/api/results/wordcloud-1").json()
    assert results["questions"][0]["buckets"] == []

    retry = _answer(client, me["id"], ["second", "attempt", "now"])
    assert retry["accepted"] is True
