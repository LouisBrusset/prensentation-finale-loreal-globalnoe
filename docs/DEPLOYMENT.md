# Déploiement

## ⚠️ Le piège Netlify, à lire en premier

**Netlify ne peut pas héberger le backend.** Ce n'est pas une question de forfait :

- Netlify n'exécute que du **statique** + des **Functions serverless** (JS/TS et Go —
  pas de runtime Python) ;
- les Functions sont sans état et éphémères : elles ne peuvent ni garder les
  réponses en mémoire, ni maintenir une **WebSocket** ouverte.

Or le projet repose exactement sur ces deux choses.

Donc, la répartition qui fonctionne :

| Quoi | Où | Coût |
|---|---|---|
| `frontend_user` (app participant) | **Netlify** | gratuit |
| `frontend_main` (deck) | **local**, ou Netlify si tu veux le partager | gratuit |
| `backend` (FastAPI) | **ailleurs** — voir ci-dessous | gratuit |

### Où mettre le backend

| Option | Avantages | À savoir |
|---|---|---|
| **Render** (free web service) | Le plus simple, WebSocket supporté, déploiement depuis Git | S'endort après 15 min d'inactivité → **réveille-le 10 min avant** de commencer |
| **Hugging Face Spaces** (Docker) | Gratuit, tu as déjà un compte, WebSocket supporté | Space public par défaut |
| **Fly.io / Koyeb** | Pas de mise en veille agressive | Demande une carte à l'inscription |
| **Ton laptop** (`./make.sh dev`) | Zéro déploiement, zéro latence | Ne marche que si le wifi de la salle autorise les connexions entre appareils — **à tester avant** |

Le chemin le plus court pour le jour J : **backend sur Render + app participant
sur Netlify + deck en local**.

---

## 1. Déployer l'app participant sur Netlify

Aucun build : trois fichiers statiques.

### Par glisser-déposer (le plus rapide)

1. Va sur <https://app.netlify.com/drop>.
2. Dépose le dossier `frontend_user/`.
3. Note l'URL obtenue, par ex. `https://loreal-presentation.netlify.app`.

### Par CLI

```bash
npx netlify-cli deploy --dir frontend_user --prod
```

### Par Git

Dans les réglages du site : **Base directory** = `frontend_user`, pas de build
command. Le fichier `frontend_user/netlify.toml` fait le reste (redirects,
en-têtes, `config.js` jamais mis en cache).

### Puis : brancher l'URL du backend

Édite **une seule ligne** de `frontend_user/config.js` avant de déployer :

```js
API_BASE: params.get("api")
  || localStorage.getItem("fp_api_base")
  || "https://final-presentation.onrender.com",   // ← l'URL de ton backend
```

> Le HTTPS de Netlify impose que le backend soit **aussi en HTTPS**. Un backend
> en `http://` sera bloqué par le navigateur (mixed content). Render et HF Spaces
> fournissent le HTTPS automatiquement.

---

## 2. Déployer le backend sur Render

1. Pousse le projet sur GitHub.
2. Sur Render : **New → Web Service**, pointe sur le dépôt.
3. Réglages :

   | Champ | Valeur |
   |---|---|
   | Environment | `Python 3` |
   | Build command | `pip install -r requirements.txt` |
   | Start command | `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT` |

4. Variables d'environnement :

   ```
   FP_PUBLIC_APP_URL = https://loreal-presentation.netlify.app
   FP_PUBLIC_API_URL = https://final-presentation.onrender.com
   FP_CORS_ORIGINS   = https://loreal-presentation.netlify.app
   FP_ADMIN_TOKEN    = <un token que tu changes>
   ```

Render ne lit pas `pyproject.toml` : génère le `requirements.txt` avant de
pousser.

```bash
uv export --no-hashes --no-dev -o requirements.txt
```

### Alternative : Hugging Face Spaces (Docker)

`Dockerfile` minimal à mettre à la racine d'un Space :

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "7860"]
```

---

## 3. Le deck

Il reste **en local** le jour J : c'est lui qui pilote, et une panne réseau ne
doit pas te priver de tes slides.

```bash
./make.sh dev
```

Puis ouvre :

```
http://localhost:8010/deck?api=https://final-presentation.onrender.com&token=<ton-token>
```

L'URL `?api=` est mémorisée dans le `localStorage` : à faire une seule fois.

Si tu veux aussi publier le deck sur Netlify (pour le partager après coup),
déploie `frontend_main/` de la même façon — mais **change le token admin**
d'abord, il est en clair dans `config.js`.

---

## Checklist avant de déployer

- [ ] `FP_ADMIN_TOKEN` changé, différent de `loreal2026`
- [ ] `FP_CORS_ORIGINS` limité à l'URL Netlify (pas `*`)
- [ ] `API_BASE` de `frontend_user/config.js` pointe vers le backend en **https**
- [ ] `FP_PUBLIC_APP_URL` côté backend = l'URL Netlify → c'est elle qui finit
      dans le QR code
- [ ] QR code testé avec un vrai téléphone, sur un vrai réseau mobile
- [ ] Backend réveillé 10 min avant si tu es sur le forfait gratuit Render
