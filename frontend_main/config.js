/* ---------------------------------------------------------------------------
 * Configuration du deck (frontend_main).
 *
 * En local : rien à changer, l'URL de l'API est devinée automatiquement.
 * En prod   : remplacer API_BASE par l'URL publique du backend
 *             (ex. "https://final-presentation.onrender.com").
 * ------------------------------------------------------------------------- */
(function () {
  const params = new URLSearchParams(location.search);

  // Port du backend en local. 8010 et non 8000 : sur cette machine, le port
  // 8000 est pris par des regles `netsh portproxy` (WSL) et refuse le bind.
  const API_PORT = "8010";

  function guessApiBase() {
    if (location.protocol === "file:") return `http://localhost:${API_PORT}`;

    // Page servie par le backend lui-même (/deck ou /app) : même origine,
    // quel que soit le port réellement utilisé.
    if (location.pathname.startsWith("/deck") || location.pathname.startsWith("/app")) {
      return location.origin;
    }

    // Serveur statique séparé (make serve-deck) : le backend est ailleurs.
    return `${location.protocol}//${location.hostname}:${API_PORT}`;
  }

  window.FP_CONFIG = {
    // Ordre de priorité : ?api=... > valeur mémorisée > devinette.
    API_BASE: params.get("api") || localStorage.getItem("fp_api_base") || guessApiBase(),

    // Doit correspondre à FP_ADMIN_TOKEN côté backend.
    ADMIN_TOKEN: params.get("token") || "loreal2026",

    // Ouvre/ferme automatiquement l'activité liée à la slide affichée.
    AUTO_OPEN_ACTIVITY: true,

    // Intervalle du repli en polling si la WebSocket ne s'établit pas (ms).
    POLL_INTERVAL_MS: 2000,
  };

  if (params.get("api")) localStorage.setItem("fp_api_base", params.get("api"));
})();
