/* ---------------------------------------------------------------------------
 * Live word cloud: each submitted word becomes a bubble, sized by how often
 * it was said. No charting library — a hand-rolled spiral bubble-packing
 * layout (the same idea d3-cloud/BubbleChart use): try positions along an
 * outward spiral from the center, place at the first spot that doesn't
 * overlap an already-placed bubble.
 *
 * Bubbles are keyed by the normalized word so a bubble that grows keeps its
 * DOM node — updates animate (size, position) instead of the whole cloud
 * flashing and rebuilding on every submission, which arrives multiple times
 * a second while the room is typing.
 * ------------------------------------------------------------------------- */
(function () {
  const PALETTE = ["#c9a227", "#8ecae6", "#e07a5f", "#81b29a", "#b8b8ff", "#f4a261", "#ff9fb2"];

  // Stage is a 0-1000 x 0-620 virtual canvas, scaled to fit via viewBox-like
  // percentage positioning so it works at any slide size.
  const STAGE_W = 1000;
  const STAGE_H = 620;
  const R_MIN = 34;
  const R_MAX = 128;

  function el(tag, className) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    return node;
  }

  /** Greedy spiral packing: returns [{key, r, x, y}] for the given words. */
  function pack(words) {
    const maxCount = Math.max(1, ...words.map((w) => w.count));
    const placed = [];

    words.forEach((word) => {
      const r = R_MIN + (R_MAX - R_MIN) * Math.sqrt(word.count / maxCount);
      const cx = STAGE_W / 2;
      const cy = STAGE_H / 2;

      let x = cx;
      let y = cy;
      let angle = 0;
      let radius = 0;
      const step = 5.5;
      const angleStep = 0.38;

      for (let attempt = 0; attempt < 2200; attempt++) {
        const fits =
          x - r > 4 &&
          x + r < STAGE_W - 4 &&
          y - r > 4 &&
          y + r < STAGE_H - 4 &&
          placed.every((p) => {
            const dx = p.x - x;
            const dy = p.y - y;
            return Math.hypot(dx, dy) >= p.r + r + 6;
          });
        if (fits) break;

        angle += angleStep;
        radius += step / (2 * Math.PI);
        x = cx + radius * Math.cos(angle) * 2.1;
        y = cy + radius * Math.sin(angle) * 1.35; // flatten to match the wide stage
      }

      placed.push({ key: word.key, label: word.label, count: word.count, r, x, y });
    });

    return placed;
  }

  /**
   * @param {HTMLElement} container  the slide's [data-role="live"] div
   * @param {object} question        a QuestionResults (buckets = the words)
   * @param {object} ctx             { status, index, total }
   */
  function render(container, question, ctx) {
    if (!question) {
      container.innerHTML = "";
      container.appendChild(Object.assign(el("p", "live-empty"), { textContent: "Not open yet." }));
      return;
    }

    let stage = container.querySelector(".wc-stage");
    let head = container.querySelector(".wc-head");
    if (!stage || container.dataset.questionId !== question.question_id) {
      container.innerHTML = "";
      container.dataset.questionId = question.question_id;

      head = el("div", "live-head wc-head");
      container.appendChild(head);

      container.appendChild(
        Object.assign(el("h3", "live-question"), { textContent: question.question_text })
      );

      stage = el("div", "wc-stage");
      container.appendChild(stage);
    }

    head.innerHTML = "";
    const step = el("span", "live-step");
    step.textContent = `Round ${ctx.index + 1} / ${ctx.total}`;
    const badge = el("span", `live-badge live-badge--${ctx.status}`);
    badge.textContent = { idle: "not started", open: "typing...", closed: "closed" }[ctx.status] || ctx.status;
    const count = el("span", "live-count");
    count.textContent = `${question.total_answers} people`;
    head.append(step, badge, count);

    const words = question.buckets.filter((b) => b.count > 0);
    if (words.length === 0) {
      stage.innerHTML = "";
      stage.appendChild(Object.assign(el("p", "wc-empty"), { textContent: "Waiting for the first words..." }));
      return;
    }
    const emptyNotice = stage.querySelector(".wc-empty");
    if (emptyNotice) emptyNotice.remove();

    const placed = pack(
      words.map((b) => ({ key: b.option_id, label: b.label, count: b.count }))
    );

    const seen = new Set();
    placed.forEach((word, i) => {
      seen.add(word.key);
      let bubble = stage.querySelector(`[data-key="${CSS.escape(word.key)}"]`);
      if (!bubble) {
        bubble = el("div", "wc-bubble");
        bubble.dataset.key = word.key;
        bubble.style.background = PALETTE[i % PALETTE.length];
        // Born at the center, invisible: it animates outward into place.
        // Height is never set explicitly — the CSS `aspect-ratio: 1 / 1` on
        // `.wc-bubble` derives it from `width` alone. Setting an inline
        // `height` here (even "0px") would pin it and `aspect-ratio` could
        // never override it again, squashing every bubble into an ellipse.
        bubble.style.left = "50%";
        bubble.style.top = "50%";
        bubble.style.width = "0px";
        stage.appendChild(bubble);
        bubble.appendChild(el("span", "wc-word"));
        bubble.appendChild(el("span", "wc-count"));
        requestAnimationFrame(() => applyPlacement(bubble, word));
      } else {
        applyPlacement(bubble, word);
      }
      bubble.querySelector(".wc-word").textContent = word.label;
      bubble.querySelector(".wc-count").textContent = word.count;
      bubble.style.fontSize = `${Math.max(0.72, word.r / 62)}rem`;
    });

    // A reset-question wipes the bucket entirely; drop bubbles for words that
    // are no longer present (only happens right after a reset, in practice).
    Array.from(stage.querySelectorAll(".wc-bubble")).forEach((node) => {
      if (!seen.has(node.dataset.key)) node.remove();
    });
  }

  function applyPlacement(bubble, word) {
    const leftPct = (word.x / STAGE_W) * 100;
    const topPct = (word.y / STAGE_H) * 100;
    const sizePct = (word.r * 2) / STAGE_W * 100;
    bubble.style.left = `${leftPct}%`;
    bubble.style.top = `${topPct}%`;
    bubble.style.width = `${sizePct}%`;
    bubble.style.transform = "translate(-50%, -50%)";
  }

  function clear(container) {
    container.innerHTML = "";
    delete container.dataset.questionId;
  }

  window.FPWordcloud = { render, clear };
})();
