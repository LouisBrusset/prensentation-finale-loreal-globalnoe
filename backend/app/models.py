"""Schemas Pydantic : contrat d'API entre le backend et les deux front-ends."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ActivityKind = Literal["poll", "quiz", "wordcloud"]
QuestionKind = Literal["single", "multi", "scale", "words"]
ActivityStatus = Literal["idle", "open", "closed", "revealed"]


# --------------------------------------------------------------------------- #
# Contenu (defini cote serveur, servi aux deux front-ends)
# --------------------------------------------------------------------------- #
class Option(BaseModel):
    id: str
    label: str
    emoji: str | None = None


class Question(BaseModel):
    id: str
    text: str
    kind: QuestionKind = "single"
    options: list[Option] = Field(default_factory=list)
    # Specifique quiz : jamais expose au front participant avant le reveal.
    correct_option_id: str | None = None
    points: int = 1000
    time_limit_s: int = 25
    # Specifique kind="words" (wordcloud) : bornes sur le nombre de mots
    # qu'un participant doit soumettre. Sans effet pour les autres kinds.
    min_words: int = 3
    max_words: int = 5


class Activity(BaseModel):
    id: str
    kind: ActivityKind
    title: str
    subtitle: str | None = None
    slide_id: str | None = None
    questions: list[Question] = Field(default_factory=list)

    def public(self, reveal: bool = False) -> dict:
        """Version envoyee aux telephones : sans la bonne reponse tant qu'on n'a pas revele."""
        data = self.model_dump()
        if not reveal:
            for q in data["questions"]:
                q.pop("correct_option_id", None)
        return data


# --------------------------------------------------------------------------- #
# Participants
# --------------------------------------------------------------------------- #
class JoinRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=24)
    # Laisse vide pour en recevoir un au hasard.
    emoji: str | None = Field(default=None, max_length=8)


class Participant(BaseModel):
    id: str
    nickname: str
    emoji: str = "🙂"
    joined_at: float
    score: int = 0
    answers_count: int = 0


class JoinResponse(BaseModel):
    participant: Participant
    session: SessionState


# --------------------------------------------------------------------------- #
# Reponses
# --------------------------------------------------------------------------- #
class AnswerRequest(BaseModel):
    participant_id: str
    option_ids: list[str] = Field(default_factory=list)
    # Specifique kind="words" : les mots soumis librement par le participant,
    # non normalises (le serveur s'en charge pour l'agregation).
    words: list[str] = Field(default_factory=list)
    elapsed_ms: int = 0


class AnswerResponse(BaseModel):
    accepted: bool
    reason: str | None = None
    awarded_points: int = 0
    total_score: int = 0
    # Temps effectivement retenu pour le calcul des points, mesure par le
    # serveur depuis l'ouverture de la question.
    elapsed_ms: int = 0


# --------------------------------------------------------------------------- #
# Etat de session
# --------------------------------------------------------------------------- #
class SessionState(BaseModel):
    session_title: str
    slide_index: int
    activity_id: str | None
    question_index: int
    status: ActivityStatus
    participants_count: int
    answers_count: int
    opened_at: float | None = None
    # Secondes ecoulees depuis l'ouverture de la question, mesurees par le
    # serveur. Permet a un telephone qui rejoint en cours de route d'afficher
    # le meme compte a rebours que tout le monde, sans dependre de son horloge.
    elapsed_s: float = 0.0
    # Identifie le "tour" de la question courante : change quand le presentateur
    # reinitialise la question. Les telephones s'en servent pour savoir s'ils
    # doivent oublier qu'ils avaient deja repondu.
    question_token: str = ""


class Voter(BaseModel):
    nickname: str
    emoji: str


class ResultBucket(BaseModel):
    option_id: str
    label: str
    count: int
    pct: float
    # Qui a choisi cette option. Sert aux panneaux de noms affiches au reveal.
    voters: list[Voter] = Field(default_factory=list)


class QuestionResults(BaseModel):
    question_id: str
    question_text: str
    kind: QuestionKind
    total_answers: int
    correct_option_id: str | None = None
    buckets: list[ResultBucket]


class ActivityResults(BaseModel):
    activity_id: str
    title: str
    kind: ActivityKind
    questions: list[QuestionResults]


class LeaderboardEntry(BaseModel):
    rank: int
    participant_id: str
    nickname: str
    emoji: str
    score: int
    answers_count: int


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #
class OpenActivityRequest(BaseModel):
    activity_id: str
    question_index: int = 0


class ResumeRequest(BaseModel):
    activity_id: str


class SlideRequest(BaseModel):
    slide_index: int


class SeedRequest(BaseModel):
    participants: int = 25
    answer_everything: bool = True


JoinResponse.model_rebuild()
