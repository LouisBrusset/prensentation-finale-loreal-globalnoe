# Runbook — le jour J

## La veille

- [ ] Réveiller le backend hébergé (Render s'endort après 15 min d'inactivité)
- [ ] Ouvrir le QR code avec un vrai téléphone, en 4G **et** en wifi
- [ ] Faire un passage complet des 12 slides avec `S` (faux participants) pour
      vérifier que tous les graphes s'affichent
- [ ] Vérifier qu'il ne reste plus aucun surlignage doré (`.placeholder`) dans le deck
- [ ] Prévoir un plan B : un PDF des slides exporté depuis le navigateur
      (Ctrl+P → « Enregistrer en PDF », en paysage)

## 15 minutes avant

- [ ] Lancer le backend : `./make.sh dev` (Git Bash) ou `.\make.ps1 dev` (PowerShell)
- [ ] Ouvrir le deck : <http://localhost:8010/deck> (le `?api=` n'est utile que si le backend est hebergé ailleurs)
- [ ] Voyant en haut à gauche **vert** = temps réel opérationnel
- [ ] `Z` pour remettre la session à zéro (efface les faux participants des répétitions)
- [ ] `F` pour le plein écran
- [ ] Couper les notifications de l'ordinateur
- [ ] Vérifier que la slide 2 affiche bien le QR **et** l'URL en clair dessous,
      et que cette URL est bien une **IP LAN** (`192.168.x.x`), pas `localhost`

## Pendant

| Moment | Geste |
|---|---|
| Slide 5 (join) | Laisser 60–90 s aux gens pour scanner. Le compteur sous le QR monte en direct. |
| Slide 6 (nuage de mots) | 2 tours (« Generative AI » puis « Companion »). `N` pour passer au second tour, les bulles poussent toutes seules — pas de reveal ici. |
| Slide 14 (quiz Companions) | `N` entre chaque question, `R` pour révéler avant de commenter. |
| Après chaque `R` | Le triptyque s'affiche : camembert, qui a voté quoi, top 5. Laisser 10–15 s, c'est le moment où la salle réagit. |
| Slide 15 (sondage prompting) | Pas de bonne réponse — sert à faire deviner la salle avant les tips. |
| Slide 20 (quiz IA) | Idem slide 14, contribue au même classement. |
| Slide 21 (podium) | Dernière étape avant la conclusion : le podium se dresse tout seul, cumulé sur les deux quiz. |

Le compteur « X réponses » en haut à droite du graphe dit quand tout le monde a
voté : c'est le signal pour passer à la suite, pas le chrono.

## Si ça casse

| Symptôme | Réflexe |
|---|---|
| Voyant doré (« mode secours ») | Rien à faire, ça marche, c'est juste 2 s plus lent |
| Voyant rouge | Le backend est tombé. Le relancer ; les slides continuent de défiler normalement, seuls les résultats live sont perdus |
| Voyant rouge **alors que le backend tourne** | Une vieille URL `?api=` est mémorisée dans le navigateur. Rouvrir le deck avec le bon `?api=…`, ou vider : `localStorage.removeItem('fp_api_base')` dans la console |
| Personne ne peut scanner | Dicter l'URL affichée sous le QR |
| Les téléphones restent bloqués en salle d'attente | Vérifier que le deck est bien sur une slide d'activité ; sinon `O` pour forcer l'ouverture |
| Quelqu'un voit « trop tard » alors que le sondage reprend | `X` réinitialise la question affichée : les réponses sont effacées et tout le monde peut revoter |
| Tu veux recommenter une question déjà passée | `P` y revient et réaffiche ses résultats, sans rouvrir les votes |
| Les résultats semblent figés | `F5` sur le deck : il se resynchronise sur l'état serveur, rien n'est perdu |
| Tout est cassé | Passer au PDF de secours et continuer sans l'interactif |

Le deck fonctionne **sans backend** : les slides s'affichent, seules les zones
de résultats restent vides. Aucune raison de s'arrêter.

## Après

- [ ] Récupérer les résultats avant d'éteindre : ils ne sont **pas** persistés

```bash
curl http://localhost:8010/api/results/poll-1 > resultats-sondage-1.json
```

```bash
curl http://localhost:8010/api/results/poll-2 > resultats-sondage-2.json
```

```bash
curl http://localhost:8010/api/leaderboard > classement.json
```
