# Images de la présentation

Dépose ici **tous** les visuels : captures d'écran de compagnons, schémas,
photos, logos. Peu importe l'organisation, je m'occupe de les optimiser et de
les copier dans `frontend_main/img/` au moment de construire les slides.

## Comment les référencer

Dans `_content/CONTENU.md`, **le nom du fichier suffit** — pas de chemin :

```
**Image :** compagnon-agenda.png
**Légende :** Le compagnon qui croise les agendas de l'équipe
```

## Formats et tailles

| Type de visuel | Format | Largeur utile |
|---|---|---|
| Capture d'écran | PNG | 1200 à 2000 px |
| Photo | JPG | 1600 à 2400 px |
| Schéma que tu as en vectoriel | SVG | peu importe |

Au-delà de 2400 px de large, c'est du poids pour rien : un vidéoprojecteur de
salle de réunion affiche rarement plus de 1920 px.

Sous Windows, `Win + Shift + S` capture une zone, puis colle dans Paint et
enregistre en PNG ici.

## ⚠️ Avant de mettre une capture d'écran interne

Le deck peut finir déployé sur Netlify pour être partagé après coup — et une URL
Netlify est **publique**. Une capture de L'OréalGPT, d'un outil interne ou d'une
conversation peut contenir des noms, des chiffres ou des projets qui n'ont rien à
faire sur le web.

Deux options :
- **recadrer ou flouter** ce qui est sensible avant de déposer le fichier ;
- me dire `**Image : ... (interne)**` — je marque alors la slide, et on garde le
  deck en local le jour J au lieu de le publier.

Dans le doute, recadre. C'est cinq secondes, et ça évite une mauvaise surprise.
