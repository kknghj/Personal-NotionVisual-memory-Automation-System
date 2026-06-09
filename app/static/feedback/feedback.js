/** Feedback UI MVP — vanilla JS */

const state = {
  recommendation: null,
  catalog: [],
};

const $ = (id) => document.getElementById(id);

function visualDisplay(v) {
  if (!v) return "—";
  if (v.type === "emoji") return v.value;
  return v.color ? `${v.value} (${v.color})` : v.value;
}

function setStatus(el, text, kind) {
  el.textContent = text || "";
  el.className = "status" + (kind ? ` ${kind}` : "");
}

async function loadCatalog() {
  const res = await fetch("/visuals/catalog");
  if (!res.ok) throw new Error("catalog load failed");
  const data = await res.json();
  state.catalog = data.items || [];
  const sel = $("catalog-select");
  sel.replaceChildren();
  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "— catalog에서 선택 —";
  sel.appendChild(placeholder);
  for (const item of state.catalog) {
    const opt = document.createElement("option");
    opt.value = JSON.stringify(item.visual);
    opt.textContent = `${visualDisplay(item.visual)} · ${item.label} (${item.candidate_id})`;
    sel.appendChild(opt);
  }
}

function renderRecommendation(data) {
  state.recommendation = data;
  $("result-section").classList.remove("hidden");
  $("action-section").classList.remove("hidden");

  const meta = $("recommendation-meta");
  meta.replaceChildren();
  const idLine = document.createElement("p");
  idLine.className = "candidate-meta";
  idLine.textContent = `recommendation_id: ${data.recommendation_id} · path: ${data.recommendation_path}`;
  meta.appendChild(idLine);

  const top = $("top-visual");
  top.replaceChildren();
  if (data.no_candidate) {
    const badge = document.createElement("span");
    badge.className = "badge-no-candidate";
    badge.textContent = "no_candidate";
    top.appendChild(badge);
    $("btn-accept").disabled = true;
  } else {
    $("btn-accept").disabled = false;
    if (data.visual) {
      const span = document.createElement("span");
      span.textContent = visualDisplay(data.visual);
      span.style.fontSize = "2rem";
      top.appendChild(span);
    }
  }

  $("recommend-reason").textContent = data.reason || "";

  const list = $("candidate-list");
  list.replaceChildren();
  if (!data.candidates || data.candidates.length === 0) {
    const li = document.createElement("li");
    li.textContent = data.no_candidate ? "후보 없음" : "(exact match — catalog ranking 생략)";
    list.appendChild(li);
  } else {
    for (const c of data.candidates) {
      const li = document.createElement("li");
      if (c.rank === 1) li.classList.add("is-top");
      const vis = document.createElement("span");
      vis.className = "candidate-visual";
      vis.textContent = visualDisplay(c.visual);
      li.appendChild(vis);
      const title = document.createElement("strong");
      title.textContent = `#${c.rank} ${c.label}`;
      li.appendChild(title);
      const metaEl = document.createElement("div");
      metaEl.className = "candidate-meta";
      metaEl.textContent = `${c.candidate_id} · score ${c.score} — ${c.summary_reason}`;
      li.appendChild(metaEl);
      list.appendChild(li);
    }
  }
}

async function runRecommend() {
  const title = $("title").value.trim();
  if (!title) {
    setStatus($("recommend-status"), "제목을 입력하세요.", "err");
    return;
  }
  setStatus($("recommend-status"), "추천 중…");
  setStatus($("feedback-status"), "");
  try {
    const res = await fetch("/recommend-icon", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus($("recommend-status"), `${res.status}: ${JSON.stringify(data)}`, "err");
      return;
    }
    renderRecommendation(data);
    setStatus($("recommend-status"), data.no_candidate ? "no_candidate (200)" : "추천 완료", "ok");
  } catch (err) {
    setStatus($("recommend-status"), String(err), "err");
  }
}

function currentTitle() {
  return $("title").value.trim();
}

function parseVisualFromOverride() {
  const catalogVal = $("catalog-select").value;
  if (catalogVal) {
    return JSON.parse(catalogVal);
  }
  const value = $("manual-value").value.trim();
  if (!value) return null;
  const type = $("manual-type").value;
  const colorRaw = $("manual-color").value.trim();
  const visual = { type, value };
  if (colorRaw) visual.color = colorRaw;
  return visual;
}

async function submitFeedback(payload) {
  setStatus($("feedback-status"), "저장 중…");
  try {
    const res = await fetch("/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      setStatus($("feedback-status"), `${res.status}: ${data.detail || JSON.stringify(data)}`, "err");
      return;
    }
    setStatus($("feedback-status"), `저장됨 (${data.feedback_type})`, "ok");
    await loadRecent();
  } catch (err) {
    setStatus($("feedback-status"), String(err), "err");
  }
}

async function acceptRecommendation() {
  const rec = state.recommendation;
  if (!rec || rec.no_candidate || !rec.visual) {
    setStatus($("feedback-status"), "accept할 추천이 없습니다.", "err");
    return;
  }
  await submitFeedback({
    recommendation_id: rec.recommendation_id,
    input_title: currentTitle(),
    feedback_type: "accepted",
    system_recommended_visual: rec.visual,
    final_selected_visual: rec.visual,
  });
}

async function recordNoCandidate() {
  const rec = state.recommendation;
  if (!rec) {
    setStatus($("feedback-status"), "먼저 추천을 실행하세요.", "err");
    return;
  }
  await submitFeedback({
    recommendation_id: rec.recommendation_id,
    input_title: currentTitle(),
    feedback_type: "no_candidate",
    system_recommended_visual: rec.visual || null,
    final_selected_visual: null,
    override_reason: rec.no_candidate ? "catalog_gap" : undefined,
    user_note: rec.no_candidate ? "시스템 no_candidate 확인" : "추천은 있었으나 적합 후보 없음으로 기록",
  });
}

async function saveOverride() {
  const rec = state.recommendation;
  if (!rec) {
    setStatus($("feedback-status"), "먼저 추천을 실행하세요.", "err");
    return;
  }
  const finalVisual = parseVisualFromOverride();
  if (!finalVisual) {
    setStatus($("feedback-status"), "override visual을 catalog 또는 직접 입력하세요.", "err");
    return;
  }
  const overrideReason = $("override-reason").value;
  if (!overrideReason) {
    setStatus($("feedback-status"), "correction reason을 선택하세요.", "err");
    return;
  }
  const userNote = $("user-note").value.trim();
  await submitFeedback({
    recommendation_id: rec.recommendation_id,
    input_title: currentTitle(),
    feedback_type: "override",
    system_recommended_visual: rec.visual || null,
    final_selected_visual: finalVisual,
    override_reason: overrideReason,
    user_note: userNote || undefined,
  });
}

async function loadRecent() {
  const tbody = $("recent-body");
  try {
    const res = await fetch("/feedback/recent?limit=20");
    const rows = await res.json();
    tbody.replaceChildren();
    if (!rows.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 5;
      td.className = "empty";
      td.textContent = "기록 없음";
      tr.appendChild(td);
      tbody.appendChild(tr);
      return;
    }
    for (const row of rows) {
      const tr = document.createElement("tr");
      const cells = [
        row.timestamp || "",
        row.input_title || "",
        row.feedback_type || "",
        `${visualDisplay(row.system_recommended_visual)} → ${visualDisplay(row.final_selected_visual)}`,
        [row.override_reason, row.user_note].filter(Boolean).join(" | "),
      ];
      for (const text of cells) {
        const td = document.createElement("td");
        td.textContent = text;
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
  } catch (err) {
    tbody.replaceChildren();
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 5;
    td.className = "empty";
    td.textContent = String(err);
    tr.appendChild(td);
    tbody.appendChild(tr);
  }
}

$("btn-recommend").addEventListener("click", runRecommend);
$("btn-accept").addEventListener("click", acceptRecommendation);
$("btn-no-candidate").addEventListener("click", recordNoCandidate);
$("btn-override").addEventListener("click", saveOverride);
$("btn-refresh-recent").addEventListener("click", loadRecent);

loadCatalog().catch(() => {});
loadRecent();
