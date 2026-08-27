/* ---------------------------------------------------------------------------
 * Deck : navigation entre slides + pilotage de la session côté présentateur.
 *
 * Le deck est le "maître" : quand il change de slide, il prévient le backend,
 * et si la slide porte un data-activity il ouvre l'activité correspondante
 * sur les téléphones.
 * ------------------------------------------------------------------------- */
(function () {
  const slides = Array.from(document.querySelectorAll(".slide"));
  const api = window.FPApi;
  const cfg = window.FP_CONFIG;

  let index = 0;
  let session = null;
  let resultsCache = {}; // activity_id -> ActivityResults
  let leaderboardCache = []; // dernier classement reçu

  // ------------------------------------------------------------------ //
  // Navigation
  // ------------------------------------------------------------------ //
  function show(i, { notify = true } = {}) {
    index = Math.max(0, Math.min(i, slides.length - 1));
    slides.forEach((slide, n) => slide.classList.toggle("is-active", n === index));

    document.getElementById("hud-slide").textContent = `${index + 1} / ${slides.length}`;
    document.getElementById("progress-bar").style.width =
      `${((index + 1) / slides.length) * 100}%`;
    location.hash = slides[index].dataset.slideId;

    if (slides[index].dataset.slideId === "s21-podium") refreshLeaderboard();
    if (notify) scheduleSync();
  }

  // Traverser 5 slides à la flèche déclenchait 5 `slide` + 5 `open`/`idle`,
  // dont 4 pour des slides déjà quittées : les téléphones voyaient une activité
  // s'ouvrir et se refermer aussitôt. On ne prévient le backend que quand la
  // navigation s'est posée.
  let syncTimer = null;
  function scheduleSync() {
    clearTimeout(syncTimer);
    syncTimer = setTimeout(() => {
      api.admin("/api/admin/slide", { slide_index: index }).catch(() => {});
      syncActivityForSlide();
    }, 180);
  }

  /**
   * Le classement n'arrive spontanément qu'avec les réponses du quiz. Sur le
   * podium ou au moment d'un reveal de sondage, on le demande explicitement
   * pour ne pas afficher un panneau vide.
   */
  async function refreshLeaderboard() {
    try {
      leaderboardCache = await api.get("/api/leaderboard?limit=10");
      window.FPLive.renderLeaderboard(leaderboardCache);
      window.FPReveal.renderPodium(leaderboardCache);
    } catch (err) {
      console.warn("Classement indisponible :", err);
    }
  }

  /** Ouvre (ou referme) l'activité liée à la slide courante. */
  function syncActivityForSlide() {
    if (!cfg.AUTO_OPEN_ACTIVITY) return;
    const activityId = slides[index].dataset.activity;

    if (activityId) {
      const alreadyOpen = session && session.activity_id === activityId;
      if (!alreadyOpen) {
        // `resume` et non `open` : on repart de la question où la salle en
        // était, pas de la première. Quitter puis revenir sur la slide ne doit
        // pas relancer l'activité depuis le début.
        api.admin("/api/admin/activity/resume", { activity_id: activityId })
          .catch(console.warn);
      }
    } else if (session && session.activity_id) {
      api.admin("/api/admin/activity/idle", {}).catch(() => {});
    }
  }

  // ------------------------------------------------------------------ //
  // Rendu des slides d'activité
  // ------------------------------------------------------------------ //
  function activitySlide(activityId) {
    return slides.find((s) => s.dataset.activity === activityId);
  }

  /** Type reel de l'activite ("poll" | "quiz" | "wordcloud"), via les resultats deja recus. */
  function activityKind(activityId) {
    const results = resultsCache[activityId];
    return results ? results.kind : null;
  }

  function renderActive() {
    if (!session || !session.activity_id) return;
    const slide = activitySlide(session.activity_id);
    if (!slide) return;

    const results = resultsCache[session.activity_id];
    const live = slide.querySelector('[data-role="live"]');
    if (results && live) {
      const question = results.questions[session.question_index];
      const ctx = {
        status: session.status,
        index: session.question_index,
        total: results.questions.length,
      };
      if (results.kind === "wordcloud") {
        window.FPWordcloud.render(live, question, ctx);
      } else {
        window.FPLive.renderQuestion(live, question, ctx);
        renderReveal(slide, question);
      }
    }
    renderControls(slide);
  }

  /**
   * Le triptyque n'apparaît qu'au `reveal`, pas à la fermeture des votes :
   * fermer laisse un temps pour commenter les barres, révéler est le moment
   * "spectacle". N'existe pas pour un nuage de mots (pas de notion de reveal).
   */
  function renderReveal(slide, question) {
    const host = slide.querySelector('[data-role="reveal"]');
    if (!host) return;

    const revealing = session.status === "revealed";
    const justRevealed = revealing && !slide.classList.contains("is-revealing");
    slide.classList.toggle("is-revealing", revealing);

    if (revealing) {
      window.FPReveal.render(host, question, leaderboardCache);
      if (justRevealed && leaderboardCache.length === 0) refreshLeaderboard();
    } else {
      window.FPReveal.clear(host);
    }
  }

  /** Nombre de questions d'une activité, connu via les résultats déjà reçus. */
  function questionCount(activityId) {
    const results = resultsCache[activityId];
    return results ? results.questions.length : Infinity;
  }

  /**
   * Efface les réponses de la seule question affichée et rouvre les votes.
   * Sert quand on revient sur une activité laissée en plan : sans ça, ceux
   * qui avaient déjà répondu restent bloqués sur « too late ».
   */
  function resetCurrentQuestion() {
    const total = session ? session.answers_count : 0;
    const warning = total
      ? `Clear ${total} response(s) for this question and reopen it?`
      : "Reopen voting on this question?";
    if (!confirm(warning)) return Promise.resolve();
    return api.admin("/api/admin/activity/reset-question", {});
  }

  // Signature du dernier rendu des boutons, par slide.
  const controlsSignature = new WeakMap();

  function renderControls(slide) {
    const host = slide.querySelector('[data-role="controls"]');
    if (!host) return;
    const isOpen = session && session.status === "open";
    const activityId = slide.dataset.activity;
    const kind = activityKind(activityId);
    const isQuiz = kind === "quiz";
    const isWordcloud = kind === "wordcloud";

    // `state` est diffusé à CHAQUE réponse envoyée par un participant. Sans ce
    // garde-fou, les boutons étaient détruits et recréés plusieurs fois par
    // seconde : un clic tombant entre le mousedown et le mouseup n'atteignait
    // jamais le bouton, et « Next » semblait ne pas marcher.
    const signature = [
      activityId,
      kind, // null avant que les resultats arrivent, connu ensuite : doit invalider le cache
      session && session.question_index,
      session && session.status,
      session && session.question_token,
    ].join("|");
    if (controlsSignature.get(slide) === signature) return;
    controlsSignature.set(slide, signature);

    const questionIndex = (session && session.question_index) || 0;
    const total = questionCount(activityId);

    host.innerHTML = "";
    const buttons = [
      { key: "p", label: "◀ Previous", disabled: questionIndex === 0,
        run: () => api.admin("/api/admin/activity/prev", {}) },
      { key: "o", label: isOpen ? "Voting open" : "Open voting", disabled: isOpen,
        run: () => api.admin("/api/admin/activity/open",
          { activity_id: activityId, question_index: session.question_index }) },
      { key: "c", label: "Close", disabled: !isOpen,
        run: () => api.admin("/api/admin/activity/close", {}) },
      { key: "x", label: "Reset", run: resetCurrentQuestion },
    ];

    // Révéler vaut aussi pour un sondage : c'est ce qui déclenche le
    // triptyque (camembert + noms + top 5), pas seulement la bonne réponse.
    // N'a pas de sens pour un nuage de mots : la bulle EST déjà le live view.
    if (!isWordcloud) {
      buttons.push({
        key: "r",
        label: isQuiz ? "Reveal answer" : "Show results",
        disabled: session && session.status === "revealed",
        run: () => api.admin("/api/admin/activity/reveal", {}),
      });
    }

    buttons.push({
      key: "n", label: "Next ▶", disabled: questionIndex >= total - 1,
      run: () => api.admin("/api/admin/activity/next", {}),
    });

    buttons.forEach((spec) => {
      const button = document.createElement("button");
      button.className = "ctrl";
      button.innerHTML = `${spec.label} <kbd>${spec.key.toUpperCase()}</kbd>`;
      button.disabled = Boolean(spec.disabled);
      button.onclick = () => spec.run().catch(console.warn);
      host.appendChild(button);
    });
  }

  // ------------------------------------------------------------------ //
  // Temps réel
  // ------------------------------------------------------------------ //
  function setStatus({ online, mode }) {
    const dot = document.getElementById("hud-dot");
    dot.className = `hud-dot hud-dot--${online ? "ok" : mode === "polling" ? "warn" : "ko"}`;
    document.getElementById("hud-status").textContent = {
      websocket: "live",
      polling: "fallback mode (polling)",
      reconnecting: "reconnecting...",
      offline: "backend unreachable",
    }[mode] || mode;
  }

  api.connect("deck", {
    status: setStatus,
    state(payload) {
      session = payload;
      document.getElementById("hud-participants").textContent = payload.participants_count;
      const qrCount = document.getElementById("qr-count");
      if (qrCount) qrCount.textContent = payload.participants_count;
      renderActive();
    },
    results(payload) {
      resultsCache[payload.activity_id] = payload;
      renderActive();
    },
    leaderboard(payload) {
      leaderboardCache = payload;
      window.FPLive.renderLeaderboard(payload);
      window.FPReveal.renderPodium(payload);
      renderActive(); // le top 5 du triptyque se réordonne
    },
    participant_joined() {
      document.body.classList.add("pulse");
      setTimeout(() => document.body.classList.remove("pulse"), 400);
    },
  });

  // ------------------------------------------------------------------ //
  // Clavier
  // ------------------------------------------------------------------ //
  const keymap = {
    ArrowRight: () => show(index + 1),
    " ": () => show(index + 1),
    PageDown: () => show(index + 1),
    ArrowLeft: () => show(index - 1),
    PageUp: () => show(index - 1),
    Home: () => show(0),
    End: () => show(slides.length - 1),
    o: () => {
      const id = slides[index].dataset.activity;
      if (id) api.admin("/api/admin/activity/open",
        { activity_id: id, question_index: session ? session.question_index : 0 }).catch(console.warn);
    },
    // Ne pas avaler les erreurs ici : c'est ce qui rendait une touche muette
    // sans laisser la moindre trace dans la console.
    c: () => api.admin("/api/admin/activity/close", {}).catch(console.warn),
    p: () => api.admin("/api/admin/activity/prev", {}).catch(console.warn),
    x: () => resetCurrentQuestion().catch(console.warn),
    r: () => api.admin("/api/admin/activity/reveal", {}).catch(console.warn),
    n: () => api.admin("/api/admin/activity/next", {}).catch(console.warn),
    s: () => api.admin("/api/admin/seed", { participants: 25 }).catch(console.warn),
    z: () => {
      if (confirm("Reset the whole session (participants + answers)?")) {
        api.admin("/api/admin/reset", {}).catch(console.warn);
      }
    },
    f: () => {
      if (document.fullscreenElement) document.exitFullscreen();
      else document.documentElement.requestFullscreen();
    },
    "?": () => document.getElementById("help-dialog").showModal(),
  };

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (target instanceof Element && target.matches("input, textarea")) return;
    const handler = keymap[event.key] || keymap[event.key.toLowerCase()];
    if (handler) {
      event.preventDefault();
      handler();
    }
  });

  document.getElementById("nav-prev").onclick = () => show(index - 1);
  document.getElementById("nav-next").onclick = () => show(index + 1);
  document.getElementById("hud-help").onclick = () =>
    document.getElementById("help-dialog").showModal();

  // ------------------------------------------------------------------ //
  // Amorçage
  // ------------------------------------------------------------------ //
  (async function boot() {
    const qrImg = document.getElementById("qr-img");
    if (qrImg) qrImg.src = api.qrUrl(14);

    try {
      const urls = await api.get("/api/join-url");
      const target = document.getElementById("join-url");
      if (target) target.textContent = urls.app_url.replace(/^https?:\/\//, "");
    } catch (err) {
      console.warn("Backend injoignable au demarrage :", err);
    }

    // Reprise sur rechargement : #slide-id dans l'URL.
    const fromHash = slides.findIndex((s) => `#${s.dataset.slideId}` === location.hash);
    show(fromHash >= 0 ? fromHash : 0, { notify: false });
  })();
})();
