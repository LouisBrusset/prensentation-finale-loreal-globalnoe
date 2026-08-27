"""Contenu de la présentation.

>>> TOUT CE FICHIER EST DU CONTENU BOUCHON (fake data) <<<
Le but ici est de valider la plomberie technique : 12 slides, 2 sondages de
3 questions et 1 mini-jeu quiz. Le vrai contenu viendra remplacer ces textes
sans toucher au code (mêmes ids, mêmes structures).

Garde-fous validés en réunion :
  - 1 seule slide sur "ce que j'ai fait" ;
  - le cœur du deck = les recommandations sur l'usage de l'IA ;
  - aucune critique ni recommandation sur Touchless.
"""

from __future__ import annotations

from app.models import Activity, Option, Question

# --------------------------------------------------------------------------- #
# Manifeste des slides du deck (frontend_main)
# --------------------------------------------------------------------------- #
# `activity_id` relie une slide à un sondage / mini-jeu : quand le présentateur
# arrive sur cette slide, le deck ouvre automatiquement l'activité pour les
# téléphones.
SLIDES: list[dict] = [
    {"id": "s01-title", "title": "Présentation finale de stage", "activity_id": None},
    {"id": "s02-join", "title": "Rejoignez la session", "activity_id": None},
    {
        "id": "s03-poll1",
        "title": "Sondage 1 : où en êtes-vous avec l'IA ?",
        "activity_id": "poll-1",
    },
    {"id": "s04-recap", "title": "Ce que j'ai fait (en 1 slide)", "activity_id": None},
    {"id": "s05-reco1", "title": "Reco 1 : le contexte fait 80 % du résultat", "activity_id": None},
    {"id": "s06-reco2", "title": "Reco 2 : itérer plutôt que one-shot", "activity_id": None},
    {"id": "s07-reco3", "title": "Reco 3 : vérifier, toujours", "activity_id": None},
    {
        "id": "s08-quiz",
        "title": "Mini-jeu : vrai ou faux de l'IA générative",
        "activity_id": "quiz-1",
    },
    {
        "id": "s09-companion-anatomy",
        "title": "Anatomie d'un compagnon L'OréalGPT",
        "activity_id": None,
    },
    {
        "id": "s10-companion-demo",
        "title": "Trois compagnons que j'ai construits",
        "activity_id": None,
    },
    {"id": "s11-poll2", "title": "Sondage 2 : et maintenant ?", "activity_id": "poll-2"},
    {"id": "s12-takeaways", "title": "3 choses à retenir + Q&A", "activity_id": None},
    {"id": "s13-podium", "title": "Podium du mini-jeu", "activity_id": None},
]


def _opt(id_: str, label: str, emoji: str | None = None) -> Option:
    return Option(id=id_, label=label, emoji=emoji)


# --------------------------------------------------------------------------- #
# Sondage 1 (slide 3) - 3 questions
# --------------------------------------------------------------------------- #
POLL_1 = Activity(
    id="poll-1",
    kind="poll",
    title="Où en êtes-vous avec l'IA générative ?",
    subtitle="Pas de mauvaise réponse, c'est anonyme (contenu bouchon)",
    slide_id="s03-poll1",
    questions=[
        Question(
            id="p1q1",
            text="À quelle fréquence utilisez-vous une IA générative au travail ?",
            kind="single",
            options=[
                _opt("p1q1a", "Tous les jours", "\U0001F525"),
                _opt("p1q1b", "Quelques fois par semaine", "\U0001F642"),
                _opt("p1q1c", "Quelques fois par mois", "\U0001F914"),
                _opt("p1q1d", "Jamais encore", "\U0001FAE5"),
            ],
        ),
        Question(
            id="p1q2",
            text="Pour quoi l'utilisez-vous le plus ? (plusieurs choix possibles)",
            kind="multi",
            options=[
                _opt("p1q2a", "Rédiger / reformuler", "✍️"),
                _opt("p1q2b", "Résumer des documents", "\U0001F4C4"),
                _opt("p1q2c", "Analyser des données", "\U0001F4CA"),
                _opt("p1q2d", "Brainstormer des idées", "\U0001F4A1"),
                _opt("p1q2e", "Coder / automatiser", "⚙️"),
            ],
        ),
        Question(
            id="p1q3",
            text="Votre plus gros frein aujourd'hui ?",
            kind="single",
            options=[
                _opt("p1q3a", "Je ne sais pas quoi lui demander", "❓"),
                _opt("p1q3b", "Je n'ai pas confiance dans les réponses", "\U0001F9D0"),
                _opt("p1q3c", "Je n'ai pas le temps d'apprendre", "⏱️"),
                _opt("p1q3d", "Aucun, je suis à l'aise", "\U0001F60E"),
            ],
        ),
    ],
)

# --------------------------------------------------------------------------- #
# Mini-jeu quiz (slide 8) - 4 questions chronométrées, avec bonne réponse
# --------------------------------------------------------------------------- #
QUIZ_1 = Activity(
    id="quiz-1",
    kind="quiz",
    title="Vrai ou faux de l'IA générative",
    subtitle="Le plus rapide marque le plus de points (contenu bouchon)",
    slide_id="s08-quiz",
    questions=[
        Question(
            id="q1q1",
            text="Donner un exemple de sortie attendue améliore nettement le résultat.",
            kind="single",
            options=[
                _opt("q1q1a", "Vrai", "✅"),
                _opt("q1q1b", "Faux", "❌"),
            ],
            correct_option_id="q1q1a",
            time_limit_s=20,
        ),
        Question(
            id="q1q2",
            text="Un prompt plus long est toujours un meilleur prompt.",
            kind="single",
            options=[
                _opt("q1q2a", "Vrai", "✅"),
                _opt("q1q2b", "Faux", "❌"),
            ],
            correct_option_id="q1q2b",
            time_limit_s=20,
        ),
        Question(
            id="q1q3",
            text="Que faut-il TOUJOURS faire avant de réutiliser une sortie d'IA ?",
            kind="single",
            options=[
                _opt("q1q3a", "La vérifier à la source", "\U0001F50E"),
                _opt("q1q3b", "La copier telle quelle", "\U0001F4CB"),
                _opt("q1q3c", "La régénérer 3 fois", "\U0001F501"),
                _opt("q1q3d", "La traduire en anglais", "\U0001F30D"),
            ],
            correct_option_id="q1q3a",
            time_limit_s=25,
        ),
        Question(
            id="q1q4",
            text="À quoi sert principalement un compagnon (custom GPT) ?",
            kind="single",
            options=[
                _opt("q1q4a", "Figer un contexte et des instructions réutilisables", "\U0001F4E6"),
                _opt("q1q4b", "Rendre le modèle plus intelligent", "\U0001F9E0"),
                _opt("q1q4c", "Accélérer le temps de réponse", "⚡"),
                _opt("q1q4d", "Stocker des fichiers", "\U0001F5C4️"),
            ],
            correct_option_id="q1q4a",
            time_limit_s=25,
        ),
    ],
)

# --------------------------------------------------------------------------- #
# Sondage 2 (slide 11) - 3 questions
# --------------------------------------------------------------------------- #
POLL_2 = Activity(
    id="poll-2",
    kind="poll",
    title="Et maintenant ?",
    subtitle="Ce que vous comptez tester dès demain (contenu bouchon)",
    slide_id="s11-poll2",
    questions=[
        Question(
            id="p2q1",
            text="Quelle reco allez-vous appliquer en premier ?",
            kind="single",
            options=[
                _opt("p2q1a", "Donner plus de contexte", "\U0001F3AF"),
                _opt("p2q1b", "Itérer au lieu de one-shot", "\U0001F501"),
                _opt("p2q1c", "Systématiser la vérification", "\U0001F50E"),
                _opt("p2q1d", "Me créer un compagnon", "\U0001F916"),
            ],
        ),
        Question(
            id="p2q2",
            text="De 1 à 5, à quel point vous sentez-vous prêt à créer un compagnon ?",
            kind="scale",
            options=[
                _opt("p2q2a", "1 - pas du tout"),
                _opt("p2q2b", "2"),
                _opt("p2q2c", "3"),
                _opt("p2q2d", "4"),
                _opt("p2q2e", "5 - je le fais ce soir"),
            ],
        ),
        Question(
            id="p2q3",
            text="Quel format vous aiderait le plus pour la suite ?",
            kind="multi",
            options=[
                _opt("p2q3a", "Un guide écrit", "\U0001F4D8"),
                _opt("p2q3b", "Un atelier pratique", "\U0001F6E0️"),
                _opt("p2q3c", "Une bibliothèque de prompts", "\U0001F4DA"),
                _opt("p2q3d", "Des compagnons prêts à l'emploi", "\U0001F916"),
            ],
        ),
    ],
)

ACTIVITIES: list[Activity] = [POLL_1, QUIZ_1, POLL_2]
ACTIVITIES_BY_ID: dict[str, Activity] = {a.id: a for a in ACTIVITIES}

SESSION_TITLE = "Stage 2026 - Ce que j'ai appris sur l'IA générative"

# Emojis proposés aux participants au moment de rejoindre. Choisis pour rester
# lisibles en petit sur un vidéoprojecteur, et distinguables entre eux.
AVATAR_EMOJIS = [
    "🦊", "🐶", "🐱", "🐹", "🐼", "🐸",
    "🐵", "🐧", "🦉", "🐝", "🐙", "🦄",
    "🚀", "🎯", "🎸", "🍕", "🌴", "🌋",
    "🔮", "🎩", "🍄", "🌵", "🧊", "🌠",
]

# Pseudos utilisés par le seeder de fausses réponses (`make seed`).
FAKE_NICKNAMES = [
    "Camille", "Sofia", "Yanis", "Marion", "Thomas", "Inès", "Lucas", "Nadia",
    "Hugo", "Chloé", "Karim", "Julie", "Adrien", "Léa", "Mehdi", "Anaïs",
    "Paul", "Sarah", "Victor", "Emma", "Nicolas", "Manon", "Antoine", "Élodie",
    "Gabriel", "Clara", "Maxime", "Alice", "Raphaël", "Jade",
]
