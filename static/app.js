const state = {
  studioFiles: [],
  vaultFiles: [],
  jobs: [],
  status: null,
  view: "studio",
};

const operationNames = {
  anonymize: "Anonimizzazione",
  transcribe: "Trascrizione",
  ocr: "OCR",
  convert: "Conversione",
  vault_encrypt: "Cifratura",
  vault_decrypt: "Decifratura",
};

const statusNames = {
  queued: "In coda",
  running: "In corso",
  completed: "Completato",
  failed: "Errore",
};

const viewTitles = {
  studio: "Laboratorio documenti",
  vault: "Cassaforte Picocrypt",
  jobs: "Attività",
  engines: "Motori locali",
};

const engineOptions = {
  anonymize: [
    ["privacy_filter", "OpenAI Privacy Filter · locale"],
  ],
  transcribe: [["parakeet", "NVIDIA Parakeet v3 · locale"]],
  ocr: [
    ["paddle", "PaddleOCR · rapido su CPU"],
    ["paddle_structure", "PP-StructureV3 · tabelle e layout"],
    ["glm", "GLM-OCR Q8 · qualità, molto lento su CPU"],
  ],
  convert: [["markitdown", "Microsoft MarkItDown · locale"]],
};

const operationHelp = {
  anonymize: {
    help: "Privacy Filter è il motore di anonimizzazione. L’estrazione del testo viene scelta automaticamente in base al file.",
    note: "OpenAI Privacy Filter rileva i dati personali in locale; MarkItDown o PaddleOCR intervengono automaticamente soltanto per leggere il documento.",
  },
  transcribe: {
    help: "Italiano e altre 24 lingue europee; punteggiatura automatica.",
    note: "FFmpeg divide in blocchi, Parakeet v3 li trascrive in sequenza e Privacy Studio li ricompone in TXT, Markdown e SRT.",
  },
  ocr: {
    help: "Paddle è consigliato e rapido; GLM-OCR Q8 conserva meglio documenti complessi ma su questa CPU può richiedere molti minuti per pagina.",
    note: "Le pagine vengono elaborate una per volta per tenere stabile la memoria anche con PDF molto lunghi.",
  },
  convert: {
    help: "Supporta PDF, Word, PowerPoint, Excel, HTML, EPUB e altri formati.",
    note: "MarkItDown usa soltanto percorsi locali e conserva titoli, elenchi, tabelle e collegamenti in Markdown.",
  },
};

const engineDescriptions = {
  markitdown: ["Microsoft MarkItDown", "Converte Office, PDF, HTML, EPUB e dati strutturati in Markdown."],
  privacy_filter: ["OpenAI Privacy Filter", "Rileva PII in locale con 8 categorie e contesto lungo."],
  parakeet: ["NVIDIA Parakeet v3", "Trascrizione multilingue con punteggiatura, anche per audio lunghi."],
  paddle: ["PaddleOCR / PP-StructureV3", "OCR CPU e ricostruzione di layout, tabelle e ordine di lettura."],
  glm: ["GLM-OCR Q8", "OCR multimodale locale via Ollama; modalità lenta per documenti complessi."],
  picocrypt: ["Picocrypt 1.49", "Volumi .pcv con XChaCha20, Argon2id e opzioni di recupero."],
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function humanSize(bytes) {
  const value = Number(bytes || 0);
  if (!value) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  return `${(value / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}`;
}

function humanDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return new Intl.DateTimeFormat("it-IT", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function toast(message, error = false) {
  const node = document.createElement("div");
  node.className = `toast${error ? " error" : ""}`;
  node.textContent = message;
  $("#toast-region").append(node);
  setTimeout(() => node.remove(), 5200);
}

function renderIcons() {
  if (!window.lucide) return;
  window.lucide.createIcons({
    attrs: {
      "aria-hidden": "true",
      focusable: "false",
    },
  });
}

async function api(path, options = {}) {
  const response = await fetch(path, { credentials: "same-origin", ...options });
  let payload = {};
  try {
    payload = await response.json();
  } catch {
    payload = {};
  }
  if (!response.ok) throw new Error(payload.detail || `Errore ${response.status}`);
  return payload;
}

function setView(name) {
  state.view = name;
  $$(".view").forEach((node) => node.classList.toggle("active", node.id === `view-${name}`));
  $$("[data-view-link]").forEach((node) => node.classList.toggle("active", node.dataset.viewLink === name));
  $("#page-title").textContent = viewTitles[name];
  if (name === "vault") loadVault();
  if (name === "engines") loadStatus();
  if (name === "jobs") renderJobs();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function fileKey(file) {
  return `${file.name}:${file.size}:${file.lastModified}`;
}

function addFiles(bucket, files) {
  const existing = new Set(state[bucket].map(fileKey));
  for (const file of files) {
    if (!existing.has(fileKey(file))) state[bucket].push(file);
  }
  renderSelectedFiles(bucket);
}

function renderSelectedFiles(bucket) {
  const target = bucket === "studioFiles" ? $("#studio-file-list") : $("#vault-file-list");
  target.innerHTML = state[bucket].map((file, index) => `
    <div class="file-pill">
      <strong title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</strong>
      <span>${humanSize(file.size)}</span>
      <button type="button" data-remove-file="${bucket}:${index}" aria-label="Rimuovi">×</button>
    </div>
  `).join("");
}

function bindDropZone(zoneSelector, inputSelector, bucket) {
  const zone = $(zoneSelector);
  const input = $(inputSelector);
  input.addEventListener("change", () => {
    addFiles(bucket, input.files);
    input.value = "";
  });
  ["dragenter", "dragover"].forEach((eventName) => {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.add("dragging");
    });
  });
  ["dragleave", "drop"].forEach((eventName) => {
    zone.addEventListener(eventName, (event) => {
      event.preventDefault();
      zone.classList.remove("dragging");
    });
  });
  zone.addEventListener("drop", (event) => addFiles(bucket, event.dataTransfer.files));
  zone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") input.click();
  });
}

function currentOperation() {
  return $('input[name="operation"]:checked').value;
}

function updateOperation() {
  const operation = currentOperation();
  $$(".operation").forEach((node) => node.classList.toggle("active", $("input", node).checked));
  $("#engine-select").innerHTML = engineOptions[operation]
    .map(([value, label]) => `<option value="${value}">${escapeHtml(label)}</option>`)
    .join("");
  $("#engine-help").textContent = operationHelp[operation].help;
  $("#engine-label").textContent = operation === "anonymize" ? "Motore privacy" : "Motore";
  $("#process-note-text").textContent = operationHelp[operation].note;
  $("#dates-option").classList.toggle("hidden", operation !== "anonymize");
  $("#chunk-option").classList.toggle("hidden", operation !== "transcribe");
}

function uploadJobs({ files, operation, engine, extras = {}, onDone, onFinally }) {
  if (!files.length) {
    toast("Aggiungi almeno un file.", true);
    return;
  }
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  form.append("operation", operation);
  form.append("engine", engine);
  Object.entries(extras).forEach(([key, value]) => form.append(key, String(value)));
  const xhr = new XMLHttpRequest();
  const progressBox = $("#upload-progress");
  const progressBar = $("#upload-progress span");
  progressBox.classList.remove("hidden");
  xhr.upload.addEventListener("progress", (event) => {
    if (event.lengthComputable) progressBar.style.width = `${event.loaded / event.total * 100}%`;
  });
  xhr.addEventListener("load", () => {
    progressBox.classList.add("hidden");
    progressBar.style.width = "0";
    if (xhr.status >= 200 && xhr.status < 300) {
      const payload = JSON.parse(xhr.responseText);
      toast(`${payload.jobs.length} lavoro/i aggiunti alla coda locale.`);
      onDone?.();
      loadJobs();
    } else {
      let detail = "Invio non riuscito.";
      try { detail = JSON.parse(xhr.responseText).detail || detail; } catch {}
      toast(detail, true);
    }
    onFinally?.();
  });
  xhr.addEventListener("error", () => {
    progressBox.classList.add("hidden");
    toast("Connessione al servizio locale interrotta.", true);
    onFinally?.();
  });
  xhr.open("POST", "/api/jobs");
  xhr.send(form);
}

function submitStudio(event) {
  event.preventDefault();
  const operation = currentOperation();
  const button = $("#studio-submit");
  button.disabled = true;
  uploadJobs({
    files: state.studioFiles,
    operation,
    engine: $("#engine-select").value,
    extras: {
      include_dates: $("#include-dates").checked,
      chunk_minutes: $("#chunk-minutes").value,
    },
    onDone: () => {
      state.studioFiles = [];
      renderSelectedFiles("studioFiles");
    },
    onFinally: () => { button.disabled = false; },
  });
}

function submitVault(operation) {
  const password = $("#vault-password").value;
  const confirm = $("#vault-confirm").value;
  if (password.length < 10) return toast("Usa una passphrase di almeno 10 caratteri.", true);
  if (operation === "vault_encrypt" && password !== confirm) {
    return toast("Le due passphrase non coincidono.", true);
  }
  if (operation === "vault_decrypt" && state.vaultFiles.some((file) => !file.name.toLowerCase().endsWith(".pcv"))) {
    return toast("Per decifrare seleziona soltanto volumi .pcv.", true);
  }
  uploadJobs({
    files: state.vaultFiles,
    operation,
    engine: "markitdown",
    extras: {
      password,
      paranoid: $("#vault-paranoid").checked,
      recovery: $("#vault-recovery").checked,
    },
    onDone: () => {
      state.vaultFiles = [];
      renderSelectedFiles("vaultFiles");
      $("#vault-password").value = "";
      $("#vault-confirm").value = "";
      loadVault();
    },
  });
}

function jobCard(job) {
  const percent = Math.round((job.progress || 0) * 100);
  return `
    <article class="job-card" data-job-id="${job.id}">
      <div class="job-head">
        <span class="job-type">${escapeHtml(operationNames[job.operation] || job.operation)}</span>
        <span class="status ${job.status}">${escapeHtml(statusNames[job.status] || job.status)}</span>
      </div>
      <h4 title="${escapeHtml(job.input_name)}">${escapeHtml(job.input_name)}</h4>
      <p>${escapeHtml(job.stage || humanDate(job.created_at))}</p>
      <div class="progress-track"><span style="width:${percent}%"></span></div>
    </article>
  `;
}

function renderJobs() {
  const recent = state.jobs.slice(0, 6);
  $("#recent-jobs").innerHTML = recent.length
    ? recent.slice(0, 3).map(jobCard).join("")
    : '<div class="empty-state">I tuoi lavori appariranno qui.</div>';
  $("#all-jobs").innerHTML = state.jobs.length
    ? state.jobs.map((job) => {
        const percent = Math.round((job.progress || 0) * 100);
        return `
          <article class="job-row" data-job-id="${job.id}">
            <span class="job-type">${escapeHtml(operationNames[job.operation] || job.operation)}</span>
            <div>
              <h4>${escapeHtml(job.input_name)}</h4>
              <p>${escapeHtml(job.stage)} · ${humanSize(job.input_size)}</p>
            </div>
            <div class="progress-inline"><div><span style="width:${percent}%"></span></div>${percent}%</div>
            <span class="status ${job.status}">${escapeHtml(statusNames[job.status] || job.status)}</span>
          </article>
        `;
      }).join("")
    : '<div class="empty-state">La coda è vuota.</div>';
  const active = state.jobs.filter((job) => ["queued", "running"].includes(job.status)).length;
  $("#active-count").textContent = active;
}

async function loadJobs() {
  try {
    const payload = await api("/api/jobs?limit=100");
    state.jobs = payload.jobs;
    renderJobs();
  } catch (error) {
    console.error(error);
  }
}

function showJob(jobId) {
  const job = state.jobs.find((item) => item.id === jobId);
  if (!job) return;
  const result = job.result || {};
  const counts = result.counts || {};
  const countHtml = Object.entries(counts).length
    ? `<div class="detail-counts">${Object.entries(counts).map(([key, value]) => `<span>${escapeHtml(key)} · ${value}</span>`).join("")}</div>`
    : "";
  const downloads = job.status === "completed" ? `
    <div class="download-actions">
      <a class="primary-button" href="/api/jobs/${job.id}/download">Scarica risultato</a>
      ${job.bundle_path ? `<a class="secondary-button" href="/api/jobs/${job.id}/download?kind=bundle">Scarica pacchetto ZIP</a>` : ""}
    </div>
  ` : "";
  $("#job-detail").innerHTML = `
    <div class="detail-title">
      <p class="eyebrow">${escapeHtml(operationNames[job.operation] || job.operation)}</p>
      <h2>${escapeHtml(job.input_name)}</h2>
      <p>${escapeHtml(job.stage)} · ${humanDate(job.updated_at)}</p>
    </div>
    <div class="detail-stats">
      <div class="detail-stat"><strong>${Math.round(job.progress * 100)}%</strong><small>Avanzamento</small></div>
      <div class="detail-stat"><strong>${humanSize(job.input_size)}</strong><small>Dimensione</small></div>
      <div class="detail-stat"><strong>${result.detections ?? result.pages ?? result.chunks ?? "—"}</strong><small>Elementi</small></div>
    </div>
    ${job.error ? `<div class="detail-error">${escapeHtml(job.error)}</div>` : ""}
    ${countHtml}
    ${result.review_required ? '<div class="process-note"><span>!</span><p>Il risultato richiede sempre revisione umana prima della condivisione.</p></div>' : ""}
    ${downloads}
  `;
  $("#job-dialog").showModal();
}

async function loadStatus() {
  try {
    const payload = await api("/api/status");
    state.status = payload;
    const entries = Object.entries(payload.engines);
    const ready = entries.filter(([, value]) => value.ready && value.model_ready).length;
    $("#engine-summary").textContent = `${ready}/${entries.length} motori pronti`;
    $("#engine-grid").innerHTML = entries.map(([key, value]) => {
      const [name, description] = engineDescriptions[key] || [key, ""];
      const fullyReady = value.ready && value.model_ready;
      return `
        <article class="engine-card">
          <div class="engine-card-head">
            <h3>${escapeHtml(name)}</h3>
            <span class="ready-badge${fullyReady ? "" : " no"}">${fullyReady ? "Pronto" : "Da preparare"}</span>
          </div>
          <p>${escapeHtml(description)}</p>
          <div class="engine-model${value.model_ready ? "" : " no"}">${escapeHtml(value.detail || "")}</div>
        </article>
      `;
    }).join("");
  } catch (error) {
    $("#engine-summary").textContent = "Servizio non disponibile";
  }
}

async function loadVault() {
  try {
    const payload = await api("/api/vault");
    $("#vault-list").innerHTML = payload.volumes.length
      ? payload.volumes.map((volume) => `
          <div class="vault-item">
            <div>
              <strong>${escapeHtml(volume.name)}</strong>
              <small>${humanSize(volume.size)} · ${humanDate(volume.updated_at)}</small>
            </div>
            <button type="button" data-decrypt-volume="${escapeHtml(volume.name)}">Decifra</button>
          </div>
        `).join("")
      : '<div class="empty-state">La cassaforte è vuota.</div>';
  } catch (error) {
    toast(error.message, true);
  }
}

async function decryptStored(event) {
  event.preventDefault();
  const name = $("#decrypt-volume-value").value;
  const form = new FormData();
  form.append("password", $("#stored-decrypt-password").value);
  try {
    await api(`/api/vault/${encodeURIComponent(name)}/decrypt`, { method: "POST", body: form });
    $("#decrypt-dialog").close();
    $("#stored-decrypt-password").value = "";
    toast("Decifratura aggiunta alla coda.");
    loadJobs();
  } catch (error) {
    toast(error.message, true);
  }
}

document.addEventListener("click", (event) => {
  const viewLink = event.target.closest("[data-view-link]");
  if (viewLink) {
    event.preventDefault();
    setView(viewLink.dataset.viewLink);
  }
  const remove = event.target.closest("[data-remove-file]");
  if (remove) {
    const [bucket, index] = remove.dataset.removeFile.split(":");
    state[bucket].splice(Number(index), 1);
    renderSelectedFiles(bucket);
  }
  const jobNode = event.target.closest("[data-job-id]");
  if (jobNode) showJob(jobNode.dataset.jobId);
  const close = event.target.closest("[data-close-dialog]");
  if (close) close.closest("dialog").close();
  const decrypt = event.target.closest("[data-decrypt-volume]");
  if (decrypt) {
    $("#decrypt-volume-name").textContent = decrypt.dataset.decryptVolume;
    $("#decrypt-volume-value").value = decrypt.dataset.decryptVolume;
    $("#decrypt-dialog").showModal();
  }
});

$$('input[name="operation"]').forEach((input) => input.addEventListener("change", updateOperation));
$("#studio-form").addEventListener("submit", submitStudio);
$("#encrypt-button").addEventListener("click", () => submitVault("vault_encrypt"));
$("#decrypt-button").addEventListener("click", () => submitVault("vault_decrypt"));
$("#stored-decrypt-form").addEventListener("submit", decryptStored);
$("#refresh-button").addEventListener("click", () => Promise.all([loadJobs(), loadStatus()]));
$("#refresh-vault").addEventListener("click", loadVault);

bindDropZone("#studio-drop", "#studio-files", "studioFiles");
bindDropZone("#vault-drop", "#vault-files", "vaultFiles");
updateOperation();
renderIcons();
loadJobs();
loadStatus();
setInterval(loadJobs, 2500);
setInterval(loadStatus, 60000);
