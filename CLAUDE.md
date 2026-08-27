# final_presentation — contexte pour l'assistant

Présentation finale de stage, interactive : un deck HTML projeté + une app
participant ouverte au téléphone via QR code + un backend FastAPI qui agrège les
réponses en temps réel.

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
| Texte des slides | `frontend_main/index.html` |
| Questions des sondages et du quiz | `backend/app/data/content.py` |
| État de session, scoring, agrégations | `backend/app/state.py` |
| Contrat d'API | `backend/app/models.py` |
| Client HTTP + WebSocket | `frontend_main/js/api.js` (dupliqué dans `frontend_user/js/api.js` — reporter les modifs) |
| Barres de résultats | `frontend_main/js/live.js` |
| Triptyque du reveal + podium | `frontend_main/js/reveal.js` |

## Piège récurrent sur le front

`state` est diffusé à chaque réponse de la salle. Ne jamais reconstruire du DOM
à chaque réception : les clics se perdent et les chronos se réinitialisent.
Chaque module garde une signature et sort tôt (`controlsSignature`,
`dataset.questionId`, `state.renderedKey`). Voir `docs/ARCHITECTURE.md`.

Attention aussi : dans un `QuestionResults`, l'identifiant est `question_id`,
pas `id`.

## Contraintes de contenu (non négociables)

- **Une seule slide** sur ce qui a été fait pendant le stage.
- Le focus est sur les **recommandations d'usage de l'IA**.
- **Rien sur Touchless** : ni critique, ni recommandation.

## État

Squelette technique validé de bout en bout (22 tests passent, parcours complet
testé au navigateur). **Tout le contenu est du bouchon** et porte la classe CSS
`.placeholder` quand il reste à écrire.

Détails dans [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) et
[`docs/CONTENT_PLAN.md`](docs/CONTENT_PLAN.md).
