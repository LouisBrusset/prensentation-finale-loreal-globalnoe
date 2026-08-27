"""Store en mémoire de la session live.

Volontairement sans base de données : une présentation dure une heure, tient
en RAM, et un redémarrage du serveur = une session repartie de zéro (ce qui est
le comportement souhaité). Si un jour il faut de la persistance, ce module est
le seul endroit à remplacer (par du SQLite ou du Redis).
"""

from __future__ import annotations

import random
import secrets
import time
from dataclasses import dataclass, field

from app.data.content import (
    ACTIVITIES_BY_ID,
    AVATAR_EMOJIS,
    FAKE_NICKNAMES,
    SESSION_TITLE,
    SLIDES,
)
from app.models import (
    Activity,
    ActivityResults,
    ActivityStatus,
    LeaderboardEntry,
    Participant,
    QuestionResults,
    ResultBucket,
    SessionState,
    Voter,
)


@dataclass
class _Answer:
    participant_id: str
    option_ids: list[str]
    elapsed_ms: int
    at: float


@dataclass
class SessionStore:
    """État complet de la session en cours."""

    participants: dict[str, Participant] = field(default_factory=dict)
    # answers[activity_id][question_id][participant_id] = _Answer
    answers: dict[str, dict[str, dict[str, _Answer]]] = field(default_factory=dict)

    slide_index: int = 0
    activity_id: str | None = None
    question_index: int = 0
    status: ActivityStatus = "idle"
    opened_at: float | None = None

    # ------------------------------------------------------------------ #
    # Cycle de vie
    # ------------------------------------------------------------------ #
    def reset(self) -> None:
        self.participants.clear()
        self.answers.clear()
        self.slide_index = 0
        self.activity_id = None
        self.question_index = 0
        self.status = "idle"
        self.opened_at = None

    # ------------------------------------------------------------------ #
    # Participants
    # ------------------------------------------------------------------ #
    def join(self, nickname: str, emoji: str | None = None) -> Participant:
        pid = secrets.token_urlsafe(9)
        participant = Participant(
            id=pid,
            nickname=nickname.strip()[:24],
            emoji=(emoji or "").strip()[:8] or self._pick_emoji(),
            joined_at=time.time(),
        )
        self.participants[pid] = participant
        return participant

    def _pick_emoji(self) -> str:
        """Tire un emoji libre ; repart sur la palette entière une fois épuisée."""
        taken = {p.emoji for p in self.participants.values()}
        free = [e for e in AVATAR_EMOJIS if e not in taken]
        return random.choice(free or AVATAR_EMOJIS)

    # ------------------------------------------------------------------ #
    # Pilotage (admin / deck)
    # ------------------------------------------------------------------ #
    def open_activity(self, activity_id: str, question_index: int = 0) -> None:
        if activity_id not in ACTIVITIES_BY_ID:
            raise KeyError(activity_id)
        self.activity_id = activity_id
        self.question_index = question_index
        self.status = "open"
        self.opened_at = time.time()

    def close_activity(self) -> None:
        if self.activity_id:
            self.status = "closed"

    def reveal(self) -> None:
        if self.activity_id:
            self.status = "revealed"

    def idle(self) -> None:
        self.activity_id = None
        self.question_index = 0
        self.status = "idle"
        self.opened_at = None

    def set_slide(self, index: int) -> None:
        self.slide_index = max(0, min(index, len(SLIDES) - 1))

    # ------------------------------------------------------------------ #
    # Réponses
    # ------------------------------------------------------------------ #
    def current_activity(self) -> Activity | None:
        if self.activity_id is None:
            return None
        return ACTIVITIES_BY_ID[self.activity_id]

    def current_question(self):
        activity = self.current_activity()
        if activity is None:
            return None
        if 0 <= self.question_index < len(activity.questions):
            return activity.questions[self.question_index]
        return None

    def record_answer(
        self,
        activity_id: str,
        question_id: str,
        participant_id: str,
        option_ids: list[str],
        elapsed_ms: int,
    ) -> tuple[int, int]:
        """Enregistre une réponse. Renvoie `(points gagnés, temps retenu en ms)`.

        Le temps retenu est **mesuré par le serveur** dès qu'une activité est
        ouverte : `maintenant - opened_at`. Il n'est identique pour personne et
        démarre au même instant pour toute la salle, donc deux participants qui
        répondent à 3 s et à 12 s sont départagés correctement.

        Le `elapsed_ms` envoyé par le client ne sert que de repli (activité
        fermée, ou seeder de démo) : il n'est pas fiable, et il a déjà causé
        l'inversion du classement — un téléphone re-rendait sa question à chaque
        réponse d'un voisin et repartait donc de zéro.
        """
        activity = ACTIVITIES_BY_ID[activity_id]
        question = next(q for q in activity.questions if q.id == question_id)
        now = time.time()

        server_timed = (
            self.status == "open"
            and self.opened_at is not None
            and self.activity_id == activity_id
            and self.question_index < len(activity.questions)
            and activity.questions[self.question_index].id == question_id
        )
        effective_ms = int((now - self.opened_at) * 1000) if server_timed else max(elapsed_ms, 0)

        bucket = self.answers.setdefault(activity_id, {}).setdefault(question_id, {})
        already_answered = participant_id in bucket
        bucket[participant_id] = _Answer(
            participant_id=participant_id,
            option_ids=option_ids,
            elapsed_ms=effective_ms,
            at=now,
        )

        participant = self.participants.get(participant_id)
        if participant and not already_answered:
            participant.answers_count += 1

        awarded = 0
        if activity.kind == "quiz" and question.correct_option_id:
            if option_ids and option_ids[0] == question.correct_option_id:
                # Kahoot-like : base + bonus de rapidité décroissant linéairement,
                # de `points` (réponse instantanée) à `points / 2` (au buzzer).
                limit_ms = max(question.time_limit_s, 1) * 1000
                speed_ratio = max(0.0, 1.0 - (effective_ms / limit_ms))
                awarded = int(question.points * (0.5 + 0.5 * speed_ratio))
            if participant:
                participant.score += awarded
        return awarded, effective_ms

    def has_answered(self, activity_id: str, question_id: str, participant_id: str) -> bool:
        return participant_id in self.answers.get(activity_id, {}).get(question_id, {})

    def answers_count(self, activity_id: str | None, question_id: str | None) -> int:
        if not activity_id or not question_id:
            return 0
        return len(self.answers.get(activity_id, {}).get(question_id, {}))

    # ------------------------------------------------------------------ #
    # Agrégations
    # ------------------------------------------------------------------ #
    def results_for(self, activity_id: str) -> ActivityResults:
        activity = ACTIVITIES_BY_ID[activity_id]
        questions: list[QuestionResults] = []

        for question in activity.questions:
            given = self.answers.get(activity_id, {}).get(question.id, {})
            counts = {opt.id: 0 for opt in question.options}
            voters: dict[str, list[Voter]] = {opt.id: [] for opt in question.options}

            # Ordre d'arrivee : les premiers a avoir vote apparaissent en premier.
            for answer in sorted(given.values(), key=lambda a: a.at):
                participant = self.participants.get(answer.participant_id)
                for oid in answer.option_ids:
                    if oid not in counts:
                        continue
                    counts[oid] += 1
                    if participant:
                        voters[oid].append(
                            Voter(nickname=participant.nickname, emoji=participant.emoji)
                        )

            total_votes = sum(counts.values())
            buckets = [
                ResultBucket(
                    option_id=opt.id,
                    label=opt.label,
                    count=counts[opt.id],
                    pct=round(100 * counts[opt.id] / total_votes, 1) if total_votes else 0.0,
                    voters=voters[opt.id],
                )
                for opt in question.options
            ]
            questions.append(
                QuestionResults(
                    question_id=question.id,
                    question_text=question.text,
                    kind=question.kind,
                    total_answers=len(given),
                    correct_option_id=question.correct_option_id,
                    buckets=buckets,
                )
            )

        return ActivityResults(
            activity_id=activity.id,
            title=activity.title,
            kind=activity.kind,
            questions=questions,
        )

    def leaderboard(self, limit: int = 10) -> list[LeaderboardEntry]:
        ranked = sorted(
            self.participants.values(),
            key=lambda p: (-p.score, p.joined_at),
        )[:limit]
        return [
            LeaderboardEntry(
                rank=i + 1,
                participant_id=p.id,
                nickname=p.nickname,
                emoji=p.emoji,
                score=p.score,
                answers_count=p.answers_count,
            )
            for i, p in enumerate(ranked)
        ]

    def snapshot(self) -> SessionState:
        question = self.current_question()
        elapsed_s = (
            round(time.time() - self.opened_at, 2)
            if self.opened_at is not None and self.status == "open"
            else 0.0
        )
        return SessionState(
            session_title=SESSION_TITLE,
            slide_index=self.slide_index,
            activity_id=self.activity_id,
            question_index=self.question_index,
            status=self.status,
            participants_count=len(self.participants),
            answers_count=self.answers_count(self.activity_id, question.id if question else None),
            opened_at=self.opened_at,
            elapsed_s=elapsed_s,
        )

    # ------------------------------------------------------------------ #
    # Démo : génère des participants et des réponses plausibles
    # ------------------------------------------------------------------ #
    def seed_fake(self, participants: int = 25, answer_everything: bool = True) -> int:
        rng = random.Random(42 + len(self.participants))
        created = 0
        for i in range(participants):
            base = FAKE_NICKNAMES[i % len(FAKE_NICKNAMES)]
            suffix = "" if i < len(FAKE_NICKNAMES) else f"-{i // len(FAKE_NICKNAMES)}"
            # Emoji laisse a None : `join` en tire un libre, comme pour un
            # vrai participant.
            participant = self.join(f"{base}{suffix}")
            created += 1

            if not answer_everything:
                continue

            for activity in ACTIVITIES_BY_ID.values():
                for question in activity.questions:
                    if rng.random() < 0.12:  # ~12 % de non-réponses, plus réaliste
                        continue
                    if question.kind == "multi":
                        k = rng.randint(1, min(3, len(question.options)))
                        picked = [o.id for o in rng.sample(question.options, k)]
                    elif activity.kind == "quiz" and question.correct_option_id:
                        # 65 % de bonnes réponses
                        if rng.random() < 0.65:
                            picked = [question.correct_option_id]
                        else:
                            wrong = [
                                o.id for o in question.options if o.id != question.correct_option_id
                            ]
                            picked = [rng.choice(wrong)]
                    else:
                        picked = [rng.choice(question.options).id]

                    # Activite fermee pendant le seed : le temps client fait foi,
                    # ce qui est exactement ce qu'on veut pour fabriquer un
                    # classement plausible.
                    self.record_answer(
                        activity.id,
                        question.id,
                        participant.id,
                        picked,
                        elapsed_ms=rng.randint(1500, question.time_limit_s * 1000),
                    )
        return created


# Instance unique partagée par toute l'application.
store = SessionStore()
