# Contenu de la présentation — à remplir

Ce fichier est **la source unique** du contenu. Quand il est rempli, je le
transpose dans `frontend_main/index.html` (les slides) et
`backend/app/data/content.py` (les questions), sans que tu aies à toucher au code.

Écris en langage normal. Ne t'occupe ni des ids, ni du HTML, ni de la mise en
page : c'est mon travail. Les seules choses qui comptent pour moi sont les
**titres de section** (`## Slide 4 — …`) et les **étiquettes en gras**
(`**Type :**`, `**Bonne réponse :**`). Le reste, écris-le comme tu veux.

Si une slide te semble inutile, écris `SUPPRIMER` dessous. Si tu veux en ajouter
une, copie un bloc et numérote-la `Slide 6bis`.

---

## Contraintes (vidéoprojecteur + téléphone)

| Élément | Limite | Pourquoi |
|---|---|---|
| Titre de slide | ~60 caractères | au-delà, ça passe sur 3 lignes |
| Ligne de liste | ~90 caractères | une ligne se lit, un paragraphe non |
| Texte d'une question | ~100 caractères | doit tenir sur un écran de téléphone |
| Libellé d'une option | ~40 caractères | idem |
| Nombre d'options | 2 à 5, **4 idéalement** | au-delà, il faut scroller pour voter |

## Mises en page disponibles

Indique-la avec `**Format :**`. Si tu ne mets rien, je choisis.

- `listes` — 3 à 5 puces
- `cartes` — 3 ou 4 encadrés, chacun un titre court + une phrase
- `avant/après` — deux blocs comparés (idéal pour montrer un prompt raté puis réussi)
- `étapes` — une suite numérotée
- `citation` — une phrase en grand
- `texte` — paragraphe libre
- `image` — un visuel plein cadre
- `texte+image` — texte à gauche, visuel à droite
- `deux images` — deux visuels côte à côte (un avant / après en captures)

## Images

Dépose les fichiers dans **`_content/images/`** puis référence-les par leur
**nom seul**, sans chemin. Tu peux en mettre sur n'importe quelle slide :

```
**Image :** compagnon-agenda.png
**Légende :** Le compagnon qui croise les agendas de l'équipe
```

Plusieurs visuels sur une slide ? Numérote-les :

```
**Image 1 :** prompt-avant.png
**Légende 1 :** Le premier jet
**Image 2 :** prompt-apres.png
**Légende 2 :** Après trois itérations
```

La légende est facultative. Détails (formats, tailles, et **une mise en garde
sur les captures internes**) dans [`images/README.md`](images/README.md).

---

# PARTIE 1 — LES SLIDES

## Slide 1 — Titre

**Titre :**
**Sous-titre :**
**Date :**
**Image de fond :** (facultatif)

---

## Slide 2 — Rejoindre la session

Rien à écrire, le QR code et le compteur sont automatiques.
Dis-moi seulement si tu veux changer la phrase d'accroche actuelle
(« Sortez votre téléphone »).

**Accroche :**

---

## Slide 4 — Ce que j'ai fait pendant le stage

> Une seule slide, c'est la consigne. Ne développe pas, ça se dit à l'oral.

**Format :** cartes

**Carte 1 — titre :**
**Carte 1 — une phrase :**

**Carte 2 — titre :**
**Carte 2 — une phrase :**

**Carte 3 — titre :**
**Carte 3 — une phrase :**

---

## Slide 5 — Recommandation 1

<!-- EXEMPLE DE REMPLISSAGE — remplace tout, c'est juste pour montrer le format.

**Titre :** Le contexte fait 80 % du résultat
**Format :** avant/après

**Le principe, en une phrase :**
Un modèle ne devine pas pour qui tu écris ni ce que tu attends : dis-le.

**Points clés :**
- Dire qui tu es et pour qui tu écris
- Donner un exemple de la sortie attendue
- Coller la matière brute plutôt que la résumer

**Avant :**
« Résume ce document. »

**Après :**
« Tu écris pour un comité de direction qui a 5 minutes. Résume ce document en
5 puces, chacune avec un chiffre. Voici un exemple du ton attendu : … »

**Image :** prompt-avant-apres.png
**Légende :** Les deux réponses côte à côte

**Ce qu'on en retient :**
Le même modèle, le même document, deux résultats sans rapport.

FIN DE L'EXEMPLE -->

**Titre :**
**Format :**

**Le principe, en une phrase :**

**Points clés :**
-
-
-

**Avant :**

**Après :**

**Image :**
**Légende :**

**Ce qu'on en retient :**

---

## Slide 6 — Recommandation 2

**Titre :**
**Format :**

**Le principe, en une phrase :**

**Points clés :**
-
-
-

**Exemple vécu :**

**Image :**
**Légende :**

**Ce qu'on en retient :**

---

## Slide 7 — Recommandation 3

**Titre :**
**Format :**

**Le principe, en une phrase :**

**Points clés :**
-
-
-

**Exemple vécu :**

**Image :**
**Légende :**

**Ce qu'on en retient :**

---

> Besoin d'une 4ᵉ ou 5ᵉ recommandation ? Copie le bloc ci-dessus en
> `Slide 7bis`. C'est le cœur de la présentation, c'est là qu'il faut charger.

---

## Slide 9 — Anatomie d'un compagnon

**Titre :**
**Format :** cartes

**Brique 1 — nom :**
**Brique 1 — une phrase :**

**Brique 2 — nom :**
**Brique 2 — une phrase :**

**Brique 3 — nom :**
**Brique 3 — une phrase :**

**Brique 4 — nom :**
**Brique 4 — une phrase :**

**Image :** (une capture de l'écran de création d'un compagnon aide beaucoup ici)
**Légende :**

**La phrase à retenir :**

---

## Slide 10 — Les compagnons que j'ai construits

> Pour chacun : le problème d'abord, la solution ensuite. Le gain de temps
> chiffré, s'il existe, vaut tous les discours.

**Compagnon 1 — nom :**
**Compagnon 1 — le problème :**
**Compagnon 1 — ce qu'il fait :**
**Compagnon 1 — gain :**
**Compagnon 1 — image :**

**Compagnon 2 — nom :**
**Compagnon 2 — le problème :**
**Compagnon 2 — ce qu'il fait :**
**Compagnon 2 — gain :**
**Compagnon 2 — image :**

**Compagnon 3 — nom :**
**Compagnon 3 — le problème :**
**Compagnon 3 — ce qu'il fait :**
**Compagnon 3 — gain :**
**Compagnon 3 — image :**

---

## Slide 12 — À retenir + Q&A

**Titre :**

**Les 3 phrases finales :**
1.
2.
3.

**Phrase de clôture :**

---

# PARTIE 2 — LES SONDAGES ET LE MINI-JEU

Format d'une question :

```
### Q1
**Texte :** ta question ?
**Type :** unique | multiple | échelle
**Options :**
- Première option
- Deuxième option
- Troisième option
- Quatrième option
```

Pour le mini-jeu, deux lignes en plus :

```
**Bonne réponse :** Deuxième option
**Temps :** 20 s
```

`unique` = on valide au premier tap · `multiple` = cases à cocher + bouton
Valider · `échelle` = de 1 à 5, je m'occupe des libellés.

---

## Sondage 1 (slide 3) — connaître la salle

> Objectif : savoir à qui tu parles, et donner à la salle un point de
> comparaison sur elle-même. Ça marche mieux avec des questions dont le
> résultat est intéressant à commenter à voix haute.

### Q1
**Texte :**
**Type :**
**Options :**
-
-
-
-

### Q2
**Texte :**
**Type :**
**Options :**
-
-
-
-

### Q3
**Texte :**
**Type :**
**Options :**
-
-
-
-

---

## Mini-jeu (slide 8) — quiz chronométré

> Objectif : réveiller la salle au milieu. Chaque question devrait illustrer une
> de tes recommandations, pour que le jeu serve le propos.
> 4 questions, c'est le bon format — 5 minutes environ.

### Q1
**Texte :**
**Type :** unique
**Options :**
-
-
**Bonne réponse :**
**Temps :** 20 s
**Illustre la reco :**

### Q2
**Texte :**
**Type :** unique
**Options :**
-
-
**Bonne réponse :**
**Temps :** 20 s
**Illustre la reco :**

### Q3
**Texte :**
**Type :** unique
**Options :**
-
-
-
-
**Bonne réponse :**
**Temps :** 25 s
**Illustre la reco :**

### Q4
**Texte :**
**Type :** unique
**Options :**
-
-
-
-
**Bonne réponse :**
**Temps :** 25 s
**Illustre la reco :**

---

## Sondage 2 (slide 11) — engagement

> Objectif : finir sur une projection concrète, et récupérer ce que les gens
> veulent pour la suite.

### Q1
**Texte :**
**Type :**
**Options :**
-
-
-
-

### Q2
**Texte :**
**Type :**
**Options :**
-
-
-
-

### Q3
**Texte :**
**Type :**
**Options :**
-
-
-
-

---

# PARTIE 3 — DIVERS

**Emojis à proposer aux participants :** (laisse vide pour garder les 24 actuels)

**Titre de la session** (affiché en interne) :

**Choses à ne surtout pas dire :** (rappel : rien sur Touchless)

**Notes en vrac pour moi :**
