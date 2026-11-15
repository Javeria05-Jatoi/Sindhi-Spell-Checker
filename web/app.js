// web/app.js -- front end for the Sindhi Spell-Checker & Translator (no build step).
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const ARABIC = /[؀-ۿ]/;

const store = {
  get(key, fallback) { try { const v = localStorage.getItem(key); return v === null ? fallback : JSON.parse(v); } catch { return fallback; } },
  set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* private mode */ } },
};

async function api(path, body) {
  const opts = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
  return res.json();
}

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => (t.hidden = true), 1800);
}

async function copyText(text) {
  try { await navigator.clipboard.writeText(text); toast("Copied to clipboard"); }
  catch { toast("Couldn't copy, select the text and press Ctrl+C"); }
}

/* ---------------- splash ---------------- */
(function initSplash() {
  const splash = $("#splash");
  if (!splash) return;
  let i = 0;
  $$("[data-blocks]", splash).forEach((row) => {
    row.innerHTML = row.dataset.blocks.split(" ").map((word) =>
      `<span class="word">${[...word].map((ch) => `<span class="tile" style="--i:${i++}">${esc(ch)}</span>`).join("")}</span>`
    ).join("");
  });
  const close = () => {
    if (splash.classList.contains("out")) return;
    splash.classList.add("out");
    document.removeEventListener("keydown", close);
    setTimeout(() => splash.remove(), 500);
  };
  splash.addEventListener("click", close);
  document.addEventListener("keydown", close);
  setTimeout(close, 4200);
  $("#splash-enter").focus({ preventScroll: true });
})();

/* ---------------- theme ---------------- */
(function initTheme() {
  const saved = store.get("theme", null);
  if (saved) document.documentElement.dataset.theme = saved;
  $("#theme-toggle").addEventListener("click", () => {
    const dark = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    const next = dark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    store.set("theme", next);
  });
})();

/* ---------------- tabs / routing ---------------- */
function showView(name) {
  if (!$(`#view-${name}`)) name = "check";
  $$(".view").forEach((v) => (v.hidden = v.dataset.view !== name));
  $$(".tab").forEach((t) => t.setAttribute("aria-selected", String(t.dataset.view === name)));
  hidePopover();
  if (name === "about") loadMetrics();
}
$$(".tab").forEach((t) => t.addEventListener("click", () => { location.hash = t.dataset.view; }));
window.addEventListener("hashchange", () => showView(location.hash.slice(1).split("/")[0]));

/* ---------------- spell check ---------------- */
const input = $("#input");
const state = { tokens: [], ignored: new Set(store.get("ignored", [])), fixed: new Set(), checking: false, seq: 0 };
const SAMPLE = "سنڌي ٻوللي دنيا جي قديمم ٻولين مان هڪ آهي. مان روز ڪتاپ پڙهان ٿو ۽ اسڪولل وڃان ٿو. سنڌ جا ماڻهو مهمن نواز آهن ۽ پنهنجي ثقافط تي فخر ڪن ٿا.";

async function runCheck() {
  const text = input.value;
  store.set("draft", text);
  const seq = ++state.seq;
  if (!text.trim()) { state.tokens = []; renderReview(text); return; }
  $("#check-btn").innerHTML = '<span class="spinner"></span>Checking';
  try {
    const res = await api("/api/check", { text });
    if (seq !== state.seq) return; // a newer check is in flight
    state.tokens = res.tokens;
    renderReview(text);
  } catch (e) {
    toast("Check failed: " + e.message);
  } finally {
    if (seq === state.seq) $("#check-btn").textContent = "Check spelling";
  }
}

const isIssue = (t) => (!t.known || t.warning) && !state.ignored.has(t.token);
function issues() {
  return state.tokens.filter(isIssue);
}

function renderReview(text) {
  const review = $("#review");
  const chars = Array.from(text);
  if (!text.trim()) {
    review.innerHTML = $("#review").dataset.empty || review.innerHTML;
    $("#stats").innerHTML = "";
    $("#issues-card").hidden = true;
    $("#fixall-btn").disabled = true;
    return;
  }
  let html = "", last = 0;
  state.tokens.forEach((t, i) => {
    html += esc(chars.slice(last, t.start).join(""));
    const word = esc(chars.slice(t.start, t.end).join(""));
    if (isIssue(t)) html += `<span class="w-err${t.warning ? " w-warn" : ""}" data-i="${i}" tabindex="0" role="button"${t.warning ? ' title="Spelled correctly, but another word fits the sentence better"' : ""}>${word}</span>`;
    else if (state.fixed.has(`${t.start}:${t.token}`)) html += `<span class="w-fixed">${word}</span>`;
    else if (t.status === "corpus") html += `<span class="w-corpus" title="Common in Sindhi text, not in the lexicon">${word}</span>`;
    else html += word;
    last = t.end;
  });
  html += esc(chars.slice(last).join(""));
  review.innerHTML = html;

  const words = state.tokens.filter((t) => t.status !== "skip").length;
  const bad = issues();
  $("#stats").innerHTML = `<span class="chip">${words} words</span>` +
    (bad.length ? `<span class="chip bad">${bad.length} to review</span>` : `<span class="chip good">✓ All good</span>`);
  $("#fixall-btn").disabled = !bad.some((t) => !t.known && t.suggestions.length);
  renderIssues(bad);
}

function sugButtons(t, i) {
  if (!t.suggestions.length) return `<div class="no-sugs">No close words found.</div>`;
  return `<div class="sugs">${t.suggestions.map((s, k) => `
    <button class="sug" data-i="${i}" data-word="${esc(s.word)}" title="Replace with ${esc(s.word)}">
      <span class="rank">${k + 1}</span>
      <span class="sug-gloss">${esc(s.gloss || "")}</span>
      <span class="sug-word">${esc(s.word)}</span>
    </button>`).join("")}</div>`;
}

function renderIssues(bad) {
  const card = $("#issues-card");
  card.hidden = !bad.length;
  $("#issues-count").textContent = bad.length ? `${bad.length} word${bad.length > 1 ? "s" : ""} · top 3 closest` : "";
  $("#issues").innerHTML = bad.map((t) => {
    const i = state.tokens.indexOf(t);
    return `<li class="issue">
      <div class="issue-top">
        <div class="issue-links">
          <button class="ghost-btn" data-ignore="${i}" title="Ignore this word">Ignore</button>
          <button class="ghost-btn" data-add="${i}" title="Add to your dictionary">+ Add</button>
        </div>
        <span class="issue-word sd${t.warning ? " warn" : ""}">${esc(t.token)}</span>
      </div>
      ${t.warning ? `<div class="warn-note">Spelled correctly, but this fits the sentence better:</div>` : ""}
      ${sugButtons(t, i)}
    </li>`;
  }).join("");
}

function replaceToken(i, word) {
  const t = state.tokens[i];
  if (!t) return;
  const chars = Array.from(input.value);
  chars.splice(t.start, t.end - t.start, ...Array.from(word));
  const delta = Array.from(word).length - (t.end - t.start);
  input.value = chars.join("");
  // shift the remaining tokens so the review updates instantly, then re-check
  state.tokens = state.tokens.map((x, k) => {
    if (k === i) return { ...x, token: word, end: x.start + Array.from(word).length, known: true, status: "lexicon", suggestions: [], warning: undefined };
    if (k > i) return { ...x, start: x.start + delta, end: x.end + delta };
    return x;
  });
  state.fixed.add(`${t.start}:${word}`);
  hidePopover();
  renderReview(input.value);
}

function fixAll() {
  const bad = new Set(issues().filter((t) => !t.known && t.suggestions.length));
  if (!bad.size) return;
  // rebuild the text and token offsets in one left-to-right pass
  const chars = Array.from(input.value);
  const out = [];
  let last = 0, shift = 0;
  state.tokens = state.tokens.map((t) => {
    out.push(...chars.slice(last, t.start));
    last = t.end;
    if (!bad.has(t)) {
      out.push(...chars.slice(t.start, t.end));
      return { ...t, start: t.start + shift, end: t.end + shift };
    }
    const word = Array.from(t.suggestions[0].word);
    out.push(...word);
    const start = t.start + shift;
    shift += word.length - (t.end - t.start);
    state.fixed.add(`${start}:${word.join("")}`);
    return { ...t, token: word.join(""), start, end: start + word.length, known: true, status: "lexicon", suggestions: [] };
  });
  out.push(...chars.slice(last));
  input.value = out.join("");
  store.set("draft", input.value);
  hidePopover();
  renderReview(input.value);
  toast(`Fixed ${bad.size} word${bad.size === 1 ? "" : "s"}`);
}

function ignoreToken(i) {
  const t = state.tokens[i];
  state.ignored.add(t.token);
  store.set("ignored", [...state.ignored]);
  hidePopover();
  renderReview(input.value);
}

async function addToken(i) {
  const t = state.tokens[i];
  await api("/api/user-words", { word: t.token }).catch(() => null);
  t.known = true; t.status = "user";
  hidePopover();
  renderReview(input.value);
  toast(`Added “${t.token}” to your dictionary`);
}

/* popover for a clicked word */
function showPopover(anchor, i) {
  const t = state.tokens[i];
  const pop = $("#popover");
  $$(".w-err.active").forEach((el) => el.classList.remove("active"));
  anchor.classList.add("active");
  pop.innerHTML = `
    <div class="pop-title"><span>${t.warning ? "Fits the sentence better…" : "Did you mean…"}</span><span class="sd">${esc(t.token)}</span></div>
    ${sugButtons(t, i)}
    <div class="pop-foot">
      <button class="ghost-btn" data-ignore="${i}">Ignore</button>
      <button class="ghost-btn" data-add="${i}">+ Add word</button>
      <button class="ghost-btn" data-lookup="${esc(t.token)}">Look up</button>
    </div>`;
  pop.hidden = false;
  const r = anchor.getBoundingClientRect();
  const left = Math.min(Math.max(8, r.left + window.scrollX + r.width / 2 - 160), window.scrollX + document.documentElement.clientWidth - 328);
  pop.style.left = `${left}px`;
  pop.style.top = `${r.bottom + window.scrollY + 8}px`;
}
function hidePopover() {
  $("#popover").hidden = true;
  $$(".w-err.active").forEach((el) => el.classList.remove("active"));
}

document.addEventListener("click", (e) => {
  const err = e.target.closest(".w-err");
  if (err) { showPopover(err, +err.dataset.i); return; }
  const sug = e.target.closest(".sug");
  if (sug) { replaceToken(+sug.dataset.i, sug.dataset.word); return; }
  const ign = e.target.closest("[data-ignore]");
  if (ign) { ignoreToken(+ign.dataset.ignore); return; }
  const add = e.target.closest("[data-add]");
  if (add) { addToken(+add.dataset.add); return; }
  const look = e.target.closest("[data-lookup]");
  if (look) { hidePopover(); location.hash = "dictionary"; doLookup(look.dataset.lookup); return; }
  if (!e.target.closest("#popover")) hidePopover();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") { hidePopover(); $("#autocomplete").hidden = true; }
  if (e.key === "Enter" && e.target.classList?.contains("w-err")) showPopover(e.target, +e.target.dataset.i);
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter" && e.target === input) runCheck();
});

$("#review").dataset.empty = $("#review").innerHTML;
let liveTimer;
input.addEventListener("input", () => {
  state.fixed.clear();
  store.set("draft", input.value);
  if ($("#live-toggle").checked) { clearTimeout(liveTimer); liveTimer = setTimeout(runCheck, 500); }
});
$("#check-btn").addEventListener("click", runCheck);
$("#fixall-btn").addEventListener("click", fixAll);
$("#copy-btn").addEventListener("click", () => copyText(input.value));
$("#clear-btn").addEventListener("click", () => { input.value = ""; store.set("draft", ""); state.tokens = []; renderReview(""); input.focus(); });
$("#sample-btn").addEventListener("click", () => { input.value = SAMPLE; state.fixed.clear(); runCheck(); });

/* ---------------- dictionary ---------------- */
const searchInput = $("#search-input");
const acList = $("#autocomplete");
let acTimer, acIndex = -1;

function freqMeter(freq) {
  const level = freq >= 5000 ? 5 : freq >= 500 ? 4 : freq >= 50 ? 3 : freq >= 5 ? 2 : freq > 0 ? 1 : 0;
  const labels = ["not seen in corpus", "rare", "uncommon", "common", "very common", "everyday word"];
  return `<span class="freq-meter" title="${freq.toLocaleString()} uses in the corpus"><span class="bars">${[1, 2, 3, 4, 5].map((n) => `<i class="${n <= level ? "on" : ""}"></i>`).join("")}</span>${labels[level]}</span>`;
}

function entryCard(e, note = "") {
  const translations = e.translations.length
    ? `<div class="section-label">English</div><ol class="translations">${e.translations.map((t) => `<li>${esc(t)}</li>`).join("")}</ol>` : "";
  const meanings = e.meanings.length
    ? `<div class="section-label">Sindhi definition</div><ol class="meanings sd" dir="rtl" lang="sd">${e.meanings.map((m) => `<li>${esc(m)}</li>`).join("")}</ol>` : "";
  const forms = e.forms.filter((f) => f !== e.word);
  return `<article class="card entry">
    ${note}
    <div class="entry-head">
      <div class="badges">
        ${e.pos ? `<span class="badge">${esc(e.pos)}</span>` : ""}
        ${e.sources.map((s) => `<span class="badge red" dir="auto">${esc(s)}</span>`).join("")}
      </div>
      <div class="headword sd" dir="rtl" lang="sd">${esc(e.word)}</div>
    </div>
    <div class="entry-head">
      ${freqMeter(e.frequency || 0)}
      ${forms.length ? `<div class="forms" dir="rtl">${forms.map(esc).join(" · ")}</div>` : ""}
    </div>
    ${translations}${meanings}
    ${!translations && !meanings ? `<p class="muted">No definition recorded for this word.</p>` : ""}
  </article>`;
}

function resultList(items) {
  return `<div class="result-list">${items.map((e) => `
    <button class="result-item" data-word="${esc(e.word)}">
      <span class="ri-word">${esc(e.word)}</span>
      <span class="ri-gloss">${esc((e.translations[0] || "").slice(0, 80))}</span>
    </button>`).join("")}</div>`;
}

function pushRecent(q) {
  const recent = store.get("recent", []).filter((w) => w !== q);
  recent.unshift(q);
  store.set("recent", recent.slice(0, 10));
  renderRecent();
}
function renderRecent() {
  const recent = store.get("recent", []);
  $("#recent").innerHTML = recent.length
    ? `<span class="muted small" style="align-self:center">Recent:</span>` + recent.map((w) => `<button data-recent="${esc(w)}" dir="auto">${esc(w)}</button>`).join("") : "";
}

async function doLookup(q) {
  q = (q || "").trim();
  if (!q) return;
  searchInput.value = q;
  acList.hidden = true;
  const out = $("#dict-result");
  out.innerHTML = `<div class="card"><div class="skeleton"></div></div>`;
  try {
    const res = await api(`/api/lookup?q=${encodeURIComponent(q)}`);
    pushRecent(q);
    if (res.mode === "english") {
      out.innerHTML = res.results.length
        ? `<div class="card"><div class="card-head"><h2>Sindhi words for “${esc(q)}”</h2><span class="muted small">${res.results.length} found</span></div>${resultList(res.results)}</div>`
        : `<div class="card"><p class="muted">No Sindhi word has “${esc(q)}” in its English gloss.</p></div>`;
    } else if (res.entry) {
      out.innerHTML = entryCard(res.entry);
    } else if (res.base_form) {
      out.innerHTML = entryCard(res.base_form,
        `<div class="note"><span class="sd">${esc(q)}</span> looks like an inflected form of <b class="sd">${esc(res.base_form.word)}</b>.</div>`);
    } else {
      const sugs = res.suggestions;
      out.innerHTML = `<div class="card">
        <div class="card-head"><h2>${res.status === "corpus" ? "A common word, but not in the lexicon" : "Not in the dictionary"}</h2></div>
        ${sugs.length ? `<p class="muted">Closest words:</p>${resultList(sugs.map((s) => ({ word: s.word, translations: [s.gloss || ""] })))}` : `<p class="muted">No close words found.</p>`}
      </div>`;
    }
  } catch (e) {
    out.innerHTML = `<div class="card"><p class="muted">Lookup failed: ${esc(e.message)}</p></div>`;
  }
}

$("#search-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const active = $$("li", acList)[acIndex];
  doLookup(active && !acList.hidden ? active.dataset.word : searchInput.value);
});
searchInput.addEventListener("input", () => {
  clearTimeout(acTimer);
  const q = searchInput.value.trim();
  if (!q || !ARABIC.test(q)) { acList.hidden = true; return; }
  acTimer = setTimeout(async () => {
    const items = await api(`/api/autocomplete?prefix=${encodeURIComponent(q)}`).catch(() => []);
    acIndex = -1;
    acList.innerHTML = items.map((it) => `<li role="option" data-word="${esc(it.word)}"><span class="ac-gloss">${esc(it.gloss || "")}</span><span class="ac-word">${esc(it.word)}</span></li>`).join("");
    acList.hidden = !items.length;
  }, 150);
});
searchInput.addEventListener("keydown", (e) => {
  const items = $$("li", acList);
  if (acList.hidden || !items.length) return;
  if (e.key === "ArrowDown" || e.key === "ArrowUp") {
    e.preventDefault();
    acIndex = (acIndex + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
    items.forEach((li, k) => li.classList.toggle("active", k === acIndex));
  }
});
acList.addEventListener("click", (e) => { const li = e.target.closest("li"); if (li) doLookup(li.dataset.word); });
document.addEventListener("click", (e) => {
  const item = e.target.closest(".result-item");
  if (item) { doLookup(item.dataset.word); window.scrollTo({ top: 0, behavior: "smooth" }); }
  const rec = e.target.closest("[data-recent]");
  if (rec) doLookup(rec.dataset.recent);
  if (!e.target.closest(".search")) acList.hidden = true;
});

async function loadWordOfDay() {
  const box = $("#wotd .wotd-body");
  try {
    const e = await api("/api/word-of-the-day");
    if (!e) { $("#wotd").hidden = true; return; }
    box.innerHTML = `<div class="wotd-word sd" dir="rtl" data-wotd="${esc(e.word)}">${esc(e.word)}</div>
      <div class="wotd-gloss">${esc(e.translations.slice(0, 2).join(" · "))}</div>
      ${e.pos ? `<div style="margin-top:8px"><span class="badge">${esc(e.pos)}</span></div>` : ""}`;
    $("[data-wotd]", box).addEventListener("click", () => doLookup(e.word));
  } catch { $("#wotd").hidden = true; }
}

/* ---------------- translate ---------------- */
const tr = { source: "sd", target: "en" };
const trInput = $("#tr-input");
const TR_SAMPLES = {
  sd: "سنڌ هڪ خوبصورت صوبو آهي. هتي جا ماڻهو تمام مهمان نواز آهن.",
  en: "Education is the key to a better future. I love reading books in my language.",
};

function setDirection() {
  const sd = tr.source === "sd";
  $("#src-lang").textContent = sd ? "Sindhi" : "English";
  $("#tgt-lang").textContent = sd ? "English" : "Sindhi";
  trInput.dir = sd ? "rtl" : "ltr";
  trInput.classList.toggle("sd", sd);
  trInput.lang = tr.source;
  trInput.placeholder = sd ? "سنڌي متن هتي لکو..." : "Type English text here…";
  const out = $("#tr-output");
  out.dir = sd ? "ltr" : "rtl";
  out.classList.toggle("sd-out", !sd);
}

async function runTranslate() {
  const text = trInput.value.trim();
  if (!text) return;
  const out = $("#tr-output");
  out.innerHTML = `<span class="muted"><span class="spinner"></span>Translating…</span>`;
  const t0 = performance.now();
  try {
    const res = await api("/api/translate", { text, source: tr.source, target: tr.target });
    out.textContent = res.translation;
    $("#tr-time").textContent = `${res.engine === "nllb" ? "NLLB-200" : "dictionary glosses"} · ${((performance.now() - t0) / 1000).toFixed(1)} s`;
    const gl = res.glosses || [];
    $("#glossary").hidden = !gl.length;
    $("#gloss-list").innerHTML = gl.map((g) => `<div class="gloss-item"><b>${esc(g.word)}</b><span>${esc(g.gloss ? g.gloss.slice(0, 40) : "-")}</span></div>`).join("");
  } catch (e) {
    out.innerHTML = `<span class="muted">Translation failed: ${esc(e.message)}</span>`;
  }
}

$("#tr-btn").addEventListener("click", runTranslate);
trInput.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") runTranslate(); });
trInput.addEventListener("input", () => { $("#tr-count").textContent = `${trInput.value.length} / 3000`; });
$("#tr-sample").addEventListener("click", () => { trInput.value = TR_SAMPLES[tr.source]; trInput.dispatchEvent(new Event("input")); runTranslate(); });
$("#tr-copy").addEventListener("click", () => copyText($("#tr-output").textContent));
$("#swap-btn").addEventListener("click", () => {
  [tr.source, tr.target] = [tr.target, tr.source];
  const out = $("#tr-output").textContent;
  if (out && !out.startsWith("Translation appears")) trInput.value = out;
  $("#tr-output").innerHTML = `<span class="muted">Translation appears here.</span>`;
  $("#glossary").hidden = true;
  $("#swap-btn").classList.toggle("spin");
  setDirection();
});

/* ---------------- keyboard ---------------- */
const KB_ROWS = "ا ب ٻ ڀ پ ت ٿ ٽ ٺ ث ج ڄ ڃ چ ڇ ح خ د ڌ ڏ ڊ ڍ ذ ر ڙ ز س ش ص ض ط ظ ع غ ف ڦ ق ڪ ک گ ڳ ڱ ل م ن ڻ و ه ھ ء ي ئ آ ۾ ۽ ، ؟ ۔".split(" ");
let kbTarget = input;
$("#kb-keys").innerHTML = KB_ROWS.map((k) => `<button type="button" data-key="${k}">${k}</button>`).join("") +
  `<button type="button" class="wide" data-key=" ">space</button><button type="button" class="wide" data-key="⌫">⌫ delete</button>`;
[input, trInput, searchInput].forEach((el) => el.addEventListener("focus", () => (kbTarget = el)));
$$("[data-keyboard-toggle]").forEach((b) => b.addEventListener("click", (e) => {
  const view = e.target.closest(".view");
  if (view) kbTarget = view.querySelector("textarea, input[type=search]") || kbTarget;
  $("#keyboard").hidden = !$("#keyboard").hidden;
  kbTarget.focus();
}));
$("#kb-keys").addEventListener("mousedown", (e) => e.preventDefault()); // keep caret in the field
$("#kb-keys").addEventListener("click", (e) => {
  const key = e.target.closest("[data-key]")?.dataset.key;
  if (!key) return;
  const el = kbTarget;
  const s = el.selectionStart ?? el.value.length, en = el.selectionEnd ?? el.value.length;
  if (key === "⌫") {
    const from = s === en ? Math.max(0, s - 1) : s;
    el.value = el.value.slice(0, from) + el.value.slice(en);
    el.selectionStart = el.selectionEnd = from;
  } else {
    el.value = el.value.slice(0, s) + key + el.value.slice(en);
    el.selectionStart = el.selectionEnd = s + key.length;
  }
  el.dispatchEvent(new Event("input"));
});

/* ---------------- about / metrics ---------------- */
let metricsLoaded = false;
async function loadMetrics() {
  if (metricsLoaded) return;
  const m = await api("/api/metrics").catch(() => ({}));
  if (!m || !m.words) return;
  metricsLoaded = true;
  const pct = (x) => (x * 100).toFixed(1) + "%";
  const w = m.words, c = m.context;
  const rows = Object.entries(w.by_type).map(([k, r]) => `<tr><td>${esc(k.replace(/_/g, " "))}</td><td>${r.n}</td><td>${pct(r.top1)}</td><td>${pct(r.top3)}</td></tr>`).join("");
  $("#metrics").innerHTML = `
    <div class="metric-tiles">
      <div class="tile"><div class="v">${pct(w.top3)}</div><div class="l">correct word in top 3 (isolated words)</div></div>
      <div class="tile"><div class="v">${c ? pct(c.top1) : "-"}</div><div class="l">top-1 in real sentences</div></div>
      <div class="tile"><div class="v">${pct(w.recall)}</div><div class="l">misspellings detected</div></div>
      <div class="tile"><div class="v">${w.latency_ms.toFixed(0)} ms</div><div class="l">per suggestion (was ~1,600 ms)</div></div>
    </div>
    <table><thead><tr><th>Error type</th><th>Cases</th><th>Top-1</th><th>Top-3</th></tr></thead><tbody>${rows}</tbody></table>
    ${m.translation ? `<div class="section-label">Translation · FLORES-200 devtest (${m.translation.sentences} sentences)</div>
      <table><thead><tr><th>Direction</th><th>chrF++</th><th>BLEU</th><th>CPU time</th></tr></thead><tbody>
      ${[["sd-en", "Sindhi → English"], ["en-sd", "English → Sindhi"]].map(([k, l]) => `<tr><td>${l}</td><td>${m.translation[k]["chrf++"]}</td><td>${m.translation[k].bleu}</td><td>${m.translation[k].seconds_per_sentence} s/sentence</td></tr>`).join("")}
      </tbody></table>` : ""}
    ${m.real_word ? `<div class="section-label">Real-word errors (held-out Wikipedia)</div>
      <p class="muted small">Flags ${pct(m.real_word.false_alarm_rate)} of correctly used words and catches ${pct(m.real_word.recall)} of words swapped for a near-identical real word.</p>` : ""}`;
}

/* ---------------- boot ---------------- */
(async function boot() {
  showView(location.hash.slice(1) || "check");
  setDirection();
  renderRecent();
  loadWordOfDay();
  const draft = store.get("draft", "");
  if (draft) { input.value = draft; runCheck(); }
  try {
    const h = await api("/api/health");
    const badge = $("#engine-badge");
    badge.textContent = h.translator ? "offline model ready" : "model not installed: dictionary fallback";
    badge.className = "engine-badge " + (h.translator ? "on" : "off");
  } catch { /* server not up yet */ }
})();
