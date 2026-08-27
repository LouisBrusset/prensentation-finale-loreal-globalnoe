# Plan de contenu

## Les consignes qui cadrent tout

Issues de la réunion de préparation :

1. **Une seule slide** sur ce que j'ai fait pendant le stage. Pas plus.
2. Le **focus** est mis sur les **recommandations d'usage de l'IA**.
3. **Aucune critique de Touchless**, et **aucune recommandation sur Touchless**.
4. Ne pas être long sur ce que j'ai accompli.

Et l'intention annoncée : le truc le moins ennuyeux possible — de l'interactif
façon Kahoot, l'énumération des techniques mises en place, et une
micro-masterclass compagnons avec des exemples concrets, pour donner le minimum
qui permet de se lancer.

## Structure actuelle (13 slides)

| # | Slide | Statut | À écrire |
|---|---|---|---|
| 1 | Titre | 🟡 bouchon | Titre définitif, date confirmée |
| 2 | Rejoignez la session | ✅ fonctionnel | rien (QR automatique) |
| 3 | **Sondage 1** — où en êtes-vous avec l'IA ? | 🟡 bouchon | 3 questions à réécrire |
| 4 | Ce que j'ai fait | 🟡 bouchon | 3 cartes courtes, **une seule slide** |
| 5 | Reco 1 — le contexte fait 80 % | 🟡 squelette | l'exemple avant/après, en vrai |
| 6 | Reco 2 — itérer | 🟡 squelette | un exemple réel en 3 tours |
| 7 | Reco 3 — vérifier | 🟡 squelette | une erreur crédible repérée à temps |
| 8 | **Mini-jeu** — vrai ou faux | 🟡 bouchon | 4 questions à réécrire |
| 9 | Anatomie d'un compagnon | 🟡 squelette | les 4 briques, expliquées |
| 10 | Trois compagnons construits | 🟡 bouchon | noms, problèmes résolus, gain |
| 11 | **Sondage 2** — et maintenant ? | 🟡 bouchon | 3 questions à réécrire |
| 12 | À retenir + Q&A | 🟡 squelette | les 3 phrases finales |
| 13 | Podium du mini-jeu | ✅ fonctionnel | rien (automatique) |

Le squelette respecte le ratio voulu : **1 slide de bilan contre 6 slides de
recommandations et de masterclass**.

## Où modifier quoi

| Ce que tu veux changer | Fichier |
|---|---|
| Le texte d'une slide | `frontend_main/index.html` |
| Une question de sondage / de quiz | `backend/app/data/content.py` |
| Ajouter une slide | `frontend_main/index.html` **et** la liste `SLIDES` de `content.py` |
| Lier une slide à un sondage | attribut `data-activity="poll-1"` sur la `<section>` |
| Les couleurs, la typo | `frontend_main/css/deck.css` (variables en haut du fichier) |

Toutes les zones à remplir portent la classe CSS `.placeholder` : elles
apparaissent **surlignées en doré** dans le deck. Quand il n'y a plus de doré à
l'écran, le contenu est complet.

## Règles pour ajouter une question

- Les `id` doivent rester uniques dans tout le fichier (`p1q1`, `p1q1a`, …).
- Un sondage (`kind="poll"`) n'a pas de `correct_option_id`.
- Une question de quiz **doit** en avoir un, sinon elle ne rapporte aucun point.
- `kind` vaut `single` (validation au clic), `multi` (bouton Valider) ou `scale`
  (traité comme un `single`, mais rendu comme une échelle).
- 4 options maximum sur mobile : au-delà, ça oblige à scroller pour voter.

## Pistes à trancher

- [ ] Garder 3 activités, ou en ajouter une (nuage de mots à l'ouverture ?)
- [ ] Le mini-jeu tombe-t-il au bon endroit (slide 8), ou plutôt en fin pour finir sur une note légère ?
- [ ] Faut-il un classement affiché en continu, ou seulement à la fin du jeu ?
- [ ] Combien de temps réel pour chaque sondage — 3 questions × ~45 s = 2–3 min pièce
- [ ] Prévoir une slide de secours si la salle a très peu de participants connectés
