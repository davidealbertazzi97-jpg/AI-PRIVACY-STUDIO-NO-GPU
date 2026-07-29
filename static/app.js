const state = {
  studioFiles: [],
  vaultFiles: [],
  jobs: [],
  status: null,
  view: "studio",
  language: localStorage.getItem("privacy-studio-language") === "en" ? "en" : "it",
};

const locales = {
  it: {
    dateLocale: "it-IT",
    text: {
      "nav.aria": "Navigazione principale",
      "nav.studio": "Laboratorio",
      "nav.vault": "Cassaforte",
      "nav.jobs": "Attività",
      "nav.engines": "Motori locali",
      "seal.title": "Connessione locale",
      "seal.detail": "Rete esterna bloccata",
      "language.aria": "Lingua interfaccia",
      "actions.refresh": "Aggiorna",
      "actions.close": "Chiudi",
      "hero.badge": "Elaborazione privata sul dispositivo",
      "hero.title": "I tuoi documenti.<br><span>Solo tuoi.</span>",
      "hero.description": "Trascrivi, converti, anonimizza e proteggi file complessi con modelli locali. Gli originali restano sempre intatti.",
      "hero.cloudTitle": "Zero cloud implicito",
      "hero.cloudDetail": "Il guard di rete consente alla suite soltanto connessioni locali.",
      "hero.verified": "Verificato",
      "studio.chooseFlow": "Scegli il flusso",
      "studio.addFiles": "Aggiungi i file",
      "studio.dropTitle": "Trascina qui i documenti",
      "studio.dropDetail": "oppure selezionali dal dispositivo",
      "studio.noLimit": "Nessun limite artificiale di pagine o durata",
      "studio.configure": "Configura",
      "studio.protectDates": "Proteggi anche le date",
      "studio.protectDatesDetail": "Include date personali e di nascita",
      "studio.chunkSize": "Dimensione blocchi audio",
      "studio.chunk5": "5 minuti — prudente",
      "studio.chunk10": "10 minuti — consigliato",
      "studio.chunk15": "15 minuti — meno blocchi",
      "studio.chunk20": "20 minuti — più memoria",
      "studio.chunkDetail": "I blocchi vengono ricomposti automaticamente.",
      "studio.start": "Avvia in locale",
      "studio.uploading": "Trasferimento locale nel laboratorio…",
      "operation.anonymize": "Anonimizza",
      "operation.anonymizeDetail": "Privacy Filter e regole italiane",
      "operation.transcribe": "Trascrivi",
      "operation.transcribeDetail": "Audio e video con Parakeet",
      "operation.ocr": "Fai OCR",
      "operation.ocrDetail": "Immagini e PDF multipagina",
      "operation.convert": "Converti",
      "operation.convertDetail": "Office e PDF in Markdown",
      "recent.label": "ATTIVITÀ RECENTI",
      "recent.title": "In lavorazione e completati",
      "recent.all": "Vedi tutto",
      "vault.badge": "Picocrypt 1.49 · formato .pcv",
      "vault.title": "Protezione forte.<br><span>Senza compromessi.</span>",
      "vault.description": "I file diventano volumi Picocrypt compatibili. La password rimane soltanto in memoria durante l’operazione e non viene mai salvata.",
      "vault.filesLabel": "FILE DA PROTEGGERE O APRIRE",
      "vault.dropTitle": "Trascina file o volumi .pcv",
      "vault.dropDetail": "Puoi cifrare file grandi senza caricarli online",
      "vault.passphrase": "Passphrase",
      "vault.passphrasePlaceholder": "Una frase lunga e unica",
      "vault.confirm": "Conferma passphrase",
      "vault.confirmPlaceholder": "Ripetila",
      "vault.paranoid": "Modalità paranoica",
      "vault.paranoidDetail": "Cascata XChaCha20 + Serpent; molto più lenta",
      "vault.recovery": "Correzione errori",
      "vault.recoveryDetail": "Reed–Solomon per archiviazione di lungo periodo",
      "vault.encrypt": "Cifra nella cassaforte",
      "vault.decrypt": "Decifra .pcv",
      "vault.localVolumes": "VOLUMI LOCALI",
      "vault.contents": "Contenuto della cassaforte",
      "vault.refresh": "Aggiorna cassaforte",
      "jobs.badge": "Coda persistente",
      "jobs.title": "Tutte le attività",
      "jobs.description": "I lavori lunghi restano in coda e riprendono dopo un riavvio.",
      "engines.badge": "Diagnostica locale",
      "engines.title": "Motori e modelli",
      "engines.description": "I modelli vengono preparati durante l’installazione. Verde significa pronto e utilizzabile con la rete esterna bloccata.",
      "engines.file": "FILE",
      "engines.extraction": "ESTRAZIONE",
      "engines.privacy": "PRIVACY",
      "engines.output": "OUTPUT",
      "engines.architecture": "MarkItDown gestisce i formati nativi; PaddleOCR e GLM-OCR le scansioni; Parakeet v3 l’audio; Privacy Filter lavora sul testo già locale. Picocrypt protegge i file separatamente.",
      "engines.oss": "Inter (OFL 1.1) + Lucide (ISC) · asset grafici open source inclusi",
      "footer.notice": "Progetto personale sperimentale, fornito \"così com’è\". Verifica sempre i risultati.",
      "footer.disclaimer": "Avvertenze · Disclaimer",
      "dialog.openVolume": "APRI VOLUME",
      "dialog.decryptLocal": "Decifra in locale",
      "status.checking": "Verifica motori…",
    },
    operationNames: {
      anonymize: "Anonimizzazione",
      transcribe: "Trascrizione",
      ocr: "OCR",
      convert: "Conversione",
      vault_encrypt: "Cifratura",
      vault_decrypt: "Decifratura",
    },
    statusNames: {
      queued: "In coda",
      running: "In corso",
      completed: "Completato",
      failed: "Errore",
    },
    viewTitles: {
      studio: "Laboratorio documenti",
      vault: "Cassaforte Picocrypt",
      jobs: "Attività",
      engines: "Motori locali",
    },
    engineOptions: {
      anonymize: [["privacy_filter", "OpenAI Privacy Filter · locale"]],
      transcribe: [["parakeet", "NVIDIA Parakeet v3 · locale"]],
      ocr: [
        ["paddle", "PaddleOCR · rapido su CPU"],
        ["paddle_structure", "PP-StructureV3 · tabelle e layout"],
        ["glm", "GLM-OCR Q8 · qualità, molto lento su CPU"],
      ],
      convert: [["markitdown", "Microsoft MarkItDown · locale"]],
    },
    operationHelp: {
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
    },
    engineDescriptions: {
      markitdown: ["Microsoft MarkItDown", "Converte Office, PDF, HTML, EPUB e dati strutturati in Markdown."],
      privacy_filter: ["OpenAI Privacy Filter", "Rileva PII in locale con 8 categorie e contesto lungo."],
      parakeet: ["NVIDIA Parakeet v3", "Trascrizione multilingue con punteggiatura, anche per audio lunghi."],
      paddle: ["PaddleOCR / PP-StructureV3", "OCR CPU e ricostruzione di layout, tabelle e ordine di lettura."],
      glm: ["GLM-OCR Q8", "OCR multimodale locale via Ollama; modalità lenta per documenti complessi."],
      picocrypt: ["Picocrypt 1.49", "Volumi .pcv con XChaCha20, Argon2id e opzioni di recupero."],
    },
    messages: {
      apiError: "Errore",
      remove: "Rimuovi",
      enginePrivacy: "Motore privacy",
      engine: "Motore",
      addFile: "Aggiungi almeno un file.",
      jobsAdded: (count) => `${count} lavoro/i aggiunti alla coda locale.`,
      sendFailed: "Invio non riuscito.",
      connectionLost: "Connessione al servizio locale interrotta.",
      passwordLength: "Usa una passphrase di almeno 10 caratteri.",
      passwordMismatch: "Le due passphrase non coincidono.",
      decryptOnlyPcv: "Per decifrare seleziona soltanto volumi .pcv.",
      recentEmpty: "I tuoi lavori appariranno qui.",
      queueEmpty: "La coda è vuota.",
      downloadResult: "Scarica risultato",
      downloadZip: "Scarica pacchetto ZIP",
      progress: "Avanzamento",
      size: "Dimensione",
      items: "Elementi",
      review: "Il risultato richiede sempre revisione umana prima della condivisione.",
      enginesReady: (ready, total) => `${ready}/${total} motori pronti`,
      ready: "Pronto",
      prepare: "Da preparare",
      serviceUnavailable: "Servizio non disponibile",
      vaultEmpty: "La cassaforte è vuota.",
      decrypt: "Decifra",
      decryptQueued: "Decifratura aggiunta alla coda.",
    },
  },
  en: {
    dateLocale: "en-GB",
    text: {
      "nav.aria": "Main navigation",
      "nav.studio": "Studio",
      "nav.vault": "Vault",
      "nav.jobs": "Activity",
      "nav.engines": "Local engines",
      "seal.title": "Local connection",
      "seal.detail": "External network blocked",
      "language.aria": "Interface language",
      "actions.refresh": "Refresh",
      "actions.close": "Close",
      "hero.badge": "Private on-device processing",
      "hero.title": "Your documents.<br><span>Yours alone.</span>",
      "hero.description": "Transcribe, convert, redact, and protect complex files with local models. Original files always remain untouched.",
      "hero.cloudTitle": "No implicit cloud",
      "hero.cloudDetail": "The network guard allows the suite to make local connections only.",
      "hero.verified": "Verified",
      "studio.chooseFlow": "Choose a workflow",
      "studio.addFiles": "Add files",
      "studio.dropTitle": "Drop your documents here",
      "studio.dropDetail": "or select them from your device",
      "studio.noLimit": "No artificial page or duration limits",
      "studio.configure": "Configure",
      "studio.protectDates": "Protect dates too",
      "studio.protectDatesDetail": "Includes personal dates and dates of birth",
      "studio.chunkSize": "Audio chunk size",
      "studio.chunk5": "5 minutes — cautious",
      "studio.chunk10": "10 minutes — recommended",
      "studio.chunk15": "15 minutes — fewer chunks",
      "studio.chunk20": "20 minutes — more memory",
      "studio.chunkDetail": "Chunks are recombined automatically.",
      "studio.start": "Start locally",
      "studio.uploading": "Transferring locally to the studio…",
      "operation.anonymize": "Redact",
      "operation.anonymizeDetail": "Privacy Filter and Italian rules",
      "operation.transcribe": "Transcribe",
      "operation.transcribeDetail": "Audio and video with Parakeet",
      "operation.ocr": "Run OCR",
      "operation.ocrDetail": "Images and multi-page PDFs",
      "operation.convert": "Convert",
      "operation.convertDetail": "Office and PDF to Markdown",
      "recent.label": "RECENT ACTIVITY",
      "recent.title": "In progress and completed",
      "recent.all": "View all",
      "vault.badge": "Picocrypt 1.49 · .pcv format",
      "vault.title": "Strong protection.<br><span>No compromises.</span>",
      "vault.description": "Files become compatible Picocrypt volumes. The passphrase remains in memory only during the operation and is never saved.",
      "vault.filesLabel": "FILES TO PROTECT OR OPEN",
      "vault.dropTitle": "Drop files or .pcv volumes",
      "vault.dropDetail": "Encrypt large files without uploading them",
      "vault.passphrase": "Passphrase",
      "vault.passphrasePlaceholder": "A long, unique phrase",
      "vault.confirm": "Confirm passphrase",
      "vault.confirmPlaceholder": "Repeat it",
      "vault.paranoid": "Paranoid mode",
      "vault.paranoidDetail": "XChaCha20 + Serpent cascade; much slower",
      "vault.recovery": "Error correction",
      "vault.recoveryDetail": "Reed–Solomon for long-term storage",
      "vault.encrypt": "Encrypt into the vault",
      "vault.decrypt": "Decrypt .pcv",
      "vault.localVolumes": "LOCAL VOLUMES",
      "vault.contents": "Vault contents",
      "vault.refresh": "Refresh vault",
      "jobs.badge": "Persistent queue",
      "jobs.title": "All activity",
      "jobs.description": "Long-running jobs remain queued and resume after a restart.",
      "engines.badge": "Local diagnostics",
      "engines.title": "Engines and models",
      "engines.description": "Models are prepared during installation. Green means ready for use with external networking blocked.",
      "engines.file": "FILE",
      "engines.extraction": "EXTRACTION",
      "engines.privacy": "PRIVACY",
      "engines.output": "OUTPUT",
      "engines.architecture": "MarkItDown handles native formats; PaddleOCR and GLM-OCR process scans; Parakeet v3 handles audio; Privacy Filter works on already-local text. Picocrypt protects files separately.",
      "engines.oss": "Inter (OFL 1.1) + Lucide (ISC) · bundled open-source visual assets",
      "footer.notice": "Personal experimental project, provided \"as is\". Always review the results.",
      "footer.disclaimer": "Legal notice · Disclaimer",
      "dialog.openVolume": "OPEN VOLUME",
      "dialog.decryptLocal": "Decrypt locally",
      "status.checking": "Checking engines…",
    },
    operationNames: {
      anonymize: "Redaction",
      transcribe: "Transcription",
      ocr: "OCR",
      convert: "Conversion",
      vault_encrypt: "Encryption",
      vault_decrypt: "Decryption",
    },
    statusNames: {
      queued: "Queued",
      running: "Running",
      completed: "Completed",
      failed: "Error",
    },
    viewTitles: {
      studio: "Document studio",
      vault: "Picocrypt vault",
      jobs: "Activity",
      engines: "Local engines",
    },
    engineOptions: {
      anonymize: [["privacy_filter", "OpenAI Privacy Filter · local"]],
      transcribe: [["parakeet", "NVIDIA Parakeet v3 · local"]],
      ocr: [
        ["paddle", "PaddleOCR · fast on CPU"],
        ["paddle_structure", "PP-StructureV3 · tables and layout"],
        ["glm", "GLM-OCR Q8 · quality, very slow on CPU"],
      ],
      convert: [["markitdown", "Microsoft MarkItDown · local"]],
    },
    operationHelp: {
      anonymize: {
        help: "Privacy Filter is the redaction engine. Text extraction is selected automatically for each file.",
        note: "OpenAI Privacy Filter detects personal data locally; MarkItDown or PaddleOCR are used automatically only to read the document.",
      },
      transcribe: {
        help: "Italian and 24 other European languages, with automatic punctuation.",
        note: "FFmpeg splits the audio, Parakeet v3 transcribes each chunk, and Privacy Studio recombines them into TXT, Markdown, and SRT.",
      },
      ocr: {
        help: "Paddle is the recommended fast option. GLM-OCR Q8 preserves complex documents better but may take several minutes per page on this CPU.",
        note: "Pages are processed one at a time to keep memory stable even with very long PDFs.",
      },
      convert: {
        help: "Supports PDF, Word, PowerPoint, Excel, HTML, EPUB, and other formats.",
        note: "MarkItDown uses local paths only and preserves headings, lists, tables, and links in Markdown.",
      },
    },
    engineDescriptions: {
      markitdown: ["Microsoft MarkItDown", "Converts Office, PDF, HTML, EPUB, and structured data to Markdown."],
      privacy_filter: ["OpenAI Privacy Filter", "Detects PII locally across 8 categories and long context."],
      parakeet: ["NVIDIA Parakeet v3", "Multilingual transcription with punctuation, including long recordings."],
      paddle: ["PaddleOCR / PP-StructureV3", "CPU OCR with layout, table, and reading-order reconstruction."],
      glm: ["GLM-OCR Q8", "Local multimodal OCR through Ollama; a slower mode for complex documents."],
      picocrypt: ["Picocrypt 1.49", ".pcv volumes with XChaCha20, Argon2id, and recovery options."],
    },
    messages: {
      apiError: "Error",
      remove: "Remove",
      enginePrivacy: "Privacy engine",
      engine: "Engine",
      addFile: "Add at least one file.",
      jobsAdded: (count) => `${count} job${count === 1 ? "" : "s"} added to the local queue.`,
      sendFailed: "Submission failed.",
      connectionLost: "Connection to the local service was interrupted.",
      passwordLength: "Use a passphrase of at least 10 characters.",
      passwordMismatch: "The two passphrases do not match.",
      decryptOnlyPcv: "Select .pcv volumes only for decryption.",
      recentEmpty: "Your jobs will appear here.",
      queueEmpty: "The queue is empty.",
      downloadResult: "Download result",
      downloadZip: "Download ZIP package",
      progress: "Progress",
      size: "Size",
      items: "Items",
      review: "The result always requires human review before sharing.",
      enginesReady: (ready, total) => `${ready}/${total} engines ready`,
      ready: "Ready",
      prepare: "Needs setup",
      serviceUnavailable: "Service unavailable",
      vaultEmpty: "The vault is empty.",
      decrypt: "Decrypt",
      decryptQueued: "Decryption added to the queue.",
    },
  },
};

const locale = () => locales[state.language];
const message = (key) => locale().messages[key];
const text = (key) => locale().text[key] || key;

const serverTranslations = {
  "In coda": "Queued",
  "In corso": "Running",
  Completato: "Completed",
  Errore: "Error",
  "Operazione non completata": "Operation not completed",
  "Ripresa dopo il riavvio": "Resumed after restart",
  "Password non conservata: ripetere l’operazione": "Passphrase not retained: repeat the operation",
  "Avvio elaborazione locale": "Starting local processing",
  "Caricamento modelli PaddleOCR": "Loading PaddleOCR models",
  "Caricamento PP-StructureV3": "Loading PP-StructureV3",
  "Caricamento OpenAI Privacy Filter (CPU)": "Loading OpenAI Privacy Filter (CPU)",
  "Creazione del rapporto privacy": "Creating the privacy report",
  "Caricamento NVIDIA Parakeet TDT 0.6B v3": "Loading NVIDIA Parakeet TDT 0.6B v3",
  "Scrittura copie anonimizzate": "Writing redacted copies",
  "PDF senza testo: avvio OCR automatico": "PDF has no text: starting automatic OCR",
  "Anonimizzazione locale completata": "Local redaction completed",
  "Normalizzazione audio con FFmpeg": "Normalizing audio with FFmpeg",
  "Trascrizione completata": "Transcription completed",
  "Preparazione immagine per GLM-OCR": "Preparing image for GLM-OCR",
  "GLM-OCR completato": "GLM-OCR completed",
  "PaddleOCR completato": "PaddleOCR completed",
  "Preparazione volume Picocrypt": "Preparing Picocrypt volume",
  "Cifratura Picocrypt in corso": "Picocrypt encryption in progress",
  "Volume salvato nella cassaforte": "Volume saved to the vault",
  "Decifratura Picocrypt in corso": "Picocrypt decryption in progress",
  "File decifrato": "File decrypted",
  "Lettura locale con Microsoft MarkItDown": "Reading locally with Microsoft MarkItDown",
  "Documento convertito in Markdown": "Document converted to Markdown",
  pronto: "ready",
  "Modello da scaricare al primo uso": "Model downloads on first use",
  "Modello non disponibile": "Model unavailable",
  "Non installato": "Not installed",
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
  return new Intl.DateTimeFormat(locale().dateLocale, {
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
  if (!response.ok) throw new Error(payload.detail || `${message("apiError")} ${response.status}`);
  return payload;
}

function localizeServerText(value) {
  if (!value || state.language === "it") return value || "";
  if (serverTranslations[value]) return serverTranslations[value];
  return value
    .replace(/^PaddleOCR: pagina (\d+)$/, "PaddleOCR: page $1")
    .replace(/^PP-StructureV3: pagina (\d+)$/, "PP-StructureV3: page $1")
    .replace(/^Preparazione pagina (\d+)\/(\d+)$/, "Preparing page $1/$2")
    .replace(/^GLM-OCR: pagina (\d+)\/(\d+)$/, "GLM-OCR: page $1/$2")
    .replace(/^Privacy Filter: blocco (\d+)\/(\d+)$/, "Privacy Filter: chunk $1/$2")
    .replace(/^Parakeet v3: blocco (\d+)\/(\d+)$/, "Parakeet v3: chunk $1/$2");
}

function applyTranslations() {
  document.documentElement.lang = state.language;
  $$("[data-i18n]").forEach((node) => {
    node.textContent = text(node.dataset.i18n);
  });
  $$("[data-i18n-html]").forEach((node) => {
    node.innerHTML = text(node.dataset.i18nHtml);
  });
  $$("[data-i18n-aria]").forEach((node) => {
    node.setAttribute("aria-label", text(node.dataset.i18nAria));
  });
  $$("[data-i18n-placeholder]").forEach((node) => {
    node.setAttribute("placeholder", text(node.dataset.i18nPlaceholder));
  });
  $$("[data-language]").forEach((node) => {
    const active = node.dataset.language === state.language;
    node.classList.toggle("active", active);
    node.setAttribute("aria-pressed", String(active));
  });
  if (!state.status) $("#engine-summary").textContent = text("status.checking");
}

function setLanguage(language) {
  state.language = language === "en" ? "en" : "it";
  localStorage.setItem("privacy-studio-language", state.language);
  applyTranslations();
  $("#page-title").textContent = locale().viewTitles[state.view];
  updateOperation();
  renderSelectedFiles("studioFiles");
  renderSelectedFiles("vaultFiles");
  renderJobs();
  if (state.status) renderStatus(state.status);
  if (state.view === "vault") loadVault();
}

function setView(name) {
  state.view = name;
  $$(".view").forEach((node) => node.classList.toggle("active", node.id === `view-${name}`));
  $$("[data-view-link]").forEach((node) => node.classList.toggle("active", node.dataset.viewLink === name));
  $("#page-title").textContent = locale().viewTitles[name];
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
      <button type="button" data-remove-file="${bucket}:${index}" aria-label="${escapeHtml(message("remove"))}">×</button>
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
  $("#engine-select").innerHTML = locale().engineOptions[operation]
    .map(([value, label]) => `<option value="${value}">${escapeHtml(label)}</option>`)
    .join("");
  $("#engine-help").textContent = locale().operationHelp[operation].help;
  $("#engine-label").textContent = operation === "anonymize" ? message("enginePrivacy") : message("engine");
  $("#process-note-text").textContent = locale().operationHelp[operation].note;
  $("#dates-option").classList.toggle("hidden", operation !== "anonymize");
  $("#chunk-option").classList.toggle("hidden", operation !== "transcribe");
}

function uploadJobs({ files, operation, engine, extras = {}, onDone, onFinally }) {
  if (!files.length) {
    toast(message("addFile"), true);
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
      toast(message("jobsAdded")(payload.jobs.length));
      onDone?.();
      loadJobs();
    } else {
      let detail = message("sendFailed");
      try { detail = JSON.parse(xhr.responseText).detail || detail; } catch {}
      toast(localizeServerText(detail), true);
    }
    onFinally?.();
  });
  xhr.addEventListener("error", () => {
    progressBox.classList.add("hidden");
    toast(message("connectionLost"), true);
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
  if (password.length < 10) return toast(message("passwordLength"), true);
  if (operation === "vault_encrypt" && password !== confirm) {
    return toast(message("passwordMismatch"), true);
  }
  if (operation === "vault_decrypt" && state.vaultFiles.some((file) => !file.name.toLowerCase().endsWith(".pcv"))) {
    return toast(message("decryptOnlyPcv"), true);
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
        <span class="job-type">${escapeHtml(locale().operationNames[job.operation] || job.operation)}</span>
        <span class="status ${job.status}">${escapeHtml(locale().statusNames[job.status] || job.status)}</span>
      </div>
      <h4 title="${escapeHtml(job.input_name)}">${escapeHtml(job.input_name)}</h4>
      <p>${escapeHtml(localizeServerText(job.stage) || humanDate(job.created_at))}</p>
      <div class="progress-track"><span style="width:${percent}%"></span></div>
    </article>
  `;
}

function renderJobs() {
  const recent = state.jobs.slice(0, 6);
  $("#recent-jobs").innerHTML = recent.length
    ? recent.slice(0, 3).map(jobCard).join("")
    : `<div class="empty-state">${escapeHtml(message("recentEmpty"))}</div>`;
  $("#all-jobs").innerHTML = state.jobs.length
    ? state.jobs.map((job) => {
        const percent = Math.round((job.progress || 0) * 100);
        return `
          <article class="job-row" data-job-id="${job.id}">
            <span class="job-type">${escapeHtml(locale().operationNames[job.operation] || job.operation)}</span>
            <div>
              <h4>${escapeHtml(job.input_name)}</h4>
              <p>${escapeHtml(localizeServerText(job.stage))} · ${humanSize(job.input_size)}</p>
            </div>
            <div class="progress-inline"><div><span style="width:${percent}%"></span></div>${percent}%</div>
            <span class="status ${job.status}">${escapeHtml(locale().statusNames[job.status] || job.status)}</span>
          </article>
        `;
      }).join("")
    : `<div class="empty-state">${escapeHtml(message("queueEmpty"))}</div>`;
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
      <a class="primary-button" href="/api/jobs/${job.id}/download">${escapeHtml(message("downloadResult"))}</a>
      ${job.bundle_path ? `<a class="secondary-button" href="/api/jobs/${job.id}/download?kind=bundle">${escapeHtml(message("downloadZip"))}</a>` : ""}
    </div>
  ` : "";
  $("#job-detail").innerHTML = `
    <div class="detail-title">
      <p class="eyebrow">${escapeHtml(locale().operationNames[job.operation] || job.operation)}</p>
      <h2>${escapeHtml(job.input_name)}</h2>
      <p>${escapeHtml(localizeServerText(job.stage))} · ${humanDate(job.updated_at)}</p>
    </div>
    <div class="detail-stats">
      <div class="detail-stat"><strong>${Math.round(job.progress * 100)}%</strong><small>${escapeHtml(message("progress"))}</small></div>
      <div class="detail-stat"><strong>${humanSize(job.input_size)}</strong><small>${escapeHtml(message("size"))}</small></div>
      <div class="detail-stat"><strong>${result.detections ?? result.pages ?? result.chunks ?? "—"}</strong><small>${escapeHtml(message("items"))}</small></div>
    </div>
    ${job.error ? `<div class="detail-error">${escapeHtml(localizeServerText(job.error))}</div>` : ""}
    ${countHtml}
    ${result.review_required ? `<div class="process-note"><span>!</span><p>${escapeHtml(message("review"))}</p></div>` : ""}
    ${downloads}
  `;
  $("#job-dialog").showModal();
}

function renderStatus(payload) {
  const entries = Object.entries(payload.engines);
  const ready = entries.filter(([, value]) => value.ready && value.model_ready).length;
  $("#engine-summary").textContent = message("enginesReady")(ready, entries.length);
  $("#engine-grid").innerHTML = entries.map(([key, value]) => {
    const [name, description] = locale().engineDescriptions[key] || [key, ""];
    const fullyReady = value.ready && value.model_ready;
    return `
      <article class="engine-card">
        <div class="engine-card-head">
          <h3>${escapeHtml(name)}</h3>
          <span class="ready-badge${fullyReady ? "" : " no"}">${escapeHtml(fullyReady ? message("ready") : message("prepare"))}</span>
        </div>
        <p>${escapeHtml(description)}</p>
        <div class="engine-model${value.model_ready ? "" : " no"}">${escapeHtml(localizeServerText(value.detail))}</div>
      </article>
    `;
  }).join("");
}

async function loadStatus() {
  try {
    const payload = await api("/api/status");
    state.status = payload;
    renderStatus(payload);
  } catch (error) {
    $("#engine-summary").textContent = message("serviceUnavailable");
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
            <button type="button" data-decrypt-volume="${escapeHtml(volume.name)}">${escapeHtml(message("decrypt"))}</button>
          </div>
        `).join("")
      : `<div class="empty-state">${escapeHtml(message("vaultEmpty"))}</div>`;
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
    toast(message("decryptQueued"));
    loadJobs();
  } catch (error) {
    toast(error.message, true);
  }
}

document.addEventListener("click", (event) => {
  const language = event.target.closest("[data-language]");
  if (language) setLanguage(language.dataset.language);
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
applyTranslations();
updateOperation();
renderIcons();
loadJobs();
loadStatus();
setInterval(loadJobs, 2500);
setInterval(loadStatus, 60000);
