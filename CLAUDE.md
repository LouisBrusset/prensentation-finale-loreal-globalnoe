# final_presentation — contexte pour l'assistant

Présentation finale de stage, interactive : un deck HTML projeté + une app
participant ouverte au téléphone via QR code + un backend FastAPI qui agrège les
réponses en temps réel. **Contenu final, en anglais**, pas du bouchon.

## Commandes

```bash
./make.sh install   # uv venv + uv sync
./make.sh dev       # API + deck (/deck) + app participant (/app) sur :8010
./make.sh test      # pytest
./make.sh lint      # ruff
```

`make` n'est pas installé sur cette machine. Quatre lanceurs équivalents, mêmes
cibles : `make.sh` (Git Bash — **c'est le shell utilisé au quotidien**),
`make.ps1` (PowerShell), `make.cmd` (universel), `Makefile` (si GNU Make installé).
Ne jamais proposer `.\make.ps1` pour du Git Bash.

**Le port par défaut est 8010, pas 8000.** Le 8000 est tenu par des règles
`netsh portproxy` (WSL) via le service IP Helper : le bind échoue avec
`WinError 10013`. Ne pas revenir à 8000.

## Où va quoi

| Sujet | Fichier |
|---|---|
| Texte des slides (anglais) | `frontend_main/index.html` |
| Sondages, quiz, nuages de mots | `backend/app/data/content.py` |
| État de session, scoring, agrégations | `backend/app/state.py` |
| Contrat d'API | `backend/app/models.py` |
| Client HTTP + WebSocket | `frontend_main/js/api.js` (dupliqué dans `frontend_user/js/api.js` — reporter les modifs) |
| Barres de résultats (poll/quiz) | `frontend_main/js/live.js` |
| Nuage de mots en direct (bulles) | `frontend_main/js/wordcloud.js` |
| Triptyque du reveal + podium | `frontend_main/js/reveal.js` |
| Saisie de mots côté téléphone | `frontend_user/js/app.js` (`renderWordsInput`) |

## Trois types d'activité

`ActivityKind = "poll" | "quiz" | "wordcloud"`. Un nuage de mots est une
activité à part : ses questions ont `kind="words"`, pas d'`options` fixées à
l'avance — les « buckets » émergent des mots soumis (normalisés : minuscules,
espaces et ponctuation de bord retirés). Jamais de score, jamais de reveal.
Voir `state._word_buckets()` et `normalize_word()`.

## Pièges récurrents sur le front

`state` est diffusé à chaque réponse de la salle. Ne jamais reconstruire du DOM
à chaque réception : les clics se perdent et les chronos se réinitialisent.
Chaque module garde une signature et sort tôt (`controlsSignature`,
`dataset.questionId`, `state.renderedKey`). **La signature doit inclure le
`kind` de l'activité** : sans ça, un premier rendu avant l'arrivée des
résultats (kind encore inconnu) reste figé et le bouton « Reveal » persiste
à tort sur un nuage de mots.

Pour une bulle de nuage de mots : ne **jamais** fixer `height` en JS (même
`"0px"`) sur un élément qui a `aspect-ratio: 1/1` en CSS — un `height` inline
explicite gagne toujours sur `aspect-ratio` et fige la bulle en ellipse. Ne
faire varier que `width`, laisser la hauteur se déduire.

Attention aussi : dans un `QuestionResults`, l'identifiant est `question_id`,
pas `id`.

## Cache navigateur en développement

`StaticFiles` ne pose pas de `Cache-Control` par défaut : un navigateur peut
garder une vieille version de `deck.js`/`reveal.js` en heuristic caching même
après un F5, sans jamais revalider — `--reload` recharge le serveur, pas le
cache du navigateur. Un middleware dans `main.py` force `Cache-Control:
no-cache` sur `/deck`, `/app`, `/static` pour que le navigateur revalide
toujours via ETag. En cas de doute pendant une répétition : vider le cache du
navigateur ou ouvrir un onglet privé.

## Navigation dans une activité

`next`/`prev` sont de la navigation pure : le statut obtenu dépend de la
question visée (vierge → `open`, déjà répondue → `closed`), pas du sens.
`reset-question` efface une seule question, rend les points de quiz, et
incrémente le `question_token` — c'est ce jeton qui fait oublier aux
téléphones qu'ils avaient répondu. Une simple réouverture ne le change pas.

## Contraintes de contenu (non négociables)

- **Une seule slide** sur ce qui a été fait pendant le stage.
- Le focus est sur la **masterclass Companions** et le **prompting playbook**.
- **Rien sur Touchless** : ni critique, ni recommandation.
- Contenu et interface **en anglais** (public L'Oréal, réunion d'équipe).

## État

Contenu final livré (22 slides, 43 tests passent, parcours complet testé au
navigateur) : parcours perso, achievements, masterclass Companions (avec vraies
captures d'écran dans `frontend_main/img/`), 5 tips de prompting (dont un
schéma SVG fait main sur la négation dans les prompts), 2 nuages de mots, 2 quiz
et un podium partagé. Sources du contenu : `_content_unorganized/` (docs
internes L'Oréal fournis par l'utilisateur — non versionnées dans le contenu
final, juste la matière première).

Détails dans [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
