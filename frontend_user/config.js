/* ---------------------------------------------------------------------------
 * Configuration de l'app participant (frontend_user) — celle ouverte par le QR.
 *
 * En local : rien à changer.
 * En prod (Netlify) : l'URL du backend Render est en dur dans
 * `guessApiBase()` ci-dessous — c'est la seule ligne à toucher si le backend
 * change d'adresse.
 * ------------------------------------------------------------------------- */
(function () {
  const params = new URLSearchParams(location.search);

  // Port du backend en local. 8010 et non 8000 : sur cette machine, le port
  // 8000 est pris par des regles `netsh portproxy` (WSL) et refuse le bind.
  const API_PORT = "8010";

  function guessApiBase() {
    if (location.protocol === "file:") return `http://localhost:${API_PORT}`;

    // Page servie par le backend lui-même (/app) : même origine, quel que soit
    // le port réellement utilisé.
    if (location.pathname.startsWith("/app") || location.pathname.startsWith("/deck")) {
      return location.origin;
    }

    // Serveur statique local (make serve-user) : le backend tourne sur la
    // même machine, sur API_PORT.
    const isLocal = ["localhost", "127.0.0.1"].includes(location.hostname)
      || /^192\.168\.|^10\.|^172\.(1[6-9]|2\d|3[01])\./.test(location.hostname);
    if (isLocal) return `${location.protocol}//${location.hostname}:${API_PORT}`;

    // Netlify (production) : le backend vit sur Render.
    return "https://prensentation-finale-loreal-globalnoe.onrender.com";
  }

  window.FP_CONFIG = {
    API_BASE: params.get("api") || localStorage.getItem("fp_api_base") || guessApiBase(),
    // Pas de token admin ici : un téléphone ne doit rien pouvoir piloter.
    ADMIN_TOKEN: null,
    POLL_INTERVAL_MS: 2500,
  };

  if (params.get("api")) localStorage.setItem("fp_api_base", params.get("api"));
})();
