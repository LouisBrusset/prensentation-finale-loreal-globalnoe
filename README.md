# final_presentation

Présentation finale de stage, en trois morceaux :

| Morceau | Dossier | Rôle |
|---|---|---|
| **Deck présentateur** | `frontend_main/` | La présentation HTML projetée. Affiche les résultats en direct. |
| **App participant** | `frontend_user/` | Ouverte au téléphone via QR code. Sondages et mini-jeu. |
| **Backend** | `backend/` | FastAPI : stocke les réponses, agrège, pousse en temps réel (WebSocket). |

> **État actuel : squelette technique validé.** Tout le contenu (slides, questions,
> exemples de compagnons) est **du bouchon** et sert uniquement à prouver que la
> mécanique tient. Le vrai contenu se remplace dans `frontend_main/index.html` et
> `backend/app/data/content.py`, sans toucher au reste du code.

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
| `test` | Tests backend (22 tests de fumée) |
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
| `N` | Question suivante de l'activité |
| `S` | Injecter 25 faux participants (répétition) |
| `Z` | Remettre la session à zéro |
| `F` | Plein écran |
| `?` | Rappel des raccourcis |

Les slides marquées `data-activity` (3, 8 et 11) **ouvrent automatiquement**
le sondage ou le jeu correspondant sur les téléphones quand tu arrives dessus.

---

## Contenu bouchon en place

- **13 slides** dans `frontend_main/index.html`
- **Sondage 1** (slide 3) — 3 questions
- **Mini-jeu quiz** (slide 8) — 4 questions chronométrées, score à la Kahoot + classement
- **Sondage 2** (slide 11) — 3 questions
- **Podium final** (slide 13) — les 3 premiers avec leur emoji

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

**À la toute fin**, la slide 13 dresse le **podium** : les marches poussent depuis
le sol, 2 · 1 · 3, médailles et emojis.

Structure des slides conforme aux consignes de la réunion : une seule slide sur
« ce que j'ai fait », le reste centré sur les recommandations d'usage de l'IA et
la micro-masterclass compagnons. Rien sur Touchless.

Tout ce qui reste à écrire est surligné en doré dans le deck (classe CSS
`.placeholder`) : impossible de les rater à la relecture.

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
