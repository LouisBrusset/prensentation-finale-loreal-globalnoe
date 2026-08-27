/* ---------------------------------------------------------------------------
 * Le triptyque du reveal.
 *
 * Affiché quand le présentateur révèle la réponse (statut `revealed`), pas à la
 * simple fermeture des votes : la fermeture laisse encore un instant pour
 * commenter les barres, le reveal est le moment "spectacle".
 *
 * Trois panneaux côte à côte :
 *   1. un camembert animé des pourcentages ;
 *   2. deux rectangles de noms (qui a voté quoi) ;
 *   3. un top 5 des meilleurs votants, qui se réordonne à la Kahoot.
 *
 * Aucune librairie : le camembert est un <svg> avec un stroke-dasharray animé,
 * le classement utilise la technique FLIP pour glisser les lignes les unes
 * par-dessus les autres.
 * ------------------------------------------------------------------------- */
(function () {
  const PALETTE = ["#c9a227", "#8ecae6", "#e07a5f", "#81b29a", "#b8b8ff", "#f4a261"];
  const NS = "http://www.w3.org/2000/svg";

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function svg(tag, attrs = {}) {
    const node = document.createElementNS(NS, tag);
    Object.entries(attrs).forEach(([k, v]) => node.setAttribute(k, v));
    return node;
  }

  // ------------------------------------------------------------------ //
  // 1. Camembert
  // ------------------------------------------------------------------ //
  /**
   * Chaque part est un cercle dont on ne peint qu'un arc, via stroke-dasharray.
   * Animer le dasharray de 0 à sa valeur fait "pousser" les parts dans le sens
   * horaire, l'une après l'autre.
   */
  function buildPie(buckets, correctOptionId) {
    const R = 60;              // rayon du tracé
    const STROKE = 52;         // épaisseur : un anneau épais lit mieux de loin
    const C = 2 * Math.PI * R;

    const wrap = el("div", "pie-wrap");
    const chart = svg("svg", {
      viewBox: "0 0 200 200",
      class: "pie",
      role: "img",
      "aria-label": "Answer breakdown",
    });

    // Piste de fond : évite un trou blanc si personne n'a voté.
    chart.appendChild(
      svg("circle", {
        cx: 100, cy: 100, r: R,
        fill: "none",
        stroke: "rgba(255,255,255,0.06)",
        "stroke-width": STROKE,
      })
    );

    const voted = buckets.filter((b) => b.count > 0);
    let offset = 0;

    voted.forEach((bucket, i) => {
      const share = bucket.pct / 100;
      const arc = svg("circle", {
        cx: 100, cy: 100, r: R,
        fill: "none",
        stroke: PALETTE[buckets.indexOf(bucket) % PALETTE.length],
        "stroke-width": STROKE,
        // On part de midi et on tourne dans le sens horaire.
        transform: "rotate(-90 100 100)",
        "stroke-dasharray": `0 ${C}`,
        "stroke-dashoffset": -offset * C,
      });
      if (correctOptionId && bucket.option_id === correctOptionId) {
        arc.setAttribute("class", "pie-slice pie-slice--correct");
      }
      chart.appendChild(arc);

      // Animation décalée : les parts apparaissent l'une après l'autre.
      setTimeout(() => {
        arc.style.transition = "stroke-dasharray 0.7s cubic-bezier(0.22, 1, 0.36, 1)";
        arc.setAttribute("stroke-dasharray", `${share * C} ${C}`);
      }, 120 + i * 180);

      offset += share;
    });

    wrap.appendChild(chart);

    // Légende avec les pourcentages.
    const legend = el("ul", "pie-legend");
    buckets.forEach((bucket, i) => {
      const item = el("li", "pie-legend-row");
      const dot = el("span", "pie-dot");
      dot.style.background = PALETTE[i % PALETTE.length];
      item.appendChild(dot);
      item.appendChild(el("span", "pie-legend-label", bucket.label));
      item.appendChild(el("span", "pie-legend-pct", `${bucket.pct}%`));
      if (correctOptionId && bucket.option_id === correctOptionId) {
        item.classList.add("is-correct");
      }
      legend.appendChild(item);
    });
    wrap.appendChild(legend);

    return wrap;
  }

  // ------------------------------------------------------------------ //
  // 2. Les deux rectangles de noms
  // ------------------------------------------------------------------ //
  /**
   * Quiz : "ont trouvé" contre "se sont trompés".
   * Sondage : les deux options les plus votées, face à face.
   */
  function splitVoters(question) {
    if (question.correct_option_id) {
      const right = question.buckets.find((b) => b.option_id === question.correct_option_id);
      const wrong = question.buckets.filter((b) => b.option_id !== question.correct_option_id);
      return [
        { title: "Got it right", tone: "ok", voters: (right && right.voters) || [] },
        { title: "Got it wrong", tone: "ko", voters: wrong.flatMap((b) => b.voters) },
      ];
    }

    const top = [...question.buckets].sort((a, b) => b.count - a.count).slice(0, 2);
    return top.map((bucket, i) => ({
      title: bucket.label,
      tone: i === 0 ? "lead" : "second",
      voters: bucket.voters,
    }));
  }

  function buildVoterPanels(question) {
    const grid = el("div", "voters-grid");

    splitVoters(question).forEach((panel, panelIndex) => {
      const box = el("div", `voters-box voters-box--${panel.tone}`);

      const head = el("div", "voters-head");
      head.appendChild(el("span", "voters-title", panel.title));
      head.appendChild(el("span", "voters-count", String(panel.voters.length)));
      box.appendChild(head);

      const list = el("div", "voters-list");
      if (panel.voters.length === 0) {
        list.appendChild(el("span", "voters-empty", "nobody yet"));
      }
      panel.voters.forEach((voter, i) => {
        const chip = el("span", "voter-chip");
        chip.appendChild(el("span", "voter-emoji", voter.emoji || ""));
        chip.appendChild(el("span", "voter-name", voter.nickname));
        // Apparition en cascade, un panneau puis l'autre.
        chip.style.animationDelay = `${panelIndex * 200 + i * 45}ms`;
        list.appendChild(chip);
      });
      box.appendChild(list);

      grid.appendChild(box);
    });

    return grid;
  }

  // ------------------------------------------------------------------ //
  // 3. Top 5 animé (technique FLIP)
  // ------------------------------------------------------------------ //
  /**
   * FLIP : on note la position de chaque ligne AVANT le changement d'ordre
   * (First), on réordonne le DOM (Last), on applique la translation inverse
   * (Invert) puis on la relâche (Play). Les lignes glissent les unes
   * par-dessus les autres au lieu de sauter.
   */
  function renderTop5(host, entries) {
    if (!host) return;
    let list = host.querySelector(".top5-list");
    if (!list) {
      host.innerHTML = "";
      host.appendChild(el("h4", "top5-title", "Top 5"));
      list = el("ol", "top5-list");
      host.appendChild(list);
    }

    const top = (entries || []).slice(0, 5);
    if (top.length === 0) {
      list.innerHTML = "";
      list.appendChild(el("li", "top5-empty", "no points yet"));
      return;
    }

    // First : positions actuelles.
    const before = new Map();
    Array.from(list.children).forEach((row) => {
      if (row.dataset.pid) before.set(row.dataset.pid, row.getBoundingClientRect().top);
    });

    list.innerHTML = "";
    top.forEach((entry) => {
      const row = el("li", "top5-row");
      row.dataset.pid = entry.participant_id;
      row.appendChild(el("span", "top5-rank", String(entry.rank)));
      row.appendChild(el("span", "top5-emoji", entry.emoji || ""));
      row.appendChild(el("span", "top5-name", entry.nickname));
      row.appendChild(el("span", "top5-score", String(entry.score)));
      list.appendChild(row);
    });

    // Last + Invert + Play.
    Array.from(list.children).forEach((row) => {
      const previous = before.get(row.dataset.pid);
      if (previous === undefined) {
        row.classList.add("top5-row--new");
        return;
      }
      const delta = previous - row.getBoundingClientRect().top;
      if (!delta) return;
      row.style.transform = `translateY(${delta}px)`;
      requestAnimationFrame(() => {
        row.style.transition = "transform 0.55s cubic-bezier(0.22, 1, 0.36, 1)";
        row.style.transform = "";
      });
    });
  }

  // ------------------------------------------------------------------ //
  // Assemblage
  // ------------------------------------------------------------------ //
  /**
   * @param {HTMLElement} host       la div [data-role="reveal"] de la slide
   * @param {object} question        un élément de ActivityResults.questions
   * @param {Array} leaderboard      classement courant
   */
  function render(host, question, leaderboard) {
    if (!question) return;

    // Rebâtir camembert et panneaux à chaque question, mais garder le top 5
    // vivant pour que l'animation FLIP ait un "avant" à comparer.
    // Attention : l'identifiant d'un QuestionResults est `question_id`, pas `id`.
    if (host.dataset.questionId !== question.question_id) {
      host.dataset.questionId = question.question_id;
      host.innerHTML = "";

      const grid = el("div", "reveal-grid");
      grid.appendChild(buildPie(question.buckets, question.correct_option_id));
      grid.appendChild(buildVoterPanels(question));
      grid.appendChild(el("div", "top5"));
      host.appendChild(grid);
    }

    renderTop5(host.querySelector(".top5"), leaderboard);
  }

  function clear(host) {
    host.innerHTML = "";
    delete host.dataset.questionId;
  }

  // ------------------------------------------------------------------ //
  // Podium final : les 3 premiers, à la Kahoot
  // ------------------------------------------------------------------ //
  // Ordre d'affichage 2 · 1 · 3 : la première marche est au centre, comme sur
  // un vrai podium. Hauteurs relatives des blocs, en rem.
  const PODIUM_STEPS = [
    { rank: 2, height: 7.5, medal: "🥈", delay: 150 },
    { rank: 1, height: 10.5, medal: "🥇", delay: 550 },
    { rank: 3, height: 5.5, medal: "🥉", delay: 350 },
  ];

  function renderPodium(entries) {
    const host = document.getElementById("podium");
    if (!host) return;

    const ranked = (entries || []).filter((e) => e.score > 0);
    if (ranked.length === 0) {
      host.innerHTML = "";
      host.appendChild(
        el("div", "podium-empty", "The podium fills in as soon as points are scored.")
      );
      return;
    }

    // Signature : on ne rejoue l'animation que si le podium a réellement changé.
    const signature = ranked
      .slice(0, 3)
      .map((e) => `${e.participant_id}:${e.score}`)
      .join("|");
    if (host.dataset.signature === signature) return;
    host.dataset.signature = signature;

    host.innerHTML = "";
    PODIUM_STEPS.forEach((step) => {
      const entry = ranked[step.rank - 1];
      const column = el("div", `podium-col podium-col--${step.rank}`);

      if (!entry) {
        column.classList.add("podium-col--vide");
        host.appendChild(column);
        return;
      }

      const head = el("div", "podium-head");
      head.appendChild(el("div", "podium-emoji", entry.emoji || ""));
      head.appendChild(el("div", "podium-name", entry.nickname));
      head.appendChild(el("div", "podium-score", `${entry.score} pts`));
      column.appendChild(head);

      const block = el("div", "podium-block");
      block.appendChild(el("span", "podium-medal", step.medal));
      block.appendChild(el("span", "podium-rank", String(step.rank)));
      // La marche pousse depuis le sol, la plus haute en dernier.
      block.style.height = `${step.height}rem`;
      block.style.animationDelay = `${step.delay}ms`;
      head.style.animationDelay = `${step.delay + 350}ms`;
      column.appendChild(block);

      host.appendChild(column);
    });
  }

  window.FPReveal = { render, clear, renderPodium };
})();
