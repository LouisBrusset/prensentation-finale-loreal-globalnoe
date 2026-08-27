/* ---------------------------------------------------------------------------
 * Rendu des résultats en direct sur les slides d'activité.
 * Aucune librairie : des <div> et une transition CSS sur la largeur suffisent.
 * ------------------------------------------------------------------------- */
(function () {
  const PALETTE = ["#c9a227", "#8ecae6", "#e07a5f", "#81b29a", "#b8b8ff", "#f4a261"];

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  /**
   * Dessine une question et ses barres.
   * @param {HTMLElement} container  la div [data-role="live"] de la slide
   * @param {object} question        un élément de ActivityResults.questions
   * @param {object} ctx             { status, index, total, answers }
   */
  function renderQuestion(container, question, ctx) {
    if (!question) {
      container.innerHTML = "";
      container.appendChild(el("p", "live-empty", "Not open yet."));
      return;
    }

    // Même question qu'au rendu précédent : on met à jour les valeurs en place
    // au lieu de tout reconstruire. Sans ça, les barres repartaient de zéro à
    // chaque réponse reçue et la transition CSS ne jouait jamais.
    // Attention : l'identifiant d'un QuestionResults est `question_id`, pas `id`.
    if (container.dataset.questionId === question.question_id) {
      updateQuestion(container, question, ctx);
      return;
    }
    container.dataset.questionId = question.question_id;
    container.innerHTML = "";

    const head = el("div", "live-head");
    head.appendChild(el("span", "live-step", `Question ${ctx.index + 1} / ${ctx.total}`));
    head.appendChild(el("span", `live-badge live-badge--${ctx.status}`, {
      idle: "closed",
      open: "voting open",
      closed: "voting closed",
      revealed: "answer revealed",
    }[ctx.status] || ctx.status));
    head.appendChild(el("span", "live-count", `${question.total_answers} answers`));
    container.appendChild(head);

    container.appendChild(el("h3", "live-question", question.question_text));

    const revealed = ctx.status === "revealed";
    const list = el("div", "bars");

    question.buckets.forEach((bucket, i) => {
      const row = el("div", "bar-row");
      row.dataset.optionId = bucket.option_id;
      if (revealed && question.correct_option_id) {
        row.classList.add(
          bucket.option_id === question.correct_option_id ? "bar-row--correct" : "bar-row--wrong"
        );
      }

      const label = el("div", "bar-label");
      label.appendChild(el("span", "bar-text", bucket.label));
      label.appendChild(el("span", "bar-value", `${bucket.pct}%  (${bucket.count})`));

      const track = el("div", "bar-track");
      const fill = el("div", "bar-fill");
      // Largeur posée au frame suivant : une transition CSS ne joue pas sur un
      // élément qui naît déjà à sa largeur finale.
      fill.style.width = "0%";
      fill.style.background = PALETTE[i % PALETTE.length];
      requestAnimationFrame(() => {
        fill.style.width = `${bucket.pct}%`;
      });
      track.appendChild(fill);

      row.appendChild(label);
      row.appendChild(track);
      list.appendChild(row);
    });

    container.appendChild(list);
  }

  /** Même question : on ne touche qu'aux chiffres, aux largeurs et au statut. */
  function updateQuestion(container, question, ctx) {
    const badge = container.querySelector(".live-badge");
    if (badge) {
      badge.className = `live-badge live-badge--${ctx.status}`;
      badge.textContent =
        {
          idle: "closed",
          open: "voting open",
          closed: "voting closed",
          revealed: "answer revealed",
        }[ctx.status] || ctx.status;
    }

    const count = container.querySelector(".live-count");
    if (count) count.textContent = `${question.total_answers} answers`;

    const revealed = ctx.status === "revealed";
    question.buckets.forEach((bucket) => {
      const row = container.querySelector(`.bar-row[data-option-id="${bucket.option_id}"]`);
      if (!row) return;

      row.classList.toggle(
        "bar-row--correct",
        revealed && bucket.option_id === question.correct_option_id
      );
      row.classList.toggle(
        "bar-row--wrong",
        revealed && Boolean(question.correct_option_id) &&
          bucket.option_id !== question.correct_option_id
      );

      const value = row.querySelector(".bar-value");
      if (value) value.textContent = `${bucket.pct}%  (${bucket.count})`;

      const fill = row.querySelector(".bar-fill");
      if (fill) fill.style.width = `${bucket.pct}%`;
    });
  }

  function renderLeaderboard(entries) {
    const list = document.getElementById("leaderboard-list");
    if (!list) return;
    list.innerHTML = "";
    if (!entries || entries.length === 0) {
      list.appendChild(el("li", "empty", "waiting..."));
      return;
    }
    entries.slice(0, 8).forEach((entry) => {
      const item = el("li", "lb-row");
      item.appendChild(el("span", "lb-rank", `#${entry.rank}`));
      item.appendChild(el("span", "lb-emoji", entry.emoji || ""));
      item.appendChild(el("span", "lb-name", entry.nickname));
      item.appendChild(el("span", "lb-score", String(entry.score)));
      list.appendChild(item);
    });
  }

  window.FPLive = { renderQuestion, renderLeaderboard };
})();
