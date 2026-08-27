/* ---------------------------------------------------------------------------
 * Client API + temps réel.
 *
 * NB : ce fichier est volontairement dupliqué dans frontend_user/js/api.js.
 * Les deux front-ends sont déployés séparément sur Netlify et n'ont pas de
 * bundler ; une copie de 120 lignes coûte moins cher qu'une étape de build.
 * Si tu modifies l'un, pense à reporter dans l'autre.
 * ------------------------------------------------------------------------- */
(function () {
  const cfg = window.FP_CONFIG;
  const base = cfg.API_BASE.replace(/\/$/, "");

  async function request(method, path, body, opts = {}) {
    const headers = { "Content-Type": "application/json" };
    if (opts.admin) headers["X-Admin-Token"] = cfg.ADMIN_TOKEN;

    const response = await fetch(base + path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      throw new Error(`${method} ${path} -> ${response.status} ${detail}`);
    }
    return response.status === 204 ? null : response.json();
  }

  /**
   * Connexion temps réel avec deux filets de sécurité :
   *  - reconnexion automatique avec back-off (wifi de salle de réunion) ;
   *  - repli en polling HTTP si la WebSocket ne s'établit jamais (proxy strict).
   */
  function connect(role, handlers = {}) {
    let socket = null;
    let attempt = 0;
    let pollTimer = null;
    let closedByUs = false;

    const emit = (type, payload) => {
      if (typeof handlers[type] === "function") handlers[type](payload);
    };

    function startPolling() {
      if (pollTimer) return;
      emit("status", { online: false, mode: "polling" });
      pollTimer = setInterval(async () => {
        try {
          const state = await request("GET", "/api/session");
          emit("state", state);
          if (state.activity_id) {
            emit("results", await request("GET", `/api/results/${state.activity_id}`));
          }
        } catch (err) {
          emit("status", { online: false, mode: "offline", error: String(err) });
        }
      }, cfg.POLL_INTERVAL_MS || 2000);
    }

    function stopPolling() {
      if (pollTimer) clearInterval(pollTimer);
      pollTimer = null;
    }

    function open() {
      const wsUrl = base.replace(/^http/, "ws") + `/ws?role=${role}`;
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        attempt = 0;
        stopPolling();
        emit("status", { online: true, mode: "websocket" });
      };

      socket.onmessage = (event) => {
        if (event.data === "pong") return;
        try {
          const { type, payload } = JSON.parse(event.data);
          emit(type, payload);
        } catch (_) {
          /* message non JSON : on ignore */
        }
      };

      socket.onclose = () => {
        if (closedByUs) return;
        attempt += 1;
        emit("status", { online: false, mode: "reconnecting" });
        if (attempt >= 3) startPolling();
        setTimeout(open, Math.min(1000 * attempt, 8000));
      };

      socket.onerror = () => socket && socket.close();
    }

    open();
    const keepAlive = setInterval(() => {
      if (socket && socket.readyState === WebSocket.OPEN) socket.send("ping");
    }, 25000);

    return {
      close() {
        closedByUs = true;
        clearInterval(keepAlive);
        stopPolling();
        if (socket) socket.close();
      },
    };
  }

  window.FPApi = {
    base,
    get: (path) => request("GET", path),
    post: (path, body, opts) => request("POST", path, body, opts),
    admin: (path, body) => request("POST", path, body, { admin: true }),
    qrUrl: (size = 12) => `${base}/api/qr.png?box_size=${size}`,
    connect,
  };
})();
