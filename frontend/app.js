const translationSelect = document.querySelector("#translation");
const translationsList = document.querySelector("#translations-list");
const statusBox = document.querySelector("#status");
const scriptureCard = document.querySelector("#scripture");
const passageTitle = document.querySelector("#passage-title");
const passageText = document.querySelector("#passage-text");
const attribution = document.querySelector("#attribution");
let currentReference = null;

async function loadTranslations() {
  const response = await fetch("/api/translations");
  const items = await response.json();

  translationSelect.innerHTML = "";
  translationsList.innerHTML = "";

  for (const item of items) {
    if (item.available) {
      const option = document.createElement("option");
      option.value = item.code;
      option.textContent = item.code + " — " + item.name;
      translationSelect.appendChild(option);
    }

    const line = document.createElement("div");
    line.className = "translation-line";
    const state = item.available ? "installed" : item.access_mode;
    line.textContent = item.code + " — " + item.name + " · " + state;
    translationsList.appendChild(line);
  }

  if (!translationSelect.options.length) {
    const option = document.createElement("option");
    option.textContent = "No local translations installed";
    option.disabled = true;
    option.selected = true;
    translationSelect.appendChild(option);
  }
}

document.querySelector("#lookup-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!translationSelect.value) return;

  const reference = document.querySelector("#reference").value.trim();
  const translation = translationSelect.value;
  statusBox.textContent = "Loading…";

  const url = "/api/passage?reference=" + encodeURIComponent(reference)
    + "&translation=" + encodeURIComponent(translation);
  const response = await fetch(url);
  const data = await response.json();

  if (!response.ok) {
    scriptureCard.classList.add("hidden");
    statusBox.textContent = data.detail || "Passage unavailable.";
    return;
  }

  currentReference = data.reference;
  passageTitle.textContent = data.reference + " — " + data.translation.name
    + " (" + data.translation.code + ")";
  passageText.innerHTML = data.verses
    .map(v => "<p><sup>" + v.verse + "</sup> " + escapeHtml(v.text) + "</p>")
    .join("");
  attribution.textContent = data.translation.attribution || "";
  scriptureCard.classList.remove("hidden");
  statusBox.textContent = "";
});

document.querySelector("#save-note").addEventListener("click", async () => {
  const note = document.querySelector("#note").value.trim();
  if (!currentReference || !note || !translationSelect.value) {
    statusBox.textContent = "Look up a passage and write a note first.";
    return;
  }

  const response = await fetch("/api/notes", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      reference: currentReference,
      translation: translationSelect.value,
      note: note
    })
  });

  statusBox.textContent = response.ok ? "Note saved." : "Could not save note.";
  if (response.ok) document.querySelector("#note").value = "";
});

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

loadTranslations().catch(() => {
  statusBox.textContent = "Could not load translation registry.";
});
