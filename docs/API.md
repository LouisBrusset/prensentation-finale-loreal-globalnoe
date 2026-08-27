# API

Base locale : `http://localhost:8010`
Doc interactive auto-générée : `http://localhost:8010/docs`

## Public — appelé par le deck **et** par les téléphones

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/api/health` | Ping + nombre de participants et de sockets |
| `GET` | `/api/content` | Manifeste complet : slides, activités (sans les bonnes réponses) et `avatar_emojis` (la palette proposée au participant) |
| `GET` | `/api/session` | État courant : slide, activité ouverte, statut, compteurs |
| `POST` | `/api/participants/join` | `{ "nickname": "...", "emoji": "🦊" }` → participant + état ; `emoji` facultatif, sinon tiré au sort |
| `GET` | `/api/activities/{activity_id}` | Une activité ; la bonne réponse n'apparaît qu'après le reveal |
| `POST` | `/api/activities/{aid}/questions/{qid}/answer` | Envoie une réponse |
| `GET` | `/api/results/{activity_id}` | Résultats agrégés, question par question |
| `GET` | `/api/leaderboard?limit=10` | Classement du mini-jeu |
| `GET` | `/api/qr.png?url=...&box_size=12` | QR code PNG (défaut : `FP_PUBLIC_APP_URL`) |
| `GET` | `/api/join-url` | URLs publiques à afficher sous le QR |

### Envoyer une réponse

```http
POST /api/activities/poll-1/questions/p1q1/answer
Content-Type: application/json

{ "participant_id": "abc123", "option_ids": ["p1q1a"], "elapsed_ms": 4200 }
```

```json
{ "accepted": true, "reason": null, "awarded_points": 0, "total_score": 0 }
```

`accepted: false` avec une `reason` quand les votes sont fermés ou que le
participant a déjà répondu à cette question. Ce n'est **pas** une erreur HTTP :
le téléphone affiche simplement « trop tard ».

## Admin — réservé au deck

Toutes ces routes exigent l'en-tête `X-Admin-Token` (valeur : `FP_ADMIN_TOKEN`,
`loreal2026` par défaut). Sans lui : `403`.

| Méthode | Chemin | Corps | Rôle |
|---|---|---|---|
| `POST` | `/api/admin/activity/open` | `{activity_id, question_index}` | Ouvre les votes |
| `POST` | `/api/admin/activity/close` | `{}` | Ferme les votes |
| `POST` | `/api/admin/activity/reveal` | `{}` | Révèle la bonne réponse (quiz) |
| `POST` | `/api/admin/activity/next` | `{}` | Question suivante ; reste sur la dernière au bout. Sans effet ni erreur si rien n'est ouvert |
| `POST` | `/api/admin/activity/prev` | `{}` | Question précédente ; sans effet sur la première |
| `POST` | `/api/admin/activity/goto` | `{activity_id, question_index}` | Saute sur n'importe quelle question |
| `POST` | `/api/admin/activity/resume` | `{activity_id}` | Reprend l'activité là où elle en était |
| `POST` | `/api/admin/activity/reset-question` | `{}` | Efface les réponses de la seule question courante et rouvre les votes |
| `POST` | `/api/admin/activity/idle` | `{}` | Aucune activité en cours |
| `POST` | `/api/admin/slide` | `{slide_index}` | Synchronise la slide affichée |
| `POST` | `/api/admin/seed` | `{participants, answer_everything}` | Faux participants + réponses |
| `POST` | `/api/admin/reset` | `{}` | Session à zéro |

## WebSocket

```
ws://localhost:8010/ws?role=deck
ws://localhost:8010/ws?role=phone
```

À la connexion, le serveur envoie immédiatement l'état courant (et les résultats
si une activité est ouverte), pour que le client s'aligne sans attendre.

Chaque message est un objet `{ "type": ..., "payload": ... }` :

| `type` | `payload` | Émis quand |
|---|---|---|
| `state` | `SessionState` | Slide, activité, statut ou compteurs changent |
| `results` | `ActivityResults` | Une réponse arrive, ou une action admin |
| `leaderboard` | `LeaderboardEntry[]` | Une réponse de quiz est marquée |
| `participant_joined` | `{nickname, total}` | Quelqu'un rejoint |

Le client peut envoyer le texte `ping` (le serveur répond `pong`) pour garder la
connexion vivante à travers les proxys — `api.js` le fait toutes les 25 s.

## Champs qui servent à l'affichage

### `SessionState.elapsed_s`

Secondes écoulées depuis l'ouverture de la question, **mesurées par le serveur**
(0 dès que les votes sont fermés). Le téléphone en déduit son compte à rebours :
quelqu'un qui rejoint au milieu d'une question voit le même temps restant que le
reste de la salle, sans dépendre de l'horloge de son appareil.

### `ResultBucket.voters`

La liste `{nickname, emoji}` de ceux qui ont choisi cette option, **dans l'ordre
d'arrivée des réponses**. C'est ce qui alimente les deux rectangles de noms du
triptyque de reveal. Sur une question à choix multiples, une même personne
apparaît sous chacune des options qu'elle a cochées.

### `emoji`

Chaque participant en a un, choisi à l'inscription ou attribué au hasard parmi
`avatar_emojis`. Tant que la palette n'est pas épuisée, deux personnes n'ont pas
le même. Il est repris dans `voters`, dans le classement et sur le podium.

## Naviguer dans une activité

`next` et `prev` sont de la **navigation**, pas des commandes de vote. Le statut
qui en découle dépend de l'état de la question visée, pas du sens de navigation :

| Question visée | Statut obtenu | Ce que voit la salle |
|---|---|---|
| aucune réponse encore | `open` | la question, votes ouverts |
| déjà des réponses | `closed` | les résultats, votes fermés |

C'est ce qui permet de revenir commenter la question 1 sans rouvrir ses votes
par accident. Pour forcer, il reste `open` (touche `O`) et `reset-question`
(touche `X`).

Aucun bouclage : `next` bute sur la dernière question, `prev` sur la première.
Le retour au repos (`idle`) se fait en quittant la slide.

### `reset-question` et le `question_token`

Réinitialiser une question efface ses réponses, **rend les points de quiz**
correspondants, et incrémente un compteur interne. Ce compteur entre dans le
`question_token` renvoyé par `/api/session`.

Les téléphones mémorisent le jeton du tour auquel ils ont répondu. Quand il
change, ils oublient leur réponse et peuvent revoter. Une simple réouverture
(`open`) ne le change pas : ceux qui ont déjà voté restent bloqués, comme il se
doit.

## Statuts d'activité

```
idle ──open──► open ──close──► closed ──reveal──► revealed
                 ▲                                    │
                 └──────────── next ──────────────────┘
```

- `idle` — rien en cours, les téléphones affichent la salle d'attente
- `open` — les votes sont acceptés
- `closed` — plus de votes, les résultats restent affichés
- `revealed` — la bonne réponse est visible (quiz uniquement)
