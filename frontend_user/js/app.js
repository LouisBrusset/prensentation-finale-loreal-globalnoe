/* ---------------------------------------------------------------------------
 * App participant : suit l'état de session poussé par le backend et affiche
 * l'écran correspondant (attente / question / confirmation).
 *
 * Le téléphone ne décide de rien : il obéit à `state`. Ça évite toute
 * désynchronisation entre le grand écran et la salle.
 * ------------------------------------------------------------------------- */
(function () {
  const api = window.FPApi;

  const state = {
    participant: null,
    session: null,
    activity: null,      // contenu de l'activité courante (questions, options)
    selection: new Set(),
    pickedEmoji: null,   // null = le serveur en tire un au hasard
    answeredKey: null,   // "activityId:questionId" déjà répondu
    renderedKey: null,   // "activityId:questionId" actuellement à l'écran
    questionShownAt: 0,
    timerHandle: null,
  };

  const $ = (id) => document.getElementById(id);
  const screens = ["join", "wait", "question", "done"];

  function showScreen(name) {
    screens.forEach((s) => $(`screen-${s}`).classList.toggle("is-active", s === name));
  }

  // ------------------------------------------------------------------ //
  // Session : rejoindre (et se souvenir)
  // ------------------------------------------------------------------ //
  function remember(participant) {
    state.participant = participant;
    localStorage.setItem("fp_participant", JSON.stringify(participant));
    $("me").textContent = participant.nickname;
    $("me-emoji").textContent = participant.emoji || "";
  }

  // ------------------------------------------------------------------ //
  // Choix de l'emoji
  // ------------------------------------------------------------------ //
  async function buildEmojiPicker() {
    const grid = $("emoji-grid");
    let palette = [];
    try {
      palette = (await api.get("/api/content")).avatar_emojis || [];
    } catch (err) {
      console.warn("Palette d'emojis indisponible :", err);
      return; // le serveur en attribuera un au hasard, l'inscription marche quand même
    }

    grid.innerHTML = "";
    palette.forEach((emoji) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "emoji-choice";
      button.textContent = emoji;
      button.setAttribute("role", "radio");
      button.setAttribute("aria-checked", "false");
      button.setAttribute("aria-label", `Emoji ${emoji}`);
      button.onclick = () => {
        const already = state.pickedEmoji === emoji;
        state.pickedEmoji = already ? null : emoji;
        Array.from(grid.children).forEach((child) => {
          const on = !already && child === button;
          child.classList.toggle("is-picked", on);
          child.setAttribute("aria-checked", String(on));
        });
      };
      grid.appendChild(button);
    });
  }

  function restore() {
    try {
      const saved = JSON.parse(localStorage.getItem("fp_participant") || "null");
      if (saved && saved.id) {
        remember(saved);
        return true;
      }
    } catch (_) { /* stockage corrompu : on repart de zéro */ }
    return false;
  }

  $("join-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const nickname = $("nickname").value.trim();
    if (!nickname) return;

    const error = $("join-error");
    error.hidden = true;
    try {
      const data = await api.post("/api/participants/join", {
        nickname,
        emoji: state.pickedEmoji,
      });
      remember(data.participant);
      applyState(data.session);
    } catch (err) {
      error.textContent = "Impossible de joindre le serveur. Vérifiez le wifi puis réessayez.";
      error.hidden = false;
      console.warn(err);
    }
  });

  // ------------------------------------------------------------------ //
  // Rendu d'une question
  // ------------------------------------------------------------------ //
  async function loadActivity(activityId) {
    if (state.activity && state.activity.id === activityId) return state.activity;
    state.activity = await api.get(`/api/activities/${activityId}`);
    return state.activity;
  }

  function renderQuestion(activity, question, session) {
    const key = `${activity.id}:${question.id}`;
    if (state.answeredKey === key) {
      showScreen("done");
      return;
    }

    // `state` est diffusé à CHAQUE réponse envoyée dans la salle. Re-rendre ici
    // remettait le chrono à zéro et recréait les boutons sous le doigt du
    // participant : un tap pouvait être perdu, et le temps de réponse mesuré
    // repartait de la réponse du voisin — d'où des scores plus élevés pour les
    // plus lents. On ne redessine que sur un vrai changement de question.
    if (state.renderedKey === key) return;
    state.renderedKey = key;

    state.selection.clear();
    state.questionShownAt = Date.now();

    $("q-step").textContent =
      `Question ${session.question_index + 1} / ${activity.questions.length}`;
    $("q-text").textContent = question.text;
    $("q-hint").hidden = question.kind !== "multi";

    const host = $("q-options");
    host.innerHTML = "";
    question.options.forEach((option) => {
      const button = document.createElement("button");
      button.className = "option";
      button.type = "button";
      button.innerHTML =
        `${option.emoji ? `<span class="emoji">${option.emoji}</span>` : ""}<span>${option.label}</span>`;
      button.onclick = () => onPick(activity, question, option, button);
      host.appendChild(button);
    });

    // Le multi a besoin d'un bouton Valider ; le single valide au clic.
    $("q-submit").hidden = question.kind !== "multi";
    $("q-submit").onclick = () => submit(activity, question);

    // Un retardataire peut arriver alors que le temps est deja ecoule : dans ce
    // cas startTimer bascule sur l'ecran "temps ecoule" et on ne doit surtout
    // pas le recouvrir par l'ecran question.
    if (!startTimer(activity, question, session)) return;
    showScreen("question");
  }

  function onPick(activity, question, option, button) {
    if (question.kind === "multi") {
      if (state.selection.has(option.id)) state.selection.delete(option.id);
      else state.selection.add(option.id);
      button.classList.toggle("is-picked");
      return;
    }
    state.selection.clear();
    state.selection.add(option.id);
    Array.from($("q-options").children).forEach((c) => c.classList.remove("is-picked"));
    button.classList.add("is-picked");
    submit(activity, question);
  }

  async function submit(activity, question) {
    if (state.selection.size === 0) return;
    stopTimer();

    try {
      const result = await api.post(
        `/api/activities/${activity.id}/questions/${question.id}/answer`,
        {
          participant_id: state.participant.id,
          option_ids: Array.from(state.selection),
          elapsed_ms: Date.now() - state.questionShownAt,
        }
      );

      state.answeredKey = `${activity.id}:${question.id}`;

      if (result.accepted) {
        $("done-title").textContent = "Réponse enregistrée";
        $("done-text").textContent = result.elapsed_ms
          ? `en ${(result.elapsed_ms / 1000).toFixed(1)} s — regardez le grand écran.`
          : "Regardez le grand écran.";
        if (result.awarded_points > 0) {
          $("done-points").textContent = `+${result.awarded_points} points`;
          $("done-points").hidden = false;
        } else {
          $("done-points").hidden = true;
        }
        $("score").textContent = result.total_score > 0 ? `${result.total_score} pts` : "";
      } else {
        $("done-title").textContent = "Trop tard !";
        $("done-text").textContent = result.reason || "";
        $("done-points").hidden = true;
      }
      showScreen("done");
    } catch (err) {
      console.warn(err);
    }
  }

  // ------------------------------------------------------------------ //
  // Chrono (quiz uniquement)
  // ------------------------------------------------------------------ //
  /** @returns {boolean} false si le temps est deja ecoule. */
  function startTimer(activity, question, session) {
    stopTimer();
    if (activity.kind !== "quiz") {
      $("q-timer").hidden = true;
      return true;
    }
    const timer = $("q-timer");
    timer.hidden = false;

    // `elapsed_s` vient du serveur : quelqu'un qui rejoint au milieu d'une
    // question voit le même décompte que le reste de la salle, sans dépendre
    // de l'horloge de son téléphone.
    const alreadyGone = Math.round((session && session.elapsed_s) || 0);
    let remaining = Math.max(0, question.time_limit_s - alreadyGone);
    timer.textContent = `${remaining}s`;
    if (remaining === 0) {
      timeUp();
      return false;
    }

    state.timerHandle = setInterval(() => {
      remaining -= 1;
      timer.textContent = `${remaining}s`;
      timer.classList.toggle("timer--urgent", remaining <= 5);
      if (remaining <= 0) timeUp();
    }, 1000);
    return true;
  }

  function timeUp() {
    stopTimer();
    $("done-title").textContent = "Temps écoulé";
    $("done-text").textContent = "Pas de points pour cette question.";
    $("done-points").hidden = true;
    showScreen("done");
  }

  function stopTimer() {
    if (state.timerHandle) clearInterval(state.timerHandle);
    state.timerHandle = null;
    $("q-timer").hidden = true;
    $("q-timer").classList.remove("timer--urgent");
  }

  // ------------------------------------------------------------------ //
  // Réaction à l'état poussé par le serveur
  // ------------------------------------------------------------------ //
  async function applyState(session) {
    state.session = session;

    if (!state.participant) {
      showScreen("join");
      return;
    }

    if (!session.activity_id || session.status === "idle") {
      stopTimer();
      state.renderedKey = null;
      $("wait-title").textContent = "C'est parti !";
      $("wait-text").textContent = "La prochaine question arrive sur grand écran.";
      showScreen("wait");
      return;
    }

    const activity = await loadActivity(session.activity_id);
    const question = activity.questions[session.question_index];
    if (!question) {
      showScreen("wait");
      return;
    }

    if (session.status === "open") {
      const key = `${activity.id}:${question.id}`;
      if (state.answeredKey === key) showScreen("done");
      else renderQuestion(activity, question, session);
      return;
    }

    // closed / revealed : plus rien à faire sur le téléphone.
    // renderedKey est libéré pour qu'une réouverture de la même question
    // redessine bien les boutons.
    stopTimer();
    state.renderedKey = null;
    $("wait-title").textContent = "Votes fermés";
    $("wait-text").textContent = "Les résultats sont sur le grand écran.";
    showScreen("wait");
  }

  // ------------------------------------------------------------------ //
  // Amorçage
  // ------------------------------------------------------------------ //
  api.connect("phone", {
    status({ online, mode }) {
      $("dot").className = `dot dot--${online ? "ok" : mode === "polling" ? "warn" : "ko"}`;
    },
    state(payload) {
      // Un changement d'activité invalide le cache local.
      if (state.session && state.session.activity_id !== payload.activity_id) {
        state.activity = null;
      }
      applyState(payload).catch(console.warn);
    },
  });

  if (restore()) {
    showScreen("wait");
  } else {
    showScreen("join");
    $("me").textContent = "non connecté";
    buildEmojiPicker();
  }
})();
