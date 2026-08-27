# final_presentation

Présentation finale de stage, en trois morceaux :

| Morceau | Dossier | Rôle |
|---|---|---|
| **Deck présentateur** | `frontend_main/` | La présentation HTML projetée. Affiche les résultats en direct. |
| **App participant** | `frontend_user/` | Ouverte au téléphone via QR code. Sondages et mini-jeu. |
| **Backend** | `backend/` | FastAPI : stocke les réponses, agrège, pousse en temps réel (WebSocket). |

> **Contenu final, en anglais.** 22 slides : parcours perso, masterclass
> Companions (vraies captures d'écran L'Oréal GPT), 5 tips de prompting, 2
> nuages de mots interactifs, 2 quiz et un podium partagé. Le texte des slides
> vit dans `frontend_main/index.html`, les sondages/quiz/nuages de mots dans
> `backend/app/data/content.py`.

---

## Démarrage rapide

Prérequis : [uv](https://docs.astral.sh/uv/) et Python ≥ 3.11.

```bash
uv venv
```

```bash
uv sync --all-groups
```

```bash
uv run uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8010
```

Puis, dans le navigateur :

- **Deck** → <http://localhost:8010/deck>
- **App participant** → <http://localhost:8010/app>
- **Doc API interactive** → <http://localhost:8010/docs>

En local, le backend sert lui-même les deux front-ends : **un seul processus à
lancer**, pas trois serveurs à jongler pendant les répétitions.

### Avec les raccourcis

`make` n'est pas installé sur cette machine. Il y a donc **un lanceur par shell**,
tous avec les mêmes noms de cibles :

| Ton shell | Comment lancer |
|---|---|
| **Git Bash / MINGW64** (`louis@LAPTOP MINGW64 ~`) | `./make.sh dev` |
| **PowerShell** | `.\make.ps1 dev` |
| **cmd.exe** | `make dev` |
| N'importe lequel des trois | `./make.cmd dev` |

⚠️ `.\make.ps1` est de la syntaxe **PowerShell** : dans Git Bash elle échoue avec
`bash: .make.ps1: command not found`. Dans Git Bash, c'est **`./make.sh`**.

```bash
./make.sh install
```

```bash
./make.sh dev
```

| Cible | Effet |
|---|---|
| `install` | Crée `.venv/` et installe tout |
| `dev` | Lance l'API + les deux front-ends |
| `test` | Tests backend (33 tests) |
| `lint` / `format` | Style (ruff) |
| `ip` | IP LAN à donner aux téléphones |
| `qr-lan` | Génère le QR code vers cette IP |
| `seed` | Injecte 25 faux participants + leurs réponses |
| `reset` | Remet la session à zéro |
| `serve-user` | Sert `frontend_user` en statique pur (comme Netlify) |
| `clean` | Supprime `.venv`, caches et QR générés |

Le `Makefile` existe et fonctionne à l'identique si tu installes GNU Make
(`winget install GnuWin32.Make` ou `scoop install make`).

---

## Les ports, en un coup d'œil

C'est la source de confusion la plus probable, donc autant être explicite.

| Port | Qui l'ouvre | Quand |
|---|---|---|
| **8010** | `dev` / `back` | **Toujours.** L'API **et** les deux front-ends (`/deck`, `/app`) |
| 5173 | `serve-user` | Seulement si tu veux tester `frontend_user` en statique pur, comme sur Netlify |
| 5174 | `serve-deck` | Seulement pour tester le deck en statique pur |

Avec `dev`, **5173 et 5174 ne tournent pas** : `localhost:5173` donne un
`ERR_CONNECTION_REFUSED`, c'est normal. L'app participant est sur
<http://localhost:8010/app>.

---

## Tester avec de vrais téléphones (répétition en salle)

1. Lance `./make.sh dev` (il écoute déjà sur `0.0.0.0`).
2. Sur le deck, va sur la slide 2 : le QR code et l'URL affichée en dessous
   pointent **automatiquement vers l'IP LAN** de la machine, par ex.
   `192.168.1.8:8010/app`.
3. Sur le téléphone, **même wifi**, scanne — ou tape l'URL affichée.

Rien à configurer : le backend détecte son IP LAN au démarrage et construit le
QR avec. Il l'affiche aussi dans ses logs :

```
Depuis un telephone  -> http://192.168.1.8:8010/app
```

Si le pare-feu Windows demande une autorisation au premier lancement : accepte
pour les **réseaux privés**.

---

## Piloter le deck

| Touche | Action |
|---|---|
| `→` / `Espace` | Slide suivante |
| `←` | Slide précédente |
| `O` / `C` | Ouvrir / fermer les votes |
| `R` | Révéler la bonne réponse (mini-jeu) |
| `N` / `P` | Question suivante / précédente de l'activité |
| `X` | Réinitialiser la question affichée (efface ses réponses) |
| `S` | Injecter 25 faux participants (répétition) |
| `Z` | Remettre la session à zéro |
| `F` | Plein écran |
| `?` | Rappel des raccourcis |

Les slides marquées `data-activity` **ouvrent automatiquement** l'activité
correspondante sur les téléphones quand tu arrives dessus.

---

## Le contenu, en un coup d'œil

22 slides dans `frontend_main/index.html`, contenu final (anglais) :

| Slide(s) | Contenu |
|---|---|
| 1-4 | Titre, agenda, parcours perso, achievements (1 slide, comme demandé) |
| 5-6 | Connexion + **nuage de mots** (2 tours : « Generative AI » puis « Companion ») |
| 7-13 | Masterclass Companions — types, cycle de vie, anatomie, super-pouvoirs, validation, mes propres compagnons (vraies captures d'écran) |
| 14 | **Quiz** — 4 questions sur les Companions, avec podium partagé |
| 15-19 | Playbook de prompting — sondage d'ouverture + 5 tips (dont un schéma sur la négation dans les prompts) |
| 20 | **Quiz** — 4 questions de culture IA générale |
| 21-22 | Podium final, conclusion |

Les captures d'écran viennent de `_content_unorganized/` (docs internes L'Oréal
fournis par l'utilisateur) et sont recopiées, optimisées, dans `frontend_main/img/`.

## Ce qui se passe à l'écran

**En rejoignant**, chacun choisit un **emoji** parmi 24. Sans choix, le serveur en
attribue un libre. Cet emoji suit la personne partout : listes de votants,
classement, podium.

**Au moment de révéler** (touche `R`, sur un sondage comme sur le mini-jeu), les
barres laissent la place à un triptyque :

| Panneau | Contenu |
|---|---|
| Camembert | les pourcentages, parts qui poussent l'une après l'autre |
| Deux rectangles | qui a voté quoi — « ont trouvé » / « se sont trompés » sur le quiz, les deux options en tête sur un sondage |
| Top 5 | les meilleurs votants, les lignes glissent les unes par-dessus les autres quand l'ordre change |

**À la toute fin**, la slide podium dresse le classement : les marches poussent
depuis le sol, 2 · 1 · 3, médailles et emojis — cumulé sur les deux quiz.

**Le nuage de mots** (slides 5-6) suit un principe différent : pas d'options
fixées à l'avance, chaque participant tape 3 à 5 mots libres, le serveur les
normalise et les agrège, et le deck les affiche en bulles (taille ∝ fréquence)
qui poussent et se replacent en direct à mesure que les réponses arrivent.

Structure conforme aux consignes de la réunion : une seule slide sur « ce que
j'ai fait », le reste centré sur la masterclass Companions et le prompting.
Rien sur Touchless.

---

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — comment les trois morceaux se parlent, et pourquoi
- [`docs/API.md`](docs/API.md) — tous les endpoints
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — Netlify + hébergement du backend (**à lire, il y a un piège**)
- [`docs/RUNBOOK.md`](docs/RUNBOOK.md) — checklist du jour J
- [`docs/CONTENT_PLAN.md`](docs/CONTENT_PLAN.md) — plan de contenu et ce qu'il reste à écrire
- [`_content/`](_content/) — brouillons de contenu (markdown)

---

## Pourquoi le port 8010 et pas 8000

Sur cette machine, le port 8000 est **inutilisable** : des règles
`netsh portproxy` (installées pour WSL) le réservent, et le service *IP Helper*
le tient en exclusif. Une tentative de bind échoue avec :

```
ERROR: [WinError 10013] Une tentative d'accès à un socket de manière
interdite par ses autorisations d'accès a été tentée
```

Le projet écoute donc sur **8010** par défaut. Rien à faire, c'est déjà réglé
partout (backend, lanceurs, `config.js` des deux front-ends).

Pour vérifier l'état des règles :

```powershell
netsh interface portproxy show all
```

Si un jour tu veux vraiment récupérer le 8000 — **seulement si tu sais que ces
règles ne servent plus à ton WSL** :

```powershell
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0
```

Pour changer de port ponctuellement :

```bash
FP_PORT=8020 ./make.sh dev
```
