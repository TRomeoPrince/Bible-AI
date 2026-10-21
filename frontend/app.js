const $ = (s) => document.querySelector(s);
let translations = [];
let currentReference = null;
let currentTranslation = null;

async function api(path, options = {}) {
  const response = await fetch(path, options);
  let data = null;
  try { data = await response.json(); } catch { data = {}; }
  if (!response.ok) throw new Error(data.detail || data.message || ("HTTP " + response.status));
  return data;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderText(value) {
  return escapeHtml(value).replaceAll("\n", "<br>");
}

function setStatus(selector, value) {
  $(selector).textContent = value || "";
}

function show(selector, yes = true) {
  $(selector).classList.toggle("hidden", !yes);
}

document.querySelectorAll(".nav").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav").forEach(x => x.classList.remove("active"));
    document.querySelectorAll(".view").forEach(x => x.classList.remove("active"));
    btn.classList.add("active");
    $("#view-" + btn.dataset.view).classList.add("active");
  });
});

async function loadProviders() {
  try {
    const p = await api("/api/providers");
    const bits = [
      "YouVersion " + (p.youversion.configured ? "✓" : "—"),
      "IQ Bible " + (p.iqbible.configured ? "✓" : "—"),
      "Ollama " + (p.ollama.configured ? (p.ollama.model_available ? "✓" : "⚠ model") : "—"),
    ];
    $("#provider-status").textContent = bits.join(" · ");
  } catch {
    $("#provider-status").textContent = "Provider status unavailable";
  }
}

async function loadTranslations() {
  try {
    translations = await api("/api/translations?language=en&include_unlicensed=true");
  } catch (e) {
    translations = [];
    setStatus("#chat-status", "Could not load translations: " + e.message);
  }

  for (const selector of ["#translation", "#chat-translation"]) {
    const select = $(selector);
    select.innerHTML = "";
    translations.forEach(item => {
      const option = document.createElement("option");
      option.value = item.code;
      option.dataset.bibleId = item.bible_id || "";
      option.disabled = item.available === false;
      option.textContent = item.code + " — " + item.name
        + (item.available === false ? " (license required)" : "")
        + " [" + item.provider + "]";
      select.appendChild(option);
    });
  }

  try {
    const pref = await api("/api/settings/preferred_translation");
    if (pref.value) {
      for (const selector of ["#translation", "#chat-translation"]) {
        const select = $(selector);
        const option = [...select.options].find(x => x.value.toUpperCase() === pref.value.toUpperCase());
        if (option) select.value = option.value;
      }
    }
  } catch {}
}

function selectedBibleId(selector) {
  const option = $(selector).selectedOptions[0];
  return option && option.dataset.bibleId ? Number(option.dataset.bibleId) : null;
}

async function lookup(reference, translation, bibleId) {
  let url = "/api/passage?reference=" + encodeURIComponent(reference)
    + "&translation=" + encodeURIComponent(translation);
  if (bibleId) url += "&bible_id=" + bibleId;
  return api(url);
}

function renderScriptureCard(target, data) {
  const t = data.translation || {};
  const text = data.text || (data.verses || []).map(v => v.text).join(" ");
  target.innerHTML =
    '<div class="section-label">SCRIPTURE · ' + escapeHtml(data.provider || t.provider || "") + '</div>' +
    '<h2>' + escapeHtml(data.reference) + ' — ' + escapeHtml(t.name || t.code || "") + '</h2>' +
    '<div class="scripture-text">' + renderText(text) + '</div>' +
    (t.attribution ? '<p class="attribution">' + escapeHtml(t.attribution) + '</p>' : "");
}

$("#lookup-btn").addEventListener("click", async () => {
  setStatus("#lookup-status", "Loading Scripture…");
  try {
    const reference = $("#reference").value.trim();
    const translation = $("#translation").value;
    const data = await lookup(reference, translation, selectedBibleId("#translation"));
    currentReference = data.reference;
    currentTranslation = translation;
    renderScriptureCard($("#scripture"), data);
    show("#scripture");
    setStatus("#lookup-status", "");
    await api("/api/settings/preferred_translation", {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({value: translation})
    });
  } catch (e) {
    show("#scripture", false);
    setStatus("#lookup-status", e.message);
  }
});

$("#save-note").addEventListener("click", async () => {
  const note = $("#note").value.trim();
  if (!currentReference || !note) {
    setStatus("#lookup-status", "Look up a passage and write a note first.");
    return;
  }
  try {
    await api("/api/notes", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        reference: currentReference,
        translation: currentTranslation,
        note
      })
    });
    $("#note").value = "";
    setStatus("#lookup-status", "Note saved.");
  } catch (e) {
    setStatus("#lookup-status", e.message);
  }
});

$("#ask-btn").addEventListener("click", async () => {
  const question = $("#question").value.trim();
  if (!question) return;
  setStatus("#chat-status", "Studying sources and preparing answer…");
  show("#ai-answer", false);
  show("#scripture-answer", false);

  try {
    const translation = $("#chat-translation").value || "WEB";
    const data = await api("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        question,
        translation,
        bible_id: selectedBibleId("#chat-translation"),
        mode: $("#chat-mode").value
      })
    });

    if (data.scripture) {
      renderScriptureCard($("#scripture-answer"), data.scripture);
      show("#scripture-answer");
    }

    $("#ai-answer").innerHTML =
      '<div class="section-label">STUDY / INTERPRETATION</div>' +
      '<div class="ai-text">' + renderText(data.answer) + '</div>' +
      '<div class="source-strip">' +
      (data.sources || []).map(s => '<span>' + escapeHtml(s.name) + ' · ' + escapeHtml(s.type) + '</span>').join("") +
      '</div>';
    show("#ai-answer");
    setStatus("#chat-status", data.ai_available ? "" : "Local AI is offline; start Ollama for explanations.");
  } catch (e) {
    setStatus("#chat-status", e.message);
  }
});

$("#compare-btn").addEventListener("click", async () => {
  setStatus("#compare-status", "Comparing translations…");
  $("#comparison-results").innerHTML = "";
  try {
    const ref = $("#compare-reference").value.trim();
    const list = $("#compare-translations").value.trim();
    const data = await api("/api/compare?reference=" + encodeURIComponent(ref) + "&translations=" + encodeURIComponent(list));
    for (const item of data.comparisons) {
      const card = document.createElement("section");
      card.className = "card";
      if (item.status !== "ok") {
        card.innerHTML = '<h3>' + escapeHtml(item.translation) + '</h3><p class="error">' + escapeHtml(item.error) + '</p>';
      } else {
        const r = item.result;
        card.innerHTML =
          '<div class="section-label">' + escapeHtml(item.translation) + ' · ' + escapeHtml(r.provider) + '</div>' +
          '<div class="scripture-text">' + renderText(r.text) + '</div>' +
          (r.translation.attribution ? '<p class="attribution">' + escapeHtml(r.translation.attribution) + '</p>' : "");
      }
      $("#comparison-results").appendChild(card);
    }
    setStatus("#compare-status", "");
  } catch (e) {
    setStatus("#compare-status", e.message);
  }
});

function firstObject(value) {
  if (!value) return null;
  if (Array.isArray(value)) return value.length ? firstObject(value[0]) : null;
  if (typeof value === "object") {
    if (Array.isArray(value.data) && value.data.length) return firstObject(value.data[0]);
    if (value.data && typeof value.data === "object") return firstObject(value.data);
    return value;
  }
  return null;
}

function renderStrongStudy(data) {
  const iq = firstObject(data.iq_bible);
  const thayer = Array.isArray(data.thayer) && data.thayer.length ? data.thayer[0] : null;
  let html = '<div class="section-label">LEXICON STUDY · ' + escapeHtml(data.strong_number) + '</div>';

  if (iq) {
    html += '<h2>' + escapeHtml(iq.word || iq.lemma || iq.key || data.strong_number) + '</h2>';
    if (iq.transliteration || iq.pronunciation || iq.pronun) {
      html += '<p><b>Transliteration / pronunciation:</b> ' +
        escapeHtml(iq.transliteration || "") + ' ' + escapeHtml(iq.pronunciation || iq.pronun || "") + '</p>';
    }
    if (iq.glossary || iq.definition || iq.gloss) {
      html += '<div class="ai-text"><b>Definition:</b><br>' +
        renderText(iq.glossary || iq.definition || iq.gloss) + '</div>';
    }
    if (iq.occurences || iq.occurrences) {
      html += '<p><b>Occurrences:</b> ' + escapeHtml(iq.occurences || iq.occurrences) + '</p>';
    }
  }

  if (thayer) {
    html += '<hr><div class="section-label">THAYER (LOCAL PUBLIC DOMAIN)</div>';
    html += '<h3>' + escapeHtml(thayer.lemma || data.strong_number) + '</h3>';
    if (thayer.grammar) html += '<p><b>Grammar:</b> ' + escapeHtml(thayer.grammar) + '</p>';
    if (thayer.definition) html += '<div class="ai-text">' + renderText(thayer.definition) + '</div>';
  }

  if (!iq && !thayer) {
    html += '<p>No lexicon entry was returned.</p>';
  }

  if (data.warnings && data.warnings.length) {
    html += '<div class="status">' + data.warnings.map(escapeHtml).join("<br>") + '</div>';
  }
  return html;
}

function renderStudyContext(data) {
  const d = data.data || {};
  let html = '<div class="section-label">PASSAGE STUDY CONTEXT · ' + escapeHtml(data.reference) + '</div>';
  const verse = firstObject(d);
  if (verse) {
    html += '<h2>' + escapeHtml(verse.name_en || verse.book || data.reference) + ' ' +
      escapeHtml(verse.chapter || "") + ':' + escapeHtml(verse.verse || "") + '</h2>';
    if (verse.text) html += '<div class="scripture-text">' + renderText(verse.text) + '</div>';
    if (verse.version) html += '<p class="attribution">Source version: ' + escapeHtml(verse.version) + ' · IQ Bible API</p>';
  } else {
    html += '<p>Study context loaded, but this response did not contain a directly renderable verse object.</p>';
  }
  return html;
}

$("#strong-btn").addEventListener("click", async () => {
  setStatus("#word-status", "Loading lexicon…");
  try {
    const data = await api("/api/word-study/strongs/" + encodeURIComponent($("#strong-number").value.trim()));
    $("#word-results").innerHTML = renderStrongStudy(data);
    show("#word-results");
    setStatus("#word-status", "");
  } catch (e) {
    setStatus("#word-status", e.message);
  }
});

$("#context-btn").addEventListener("click", async () => {
  setStatus("#word-status", "Loading passage study context…");
  try {
    const data = await api("/api/word-study/context?reference=" + encodeURIComponent($("#word-reference").value.trim()));
    $("#word-results").innerHTML = renderStudyContext(data);
    show("#word-results");
    setStatus("#word-status", "");
  } catch (e) {
    setStatus("#word-status", e.message);
  }
});

async function loadMemorization() {
  try {
    const items = await api("/api/memorization");
    $("#memorization-list").innerHTML = items.length
      ? items.map(x => '<div class="memory-item"><b>' + escapeHtml(x.reference) + '</b> · ' +
          escapeHtml(x.translation) + '<br><small>✓ ' + x.correct_count + ' · ✗ ' + x.incorrect_count + '</small></div>').join("")
      : '<p class="muted">No memorization verses yet.</p>';
  } catch {}
}

$("#memorize-btn").addEventListener("click", async () => {
  try {
    await api("/api/memorization", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        reference: $("#memory-reference").value.trim(),
        translation: $("#memory-translation").value.trim()
      })
    });
    await loadMemorization();
  } catch (e) {
    alert(e.message);
  }
});

$("#plan-btn").addEventListener("click", async () => {
  $("#plan-output").textContent = "Generating…";
  try {
    const data = await api("/api/study-plans", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        title: $("#plan-title").value.trim() || "Bible Study Plan",
        topic: $("#plan-topic").value.trim(),
        days: Number($("#plan-days").value || 7),
        generate: true
      })
    });
    $("#plan-output").innerHTML = data.generated
      ? '<div class="ai-text">' + renderText(data.generated.answer) + '</div>'
      : '<p>Plan saved.</p>';
  } catch (e) {
    $("#plan-output").textContent = e.message;
  }
});

Promise.all([loadProviders(), loadTranslations(), loadMemorization()]);
