"""Content of the presentation: slide manifest + all interactive activities.

This is the final content (no longer a placeholder). It backs a live talk
given to a 10-12 person team: a quick recap of the internship, a masterclass
on L'OréalGPT Companions, and a set of non-101 prompting tips — with word
clouds, polls and quizzes woven through to keep it interactive.

Editorial constraints agreed with the manager, still honoured here:
  - exactly one slide on "what I did" during the internship;
  - the real focus is the recommendations on using AI;
  - no criticism of Touchless, no Touchless recommendations either.
"""

from __future__ import annotations

from app.models import Activity, Option, Question

# --------------------------------------------------------------------------- #
# Deck manifest (frontend_main)
# --------------------------------------------------------------------------- #
# `activity_id` ties a slide to a poll / quiz / word cloud: when the presenter
# lands on that slide, the deck automatically opens the activity for phones.
SLIDES: list[dict] = [
    {"id": "s01-title", "title": "Title", "activity_id": None},
    {"id": "s02-agenda", "title": "Agenda", "activity_id": None},
    {"id": "s03-journey", "title": "My journey", "activity_id": None},
    {"id": "s04-achievements", "title": "What I actually did", "activity_id": None},
    {"id": "s05-join", "title": "Join the session", "activity_id": None},
    {"id": "s06-wordcloud", "title": "Word cloud warm-up", "activity_id": "wordcloud-1"},
    {"id": "s07-companion-intro", "title": "Meet the Companions", "activity_id": None},
    {"id": "s08-companion-types", "title": "Three flavours of Companion", "activity_id": None},
    {"id": "s09-companion-lifecycle", "title": "From idea to live Companion", "activity_id": None},
    {"id": "s10-companion-anatomy", "title": "Anatomy of a Companion", "activity_id": None},
    {"id": "s11-companion-powerups", "title": "Giving it super-powers", "activity_id": None},
    {"id": "s12-companion-validation", "title": "Proving it actually works", "activity_id": None},
    {"id": "s13-companion-mine", "title": "My own Companions", "activity_id": None},
    {
        "id": "s14-quiz-companions",
        "title": "Quiz: did that stick?",
        "activity_id": "quiz-companions",
    },
    {
        "id": "s15-prompt-warmup",
        "title": "Prompting instincts check",
        "activity_id": "poll-prompt-warmup",
    },
    {"id": "s16-tip-workflow", "title": "Two workflow habits", "activity_id": None},
    {
        "id": "s17-tip-negation",
        "title": "The trick with actual math behind it",
        "activity_id": None,
    },
    {"id": "s18-tip-variables", "title": "Prompts that scale", "activity_id": None},
    {"id": "s19-tip-verify", "title": "Trust, but verify", "activity_id": None},
    {
        "id": "s20-quiz-ai-literacy",
        "title": "Quiz: AI literacy",
        "activity_id": "quiz-ai-literacy",
    },
    {"id": "s21-podium", "title": "Podium", "activity_id": None},
    {"id": "s22-conclusion", "title": "Thank you", "activity_id": None},
]


def _opt(id_: str, label: str, emoji: str | None = None) -> Option:
    return Option(id=id_, label=label, emoji=emoji)


def _words(id_: str, text: str) -> Question:
    return Question(id=id_, text=text, kind="words", min_words=3, max_words=5)


# --------------------------------------------------------------------------- #
# Word cloud warm-up (slide 6) — no scoring, pure ice-breaker.
# --------------------------------------------------------------------------- #
WORDCLOUD_1 = Activity(
    id="wordcloud-1",
    kind="wordcloud",
    title="Word cloud warm-up",
    subtitle="3 to 5 words, whatever comes to mind — there's no wrong answer",
    slide_id="s06-wordcloud",
    questions=[
        _words("wc1q1", "In 3-5 words: what comes to mind when you hear “Generative AI”?"),
        _words("wc1q2", "Now do the same for “Companion.” 3-5 words, go!"),
    ],
)

# --------------------------------------------------------------------------- #
# Quiz: Companions (slide 14) — checks whether Part 2 landed.
# --------------------------------------------------------------------------- #
QUIZ_COMPANIONS = Activity(
    id="quiz-companions",
    kind="quiz",
    title="Did that stick?",
    subtitle="Four questions on what we just covered",
    slide_id="s14-quiz-companions",
    questions=[
        Question(
            id="qc1",
            text="A colleague wants an AI to open their Excel file, run formulas across "
            "several tabs, and auto-build a pivot table. Best move?",
            kind="single",
            options=[
                _opt(
                    "qc1a",
                    "Build a Métier Companion with Conversational Analytics",
                    "\U0001F4CA",
                ),
                _opt(
                    "qc1b",
                    "Tell them a Companion isn't the right tool for that job",
                    "\U0001F6D1",
                ),
                _opt("qc1c", "Paste the whole spreadsheet into Standard Chat", "\U0001F4CB"),
                _opt("qc1d", "Point AKS at the spreadsheet and let it search", "\U0001F50D"),
            ],
            correct_option_id="qc1b",
            time_limit_s=25,
        ),
        Question(
            id="qc2",
            text="Which Companion type needs formal Métier validation before you can "
            "even start building it?",
            kind="single",
            options=[
                _opt("qc2a", "MyCompanion", "\U0001F464"),
                _opt("qc2b", "Team Companion", "\U0001F465"),
                _opt("qc2c", "Métier Companion", "\U0001F3E2"),
                _opt("qc2d", "Standard Chat", "\U0001F4AC"),
            ],
            correct_option_id="qc2c",
            time_limit_s=20,
        ),
        Question(
            id="qc3",
            text="What minimum automatic accuracy score does a Métier Companion "
            "need to launch (non-creative use cases)?",
            kind="single",
            options=[
                _opt("qc3a", "50%"),
                _opt("qc3b", "65%"),
                _opt("qc3c", "80%"),
                _opt("qc3d", "95%"),
            ],
            correct_option_id="qc3c",
            time_limit_s=20,
        ),
        Question(
            id="qc4",
            text="Which model would nail flawless Chinese-language content... but "
            "you literally cannot pick it for a Companion today?",
            kind="single",
            options=[
                _opt("qc4a", "Claude Sonnet"),
                _opt("qc4b", "Gemini Flash"),
                _opt("qc4c", "GPT Terra"),
                _opt("qc4d", "DeepSeek"),
            ],
            correct_option_id="qc4d",
            time_limit_s=25,
        ),
    ],
)

# --------------------------------------------------------------------------- #
# Poll: prompting instincts (slide 15) — opinions, no correct answer, opens
# Part 3 by finding out what the room already believes before the tips land.
# --------------------------------------------------------------------------- #
POLL_PROMPT_WARMUP = Activity(
    id="poll-prompt-warmup",
    kind="poll",
    title="Prompting instincts check",
    subtitle="No right answer here — let's see what the room actually thinks",
    slide_id="s15-prompt-warmup",
    questions=[
        Question(
            id="pw1",
            text="Which habit do you think helps MOST when prompting an AI?",
            kind="single",
            options=[
                _opt("pw1a", "Being extremely polite (please, thank you...)", "\U0001F64F"),
                _opt("pw1b", "Telling it exactly what NOT to do", "\U0001F6AB"),
                _opt("pw1c", "Perfect grammar and full sentences", "\U0001F4DD"),
                _opt("pw1d", "One giant do-everything mega-prompt", "\U0001F4A3"),
            ],
        ),
        Question(
            id="pw2",
            text="Rate your own prompt-engineering game, honestly.",
            kind="scale",
            options=[
                _opt("pw2a", "1 - I panic-prompt"),
                _opt("pw2b", "2"),
                _opt("pw2c", "3"),
                _opt("pw2d", "4"),
                _opt("pw2e", "5 - I could teach this"),
            ],
        ),
        Question(
            id="pw3",
            text="Which of these do you already do on a regular basis?",
            kind="multi",
            options=[
                _opt("pw3a", "Iterating instead of expecting a perfect first answer", "\U0001F501"),
                _opt("pw3b", "Giving 2-3 examples of what I want", "\U0001F3AF"),
                _opt("pw3c", "Asking for a ready-to-paste box or table", "\U0001F4E6"),
                _opt("pw3d", "Breaking a big task into smaller steps", "\U0001FA9C"),
                _opt("pw3e", "None of the above, I panic-prompt", "\U0001F625"),
            ],
        ),
    ],
)

# --------------------------------------------------------------------------- #
# Quiz: AI literacy (slide 20) — closes Part 3, doubles as a fun dry run for
# the real AmplifAI self-assessment.
# --------------------------------------------------------------------------- #
QUIZ_AI_LITERACY = Activity(
    id="quiz-ai-literacy",
    kind="quiz",
    title="AI literacy check",
    subtitle="A fun dry run before your real AmplifAI self-assessment",
    slide_id="s20-quiz-ai-literacy",
    questions=[
        Question(
            id="qa1",
            text="Your AI tool flags a fraudulent transaction by matching patterns "
            "in historical data. Which type of AI is that?",
            kind="single",
            options=[
                _opt("qa1a", "Generative AI"),
                _opt("qa1b", "Analytical AI"),
                _opt("qa1c", "Predictive AI"),
                _opt("qa1d", "Agentic AI"),
            ],
            correct_option_id="qa1b",
            time_limit_s=22,
        ),
        Question(
            id="qa2",
            text="An AI states, with total confidence, a statistic that turns out "
            "to be completely made up. What's this called?",
            kind="single",
            options=[
                _opt("qa2a", "Data drift"),
                _opt("qa2b", "Automation bias"),
                _opt("qa2c", "Hallucination"),
                _opt("qa2d", "Concept drift"),
            ],
            correct_option_id="qa2c",
            time_limit_s=20,
        ),
        Question(
            id="qa3",
            text="Under the EU AI Act, which of these counts as HIGH RISK, requiring "
            "human oversight?",
            kind="single",
            options=[
                _opt("qa3a", "A spam filter"),
                _opt("qa3b", "An AI recruitment / hiring tool"),
                _opt("qa3c", "An HR FAQ chatbot"),
                _opt("qa3d", "A content generator that labels itself as AI"),
            ],
            correct_option_id="qa3b",
            time_limit_s=25,
        ),
        Question(
            id="qa4",
            text="Your Companion always fetches the latest info from a live "
            "knowledge base before answering, instead of relying only on its "
            "training. What's this architecture called?",
            kind="single",
            options=[
                _opt("qa4a", "Transfer learning"),
                _opt("qa4b", "Federated learning"),
                _opt("qa4c", "RAG (Retrieval-Augmented Generation)"),
                _opt("qa4d", "Meta-prompting"),
            ],
            correct_option_id="qa4c",
            time_limit_s=22,
        ),
    ],
)

ACTIVITIES: list[Activity] = [
    WORDCLOUD_1,
    QUIZ_COMPANIONS,
    POLL_PROMPT_WARMUP,
    QUIZ_AI_LITERACY,
]
ACTIVITIES_BY_ID: dict[str, Activity] = {a.id: a for a in ACTIVITIES}

SESSION_TITLE = "Final Presentation - Louis Brusset - Global Demand Planning"

# Emojis offered to participants when they join. Kept topic-neutral on
# purpose: works for any presentation, not just this one.
AVATAR_EMOJIS = [
    "\U0001F98A", "\U0001F436", "\U0001F431", "\U0001F439", "\U0001F43C", "\U0001F438",
    "\U0001F435", "\U0001F427", "\U0001F989", "\U0001F41D", "\U0001F419", "\U0001F984",
    "\U0001F680", "\U0001F3AF", "\U0001F3B8", "\U0001F355", "\U0001F334", "\U0001F30B",
    "\U0001F52E", "\U0001F3A9", "\U0001F344", "\U0001F335", "\U0001F9CA", "\U0001F320",
]

# Nicknames used by the demo seeder (`make seed`).
FAKE_NICKNAMES = [
    "Camille", "Sofia", "Yanis", "Marion", "Thomas", "Ines", "Lucas", "Nadia",
    "Hugo", "Chloe", "Karim", "Julie", "Adrien", "Lea", "Mehdi", "Anais",
    "Paul", "Sarah", "Victor", "Emma", "Nicolas", "Manon", "Antoine", "Elodie",
    "Gabriel", "Clara", "Maxime", "Alice", "Raphael", "Jade",
]
