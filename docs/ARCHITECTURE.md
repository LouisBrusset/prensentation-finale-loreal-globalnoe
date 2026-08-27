# Architecture

## Vue d'ensemble

```
   ┌──────────────────────┐              ┌──────────────────────┐
   │  frontend_main       │              │  frontend_user       │
   │  (deck projeté)      │              │  (téléphones)        │
   │  HTML/CSS/JS         │              │  HTML/CSS/JS         │
   └──────────┬───────────┘              └──────────┬───────────┘
              │ REST + WebSocket                    │ REST + WebSocket
              │ (rôle "deck", token admin)          │ (rôle "phone")
              └──────────────┬──────────────────────┘
                             ▼
                  ┌─────────────────────────┐
                  │  backend (FastAPI)      │
                  │  • état en mémoire      │
                  │  • agrégation résultats │
                  │  • scoring quiz         │
                  │  • génération QR code   │
                  └─────────────────────────┘
```

Un seul principe : **le deck décide, le backend arbitre, les téléphones obéissent.**

Quand le présentateur change de slide, le deck appelle l'API admin. Le backend
met à jour son état et le **pousse** à tout le monde par WebSocket. Les
téléphones ne font que refléter l'état reçu — ils ne décident jamais quel écran
afficher par eux-mêmes. C'est ce qui empêche la salle de se désynchroniser du
grand écran.

## Choix techniques et leurs raisons

### Pas de base de données

L'état vit dans `backend/app/state.py`, en RAM. Une présentation dure une heure ;
un redémarrage du serveur = une session repartie de zéro, ce qui est exactement
le comportement voulu. Si un jour il faut de la persistance (relire les résultats
après coup), `SessionStore` est la seule classe à remplacer.

**Conséquence à connaître :** si le backend redémarre pendant la présentation,
les participants doivent re-rejoindre. Leur pseudo est mémorisé dans le
`localStorage` du téléphone, mais leur identifiant serveur, lui, a disparu.

### WebSocket avec repli en polling

`frontend_*/js/api.js` ouvre une WebSocket sur `/ws?role=deck|phone`. Si elle ne
s'établit pas après 3 tentatives (proxy d'entreprise, wifi capricieux), le client
bascule tout seul sur un polling HTTP toutes les 2–2,5 s. Le voyant en haut à
gauche du deck indique le mode en cours :

| Voyant | Signification |
|---|---|
| vert | WebSocket, temps réel |
| doré | mode secours (polling) |
| rouge | backend injoignable |

C'est le seul endroit du projet qui mérite d'être testé sur le wifi de la salle
**avant** le jour J.

### Le contenu vit côté serveur

Les questions, options et bonnes réponses sont dans
`backend/app/data/content.py`. Le deck n'a que la mise en forme. Deux avantages :

1. la bonne réponse du quiz ne part jamais vers les téléphones avant le reveal
   (`Activity.public(reveal=False)` la retire) — un test le vérifie ;
2. corriger une faute de frappe dans une question ne demande pas de redéployer
   Netlify.

Le manifeste `SLIDES` fait le lien : chaque slide du deck porte un
`data-slide-id`, et celles qui portent aussi un `data-activity` ouvrent
automatiquement l'activité correspondante.

### Sécurité : un token partagé, et c'est tout

Les routes `/api/admin/*` exigent l'en-tête `X-Admin-Token`. La seule chose à
empêcher, c'est qu'un participant malin ferme un sondage depuis son téléphone.
Le token est en clair dans `frontend_main/config.js` — **ne déploie pas le deck
sur une URL publique devinable** avec le vrai token, ou change-le juste avant.

Aucune donnée personnelle n'est collectée : un pseudo choisi librement, rien
d'autre, et rien n'est écrit sur disque.

### Scoring du mini-jeu

`base × (0.5 + 0.5 × rapidité)`, la rapidité décroissant linéairement jusqu'à la
limite de temps de la question. Répondre juste tout de suite ≈ 1000 points ;
répondre juste au buzzer ≈ 500. Répondre faux : 0.

**Le temps est mesuré par le serveur**, entre `opened_at` (l'instant où le
présentateur ouvre la question, identique pour toute la salle) et l'arrivée de
la réponse. Le `elapsed_ms` envoyé par le téléphone est ignoré tant que
l'activité est ouverte ; il ne sert de repli que pour le seeder de démo.

C'est une correction, pas un raffinement : quand le chrono partait du téléphone,
chaque réponse d'un participant déclenchait un événement `state` qui re-rendait
la question chez les autres et **remettait leur chrono à zéro**. Résultat, plus
on répondait tard, plus on marquait de points. Trois tests verrouillent
maintenant le comportement, dont un où les clients mentent en annonçant
`elapsed_ms: 0`.

## Limites connues (assumées à ce stade)

- **Le compte à rebours affiché sur le téléphone** part de la réception de
  l'état, pas de `opened_at`. Quelqu'un qui rejoint en plein milieu d'une
  question voit donc un chrono plein. Sans effet sur le score, qui est calculé
  côté serveur — c'est purement cosmétique.
- **Pas de reprise d'identité après redémarrage du backend** (voir plus haut).
- **Une seule session à la fois.** Il n'y a pas de notion de « room » : tout le
  monde qui atteint l'URL rejoint la même présentation.

## Un piège à connaître si tu touches au front

Le serveur diffuse un événement `state` à **chaque réponse envoyée dans la
salle**. Tout ce qui écoute `state` est donc appelé plusieurs fois par seconde
pendant un vote. Reconstruire du DOM à chaque fois a deux conséquences vicieuses,
toutes deux rencontrées ici :

1. **Les clics se perdent.** Un bouton détruit entre le `mousedown` et le
   `mouseup` ne déclenche jamais son `click` — c'est ce qui faisait croire que
   « Question suivante » ne marchait pas.
2. **L'état local est réinitialisé** (chrono, sélection en cours).

D'où la règle appliquée dans `deck.js`, `live.js` et `app.js` : **ne redessiner
que sur un vrai changement**, et sinon mettre à jour les valeurs en place. Chaque
endroit garde une signature (`controlsSignature`, `dataset.questionId`,
`state.renderedKey`) et sort tôt si rien n'a bougé.

## Arborescence

```
presentation_finale_loreal/
├── backend/
│   ├── app/
│   │   ├── main.py           point d'entrée FastAPI, WebSocket, montages statiques
│   │   ├── config.py         variables FP_* (.env)
│   │   ├── models.py         schémas Pydantic = contrat d'API
│   │   ├── state.py          store en mémoire, scoring, agrégations, seeder
│   │   ├── realtime.py       gestionnaire de connexions WebSocket
│   │   ├── events.py         helpers de diffusion
│   │   ├── qrcodes.py        génération PNG
│   │   ├── data/content.py   ►► LE CONTENU final (22 slides, anglais)
│   │   └── routers/          public.py · admin.py · qr.py
│   └── tests/                43 tests (test_smoke, test_navigation, test_wordcloud)
├── frontend_main/            deck : index.html + css/ + config.js + img/ (captures reelles)
│                             js/ : api · deck · live (barres) · wordcloud (bulles) · reveal (triptyque + podium)
├── frontend_user/            app participant : idem (+ saisie de mots libres)
├── scripts/gen_qr.py         QR codes en ligne de commande
├── static/qr/                QR générés (non versionnés)
├── docs/                     cette documentation
├── _content_unorganized/     matiere premiere fournie par l'utilisateur (docs internes L'Oreal)
├── Makefile / make.{sh,ps1,cmd}  commandes de dev, un lanceur par shell
└── pyproject.toml            dépendances (uv)
```

`frontend_main/js/api.js` et `frontend_user/js/api.js` sont **volontairement
identiques**. Les deux front-ends sont déployés séparément et n'ont pas de
bundler ; dupliquer 120 lignes coûte moins cher qu'une étape de build. Si tu
modifies l'un, reporte dans l'autre.
