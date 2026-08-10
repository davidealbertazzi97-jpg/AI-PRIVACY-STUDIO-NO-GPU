const state = {
  studioFiles: [],
  vaultFiles: [],
  vaultGroupFiles: [],
  jobs: [],
  status: null,
  preview: null,
  previewQueue: null,
  permanentVault: {
    session: null,
    exists: false,
    unlocked: false,
    files: [],
    query: "",
  },
  view: "studio",
  language: localStorage.getItem("privacy-studio-language") === "en" ? "en" : "it",
  excludedCategories: [],
};

try {
  const savedCategories = JSON.parse(localStorage.getItem("privacy-studio-excluded-categories") || "[]");
  if (Array.isArray(savedCategories)) state.excludedCategories = savedCategories.filter((item) => typeof item === "string");
} catch {}

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
      "vault.title": "Proteggi i tuoi file.<br><span>Nel modo giusto.</span>",
      "vault.description": "Scegli tra un documento cifrato indipendente e un vault persistente da aprire e aggiornare nel tempo.",
      "vault.guideSingleTitle": "Documento singolo",
      "vault.guideSingleDetail": "Un file → un volume .pcv indipendente",
      "vault.guideManagerTitle": "Vault persistente",
      "vault.guideManagerDetail": "Una cassaforte da aprire, aggiornare e bloccare",
      "vault.singleLabel": "01 · DOCUMENTI SINGOLI",
      "vault.singleTitle": "Cripta un documento alla volta",
      "vault.singleDetail": "Usa questa area quando vuoi consegnare o archiviare un singolo file cifrato. Il risultato è un volume .pcv autonomo.",
      "vault.singleStep1Title": "Seleziona un documento",
      "vault.singleStep1Detail": "Il file originale non viene modificato.",
      "vault.singleStep2Title": "Imposta una passphrase",
      "vault.singleStep2Detail": "Usa almeno 10 caratteri e conservala separatamente.",
      "vault.singleStep3Title": "Scarica il volume",
      "vault.singleStep3Detail": "Riceverai un .pcv da aprire solo con la passphrase.",
      "vault.singleFilesLabel": "DOCUMENTO DA CIFRARE O VOLUME DA DECIFRARE",
      "vault.singleDropTitle": "Trascina qui un documento",
      "vault.singleDropDetail": "Per la decifratura seleziona un volume .pcv",
      "vault.singlePasswordHint": "La passphrase non viene salvata.",
      "vault.encryptSingle": "Cifra questo documento",
      "vault.decryptSingle": "Decifra questo volume .pcv",
      "vault.managerLabel": "02 · VAULT CRIPTATI",
      "vault.managerTitle": "Crea e gestisci una cassaforte persistente",
      "vault.managerDetail": "Questo è il flusso in stile Cryptomator: crei il vault una volta, poi lo apri, aggiungi documenti, li scarichi o li elimini senza ricostruire tutto.",
      "vault.managerHintTitle": "Come usarlo",
      "vault.managerHintDetail": "Crea o apri il vault con la password. Quando hai finito, usa “Blocca vault”: senza password i documenti non sono leggibili.",
      "vault.portableLabel": "VAULT PORTATILE",
      "vault.portableTitle": "Raccogli più documenti in un unico .pcv",
      "vault.portableDetail": "Crea un volume unico da spostare o consegnare. È separato dal vault permanente e non si aggiorna automaticamente.",
      "vault.portableFilesLabel": "DOCUMENTI DA RACCOGLIERE",
      "vault.portableDropTitle": "Trascina più documenti",
      "vault.portableDropDetail": "Verranno cifrati insieme in un solo volume",
      "vault.createPortable": "Crea volume portatile",
      "vault.filesLabel": "FILE DA PROTEGGERE O APRIRE",
      "vault.dropTitle": "Trascina file o volumi .pcv",
      "vault.dropDetail": "Cifra, scarica, decifra o elimina i tuoi volumi locali",
      "vault.passphrase": "Passphrase",
      "vault.passphrasePlaceholder": "Una frase lunga e unica",
      "vault.confirm": "Conferma passphrase",
      "vault.confirmPlaceholder": "Ripetila",
      "vault.paranoid": "Modalità paranoica",
      "vault.paranoidDetail": "Cascata XChaCha20 + Serpent; molto più lenta",
      "vault.recovery": "Correzione errori",
      "vault.recoveryDetail": "Reed–Solomon per archiviazione di lungo periodo",
      "vault.encrypt": "Cifra documenti",
      "vault.decrypt": "Decifra .pcv",
      "vault.groupName": "Nome del vault",
      "vault.groupNamePlaceholder": "Documenti del progetto",
      "vault.groupTitle": "Crea un vault locale",
      "vault.groupDetail": "Più documenti in un solo volume Picocrypt cifrato.",
      "vault.createGroup": "Crea vault locale",
      "vault.download": "Scarica",
      "vault.delete": "Elimina",
      "vault.file": "Documento cifrato",
      "vault.group": "Vault di gruppo",
      "vault.dictionary": "Dizionario reversibile",
      "vault.localVolumes": "VOLUMI PCV LOCALI",
      "vault.contents": "Volumi creati dai documenti singoli",
      "vault.refresh": "Aggiorna cassaforte",
      "vault.permanentLabel": "VAULT PERMANENTE",
      "vault.permanentTitle": "I tuoi documenti, sempre nella cassaforte",
      "vault.localOnly": "Locale e cifrato",
      "vault.permanentDetail": "Un archivio incrementale protetto da password: aprilo, cerca i documenti e scaricali senza ricreare tutto il vault.",
      "vault.createPermanent": "Crea vault permanente",
      "vault.unlockPermanent": "Apri vault",
      "vault.lockPermanent": "Blocca vault",
      "vault.permanentPassword": "Password del vault permanente",
      "vault.permanentPasswordPlaceholder": "Almeno 10 caratteri",
      "vault.permanentConfirm": "Conferma password",
      "vault.permanentConfirmPlaceholder": "Ripetila per creare il vault",
      "vault.permanentUpload": "Aggiungi documenti",
      "vault.permanentSearch": "Cerca per nome…",
      "vault.permanentBackupFolder": "Cartella sincronizzata per backup cifrato",
      "vault.permanentBackupPlaceholder": "/percorso/Dropbox/privacy-studio",
      "vault.permanentBackup": "Esegui backup cifrato",
      "vault.permanentRestorePath": "Percorso del backup da ripristinare",
      "vault.permanentRestore": "Ripristina backup",
      "vault.permanentCloudHint": "Indica una cartella già sincronizzata da Dropbox, OneDrive, Nextcloud o altro servizio. Privacy Studio copia solo file già cifrati.",
      "vault.permanentEmpty": "Il vault permanente non contiene ancora documenti.",
      "vault.permanentLocked": "Il vault esiste già. Inserisci la password per aprirlo.",
      "vault.permanentMissing": "Crea il tuo primo vault permanente locale.",
      "vault.permanentOpened": "Vault permanente aperto.",
      "vault.permanentLockedToast": "Vault permanente bloccato.",
      "vault.permanentCreated": "Vault permanente creato e aperto.",
      "vault.permanentUploaded": (count) => `${count} documento/i archiviato/i nel vault permanente.`,
      "vault.permanentBackedUp": (path) => `Backup cifrato creato in: ${path}`,
      "vault.permanentRestored": "Backup cifrato ripristinato.",
      "vault.permanentDeleted": "Documento eliminato dal vault permanente.",
      "vault.permanentDeleteConfirm": (name) => `Eliminare «${name}» dal vault permanente?`,
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
      anonymize_preview: "Preview anonimizzazione",
      transcribe: "Trascrizione",
      ocr: "OCR",
      convert: "Conversione",
      vault_encrypt: "Cifratura",
      vault_decrypt: "Decifratura",
      vault_group_encrypt: "Creazione vault locale",
      vault_group_decrypt: "Apertura vault locale",
    },
    statusNames: {
      queued: "In coda",
      running: "In corso",
      completed: "Completato",
      failed: "Errore",
      consumed: "Confermato",
      discarded: "Annullato",
    },
    viewTitles: {
      studio: "Laboratorio documenti",
      vault: "Cassaforte Picocrypt",
      jobs: "Attività",
      engines: "Motori locali",
    },
    engineOptions: {
      anonymize: [
        ["privacy_filter", "OpenAI Privacy Filter (Tutte le lingue) · locale"],
        ["privacy_filter_rizzo", "Rizzo PII 0.3B di Simone Rizzo (Solo italiano) · locale"],
      ],
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
        help: "Prima di scrivere il risultato puoi rivedere e selezionare ogni rilevazione. L’estrazione del testo viene scelta automaticamente in base al file.",
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
      privacy_filter: ["OpenAI Privacy Filter", "Rileva PII in locale con 8 categorie e contesto lungo (Tutte le lingue)."],
      privacy_filter_rizzo: ["Rizzo PII 0.3B", "Modello ModernBERT di Simone Rizzo per PII in italiano: 22 categorie, CF, P.IVA, CATASTO, DOCID (Solo italiano)."],
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
      previewQueued: "Analisi locale in corso: la preview apparirà appena pronta.",
      previewProgress: (percent) => `Avanzamento preview: ${percent}%`,
      previewStage: "Fase",
      previewTitle: "Rivedi prima di anonimizzare",
      previewIntro: "Seleziona le rilevazioni da sostituire. Gli elementi non selezionati resteranno nel testo in chiaro.",
      previewOriginal: "Testo rilevato",
      previewOutput: "Output che verrà creato",
      previewPdfOriginal: "PDF originale",
      previewPdfRedacted: "PDF redatto",
      previewCategories: "Categorie rilevate",
      previewReplacement: "Sostituisci con",
      previewReplacementPlaceholder: "Segnaposto o testo personalizzato",
      previewDocumentReplacement: "Sostituzione predefinita del documento",
      previewDocumentReplacementPlaceholder: "Applica lo stesso testo a tutte le selezioni",
      previewApplyReplacement: "Applica a tutte",
      previewExtraTitle: "Aggiungi testo da anonimizzare",
      previewExtraPlaceholder: "Parola o frase da proteggere",
      previewExtraAdd: "Aggiungi",
      previewExtraHelp: "Inserisci una parola o una frase: verranno evidenziate tutte le occorrenze trovate nel testo.",
      previewManualLabel: "MANUALE",
      previewExtraAdded: (count) => `${count} occorrenza/e aggiunta/e alla preview.`,
      previewExtraNoMatch: "La parola o frase non è presente nel testo oppure è già coperta da una rilevazione.",
      previewDictionaryTitle: "Dizionario reversibile nella cassaforte (opzionale)",
      previewDictionaryDetail: "Salva la mappa dei valori originali in un volume cifrato separato.",
      previewDictionaryPassword: "Password del dizionario",
      previewDictionaryPasswordPlaceholder: "Almeno 10 caratteri",
      previewDictionaryHint: "La password non viene salvata nel database.",
      previewResidualWarning: "Alcuni valori potrebbero essere rimasti nel testo. Controlla con attenzione la preview.",
      previewShortWarning: "Alcune rilevazioni sono troppo corte per una verifica automatica affidabile.",
      previewSelectAll: "Seleziona tutto",
      previewSelectNone: "Deseleziona tutto",
      previewSelected: (selected, total) => `${selected} di ${total} elementi selezionati`,
      previewConfirm: "Conferma e anonimizza",
      previewCancel: "Annulla preview",
      previewNoDetections: "Nessuna rilevazione trovata. Puoi comunque creare una copia invariata.",
      previewNext: "Preview confermata. Passo al file successivo…",
      previewNoFiles: "Nessun file da anonimizzare.",
      vaultDeleteConfirm: (name) => `Eliminare definitivamente il volume «${name}»?`,
      vaultDeleted: "Volume eliminato dalla cassaforte.",
      vaultGroupQueued: "Creazione del vault locale aggiunta alla coda.",
      residualWarning: "Controllo residui: verifica manualmente il documento prima di condividerlo.",
      dictionarySaved: (name) => `Dizionario cifrato salvato nella cassaforte: ${name}`,
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
      "vault.title": "Protect your files.<br><span>The right way.</span>",
      "vault.description": "Choose between an independent encrypted document and a persistent vault you can open and update over time.",
      "vault.guideSingleTitle": "Single document",
      "vault.guideSingleDetail": "One file → one independent .pcv volume",
      "vault.guideManagerTitle": "Persistent vault",
      "vault.guideManagerDetail": "A safe you can open, update, and lock",
      "vault.singleLabel": "01 · SINGLE DOCUMENTS",
      "vault.singleTitle": "Encrypt one document at a time",
      "vault.singleDetail": "Use this area when you want to deliver or archive one encrypted file. The result is a standalone .pcv volume.",
      "vault.singleStep1Title": "Select one document",
      "vault.singleStep1Detail": "The original file is never modified.",
      "vault.singleStep2Title": "Set a passphrase",
      "vault.singleStep2Detail": "Use at least 10 characters and store it separately.",
      "vault.singleStep3Title": "Download the volume",
      "vault.singleStep3Detail": "You will receive a .pcv that requires the passphrase to open.",
      "vault.singleFilesLabel": "DOCUMENT TO ENCRYPT OR VOLUME TO DECRYPT",
      "vault.singleDropTitle": "Drop one document here",
      "vault.singleDropDetail": "For decryption, select a .pcv volume",
      "vault.singlePasswordHint": "The passphrase is never saved.",
      "vault.encryptSingle": "Encrypt this document",
      "vault.decryptSingle": "Decrypt this .pcv volume",
      "vault.managerLabel": "02 · ENCRYPTED VAULTS",
      "vault.managerTitle": "Create and manage a persistent safe",
      "vault.managerDetail": "This is the Cryptomator-style flow: create the vault once, then open it, add documents, download or delete them without rebuilding everything.",
      "vault.managerHintTitle": "How to use it",
      "vault.managerHintDetail": "Create or open the vault with its password. When finished, use “Lock vault”: without the password, documents cannot be read.",
      "vault.portableLabel": "PORTABLE VAULT",
      "vault.portableTitle": "Collect multiple documents in one .pcv",
      "vault.portableDetail": "Create one volume to move or deliver. It is separate from the permanent vault and does not update automatically.",
      "vault.portableFilesLabel": "DOCUMENTS TO COLLECT",
      "vault.portableDropTitle": "Drop multiple documents",
      "vault.portableDropDetail": "They will be encrypted together in one volume",
      "vault.createPortable": "Create portable volume",
      "vault.filesLabel": "FILES TO PROTECT OR OPEN",
      "vault.dropTitle": "Drop files or .pcv volumes",
      "vault.dropDetail": "Encrypt, download, decrypt, or delete local volumes",
      "vault.passphrase": "Passphrase",
      "vault.passphrasePlaceholder": "A long, unique phrase",
      "vault.confirm": "Confirm passphrase",
      "vault.confirmPlaceholder": "Repeat it",
      "vault.paranoid": "Paranoid mode",
      "vault.paranoidDetail": "XChaCha20 + Serpent cascade; much slower",
      "vault.recovery": "Error correction",
      "vault.recoveryDetail": "Reed–Solomon for long-term storage",
      "vault.encrypt": "Encrypt documents",
      "vault.decrypt": "Decrypt .pcv",
      "vault.groupName": "Vault name",
      "vault.groupNamePlaceholder": "Project documents",
      "vault.groupTitle": "Create a local vault",
      "vault.groupDetail": "Multiple documents in one encrypted Picocrypt volume.",
      "vault.createGroup": "Create local vault",
      "vault.download": "Download",
      "vault.delete": "Delete",
      "vault.file": "Encrypted document",
      "vault.group": "Group vault",
      "vault.dictionary": "Reversible dictionary",
      "vault.localVolumes": "LOCAL PCV VOLUMES",
      "vault.contents": "Volumes created from single documents",
      "vault.refresh": "Refresh vault",
      "vault.permanentLabel": "PERMANENT VAULT",
      "vault.permanentTitle": "Your documents, always in the vault",
      "vault.localOnly": "Local and encrypted",
      "vault.permanentDetail": "A password-protected incremental archive: open it, search documents, and download them without rebuilding the whole vault.",
      "vault.createPermanent": "Create permanent vault",
      "vault.unlockPermanent": "Open vault",
      "vault.lockPermanent": "Lock vault",
      "vault.permanentPassword": "Permanent vault password",
      "vault.permanentPasswordPlaceholder": "At least 10 characters",
      "vault.permanentConfirm": "Confirm password",
      "vault.permanentConfirmPlaceholder": "Repeat it to create the vault",
      "vault.permanentUpload": "Add documents",
      "vault.permanentSearch": "Search by name…",
      "vault.permanentBackupFolder": "Synced folder for encrypted backup",
      "vault.permanentBackupPlaceholder": "/path/Dropbox/privacy-studio",
      "vault.permanentBackup": "Create encrypted backup",
      "vault.permanentRestorePath": "Backup path to restore",
      "vault.permanentRestore": "Restore backup",
      "vault.permanentCloudHint": "Choose a folder already synchronized by Dropbox, OneDrive, Nextcloud, or another service. Privacy Studio copies only files that are already encrypted.",
      "vault.permanentEmpty": "The permanent vault does not contain documents yet.",
      "vault.permanentLocked": "The vault already exists. Enter its password to open it.",
      "vault.permanentMissing": "Create your first permanent local vault.",
      "vault.permanentOpened": "Permanent vault opened.",
      "vault.permanentLockedToast": "Permanent vault locked.",
      "vault.permanentCreated": "Permanent vault created and opened.",
      "vault.permanentUploaded": (count) => `${count} document${count === 1 ? "" : "s"} stored in the permanent vault.`,
      "vault.permanentBackedUp": (path) => `Encrypted backup created at: ${path}`,
      "vault.permanentRestored": "Encrypted backup restored.",
      "vault.permanentDeleted": "Document deleted from the permanent vault.",
      "vault.permanentDeleteConfirm": (name) => `Delete “${name}” from the permanent vault?`,
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
      anonymize_preview: "Redaction preview",
      transcribe: "Transcription",
      ocr: "OCR",
      convert: "Conversion",
      vault_encrypt: "Encryption",
      vault_decrypt: "Decryption",
      vault_group_encrypt: "Local vault creation",
      vault_group_decrypt: "Local vault extraction",
    },
    statusNames: {
      queued: "Queued",
      running: "Running",
      completed: "Completed",
      failed: "Error",
      consumed: "Confirmed",
      discarded: "Cancelled",
    },
    viewTitles: {
      studio: "Document studio",
      vault: "Picocrypt vault",
      jobs: "Activity",
      engines: "Local engines",
    },
    engineOptions: {
      anonymize: [
        ["privacy_filter", "OpenAI Privacy Filter (All languages) · local"],
        ["privacy_filter_rizzo", "Rizzo PII 0.3B by Simone Rizzo (Italian only) · local"],
      ],
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
        help: "Before writing the result you can review and select every detection. Text extraction is selected automatically for each file.",
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
      privacy_filter: ["OpenAI Privacy Filter", "Detects PII locally across 8 categories and long context (All languages)."],
      privacy_filter_rizzo: ["Rizzo PII 0.3B", "Italian PII ModernBERT model by Simone Rizzo: 22 categories, Tax Code, VAT ID, Land Registry (Italian only)."],
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
      previewQueued: "Local analysis is running: the preview will appear when ready.",
      previewProgress: (percent) => `Preview progress: ${percent}%`,
      previewStage: "Stage",
      previewTitle: "Review before redaction",
      previewIntro: "Select the detections to replace. Unselected elements will remain in clear text.",
      previewOriginal: "Detected text",
      previewOutput: "Output that will be created",
      previewPdfOriginal: "Original PDF",
      previewPdfRedacted: "Redacted PDF",
      previewCategories: "Detected categories",
      previewReplacement: "Replace with",
      previewReplacementPlaceholder: "Placeholder or custom text",
      previewDocumentReplacement: "Document-wide replacement",
      previewDocumentReplacementPlaceholder: "Apply the same text to every selection",
      previewApplyReplacement: "Apply to all",
      previewExtraTitle: "Add text to redact",
      previewExtraPlaceholder: "Word or phrase to protect",
      previewExtraAdd: "Add",
      previewExtraHelp: "Enter a word or phrase: every occurrence found in the text will be highlighted.",
      previewManualLabel: "MANUAL",
      previewExtraAdded: (count) => `${count} occurrence${count === 1 ? "" : "s"} added to the preview.`,
      previewExtraNoMatch: "The word or phrase is not in the text or is already covered by a detection.",
      previewDictionaryTitle: "Reversible dictionary in the vault (optional)",
      previewDictionaryDetail: "Save the original-value map in a separate encrypted volume.",
      previewDictionaryPassword: "Dictionary password",
      previewDictionaryPasswordPlaceholder: "At least 10 characters",
      previewDictionaryHint: "The password is never saved in the database.",
      previewResidualWarning: "Some values may still be present in the text. Review the preview carefully.",
      previewShortWarning: "Some detections are too short for a reliable automatic residual check.",
      previewSelectAll: "Select all",
      previewSelectNone: "Select none",
      previewSelected: (selected, total) => `${selected} of ${total} elements selected`,
      previewConfirm: "Confirm and redact",
      previewCancel: "Cancel preview",
      previewNoDetections: "No detections found. You can still create an unchanged copy.",
      previewNext: "Preview confirmed. Moving to the next file…",
      previewNoFiles: "No files to redact.",
      vaultDeleteConfirm: (name) => `Permanently delete the volume “${name}”?`,
      vaultDeleted: "Volume deleted from the vault.",
      vaultGroupQueued: "Local vault creation added to the queue.",
      residualWarning: "Residual check: review the document manually before sharing it.",
      dictionarySaved: (name) => `Encrypted dictionary saved in the vault: ${name}`,
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
  "Caricamento Rizzo PII 0.3B (CPU)": "Loading Rizzo PII 0.3B (CPU)",
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
  "Preparazione vault locale": "Preparing local vault",
  "Decifratura vault locale in corso": "Decrypting local vault",
  "Documenti del vault estratti": "Vault documents extracted",
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
  renderSelectedFiles("vaultGroupFiles");
  renderJobs();
  if (state.status) renderStatus(state.status);
  if (state.view === "vault") {
    loadVault();
    loadPermanentVault();
  }
  if (state.preview) {
    const selected = selectedPreviewKeys();
    renderAnonymizationPreview(state.preview.job, selected);
  }
}

function setView(name) {
  state.view = name;
  $$(".view").forEach((node) => node.classList.toggle("active", node.id === `view-${name}`));
  $$("[data-view-link]").forEach((node) => node.classList.toggle("active", node.dataset.viewLink === name));
  $("#page-title").textContent = locale().viewTitles[name];
  if (name === "vault") {
    loadVault();
    loadPermanentVault();
  }
  if (name === "engines") loadStatus();
  if (name === "jobs") renderJobs();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function fileKey(file) {
  return `${file.name}:${file.size}:${file.lastModified}`;
}

function addFiles(bucket, files) {
  const existing = new Set(state[bucket].map(fileKey));
  const incoming = bucket === "vaultFiles" ? [...files].slice(0, 1) : [...files];
  for (const file of incoming) {
    if (!existing.has(fileKey(file))) state[bucket].push(file);
  }
  renderSelectedFiles(bucket);
}

function renderSelectedFiles(bucket) {
  const targetIds = {
    studioFiles: "#studio-file-list",
    vaultFiles: "#vault-file-list",
    vaultGroupFiles: "#vault-group-file-list",
  };
  const target = $(targetIds[bucket]);
  if (!target) return;
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

function pause(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function waitForJob(jobId, onUpdate) {
  for (;;) {
    const job = await api(`/api/jobs/${jobId}`);
    onUpdate?.(job);
    if (["completed", "failed", "discarded", "consumed"].includes(job.status)) return job;
    await pause(900);
  }
}

async function createAnonymizationPreview(file, engine, extras) {
  const form = new FormData();
  form.append("files", file);
  form.append("engine", engine);
  Object.entries(extras).forEach(([key, value]) => form.append(key, String(value)));
  const payload = await api("/api/anonymization-previews", { method: "POST", body: form });
  return payload.job;
}

function previewSpans() {
  if (!state.preview) return [];
  return [
    ...(state.preview.job?.result?.spans || []),
    ...(state.preview.extraSpans || []),
  ];
}

function previewSpanKey(span) {
  return `${Number(span.start)}:${Number(span.end)}:${String(span.label || "")}`;
}

function selectedPreviewKeys() {
  return new Set(
    [...selectedPreviewIndexes()]
      .map((index) => previewSpans()[index])
      .filter(Boolean)
      .map(previewSpanKey),
  );
}

function storedPreviewReplacement(span) {
  return state.preview?.replacements?.[previewSpanKey(span)] || "";
}

function previewReplacement(index, span) {
  const input = $(`#preview-replacement-${index}`);
  return input ? input.value.trim() : storedPreviewReplacement(span);
}

function previewCategoryLabel(label) {
  return label === "manual_text"
    ? message("previewManualLabel")
    : String(label || "PII").replaceAll("_", " ").toUpperCase();
}

function previewCategoryMarkup(spans) {
  const counts = new Map();
  spans.forEach((span) => counts.set(span.label, (counts.get(span.label) || 0) + 1));
  if (!counts.size) return "";
  return `
    <div class="preview-categories">
      <strong>${escapeHtml(message("previewCategories"))}</strong>
      <div class="preview-category-list">
        ${[...counts.entries()].map(([label, count]) => `
          <button type="button" class="preview-category" data-preview-category="${escapeHtml(label)}">
            ${escapeHtml(previewCategoryLabel(label))} · ${count}
          </button>
        `).join("")}
      </div>
    </div>
  `;
}

function selectedPreviewIndexes() {
  return new Set(
    $$("#preview-entity-list input[data-preview-index]:checked")
      .map((input) => Number(input.dataset.previewIndex)),
  );
}

function buildPreviewSource(result, selected) {
  const original = result.original_text || "";
  const spans = previewSpans();
  if (!spans.length) return `<span class="preview-empty">${escapeHtml(message("previewNoDetections"))}</span>`;
  const pieces = [];
  let cursor = 0;
  spans.forEach((span, index) => {
    if (span.start < cursor) return;
    pieces.push(escapeHtml(original.slice(cursor, span.start)));
    const label = previewCategoryLabel(span.label);
    const replacement = storedPreviewReplacement(span);
    pieces.push(
      `<label class="preview-entity" data-preview-entity="${index}">` +
      `<input type="checkbox" data-preview-index="${index}" data-preview-label="${escapeHtml(span.label || "PII")}"${selected.has(index) ? " checked" : ""}>` +
      `<em>${escapeHtml(label)}</em>` +
      `<span class="preview-original">${escapeHtml(span.original || original.slice(span.start, span.end))}</span>` +
      `<input class="preview-replacement" type="text" id="preview-replacement-${index}" data-preview-replacement-index="${index}" value="${escapeHtml(replacement)}" placeholder="${escapeHtml(message("previewReplacement"))}" maxlength="180">` +
      `</label>`,
    );
    cursor = span.end;
  });
  pieces.push(escapeHtml(original.slice(cursor)));
  return pieces.join("");
}

function buildPreviewOutput(result, selected) {
  const original = result.original_text || "";
  const spans = previewSpans();
  if (!spans.length) return escapeHtml(original) || `<span class="preview-empty">${escapeHtml(message("previewNoDetections"))}</span>`;
  const pieces = [];
  let cursor = 0;
  spans.forEach((span, index) => {
    if (span.start < cursor) return;
    pieces.push(escapeHtml(original.slice(cursor, span.start)));
    const custom = previewReplacement(index, span);
    const value = selected.has(index)
      ? (custom || span.placeholder || `[${String(span.label || "PII").toUpperCase()}]`)
      : (span.original || original.slice(span.start, span.end));
    pieces.push(escapeHtml(value));
    cursor = span.end;
  });
  pieces.push(escapeHtml(original.slice(cursor)));
  return pieces.join("");
}

function updatePreviewReplacement(event) {
  if (!state.preview) return;
  const index = Number(event.target.dataset.previewReplacementIndex);
  const span = previewSpans()[index];
  if (!span) return;
  const value = event.target.value.trim();
  state.preview.replacements[previewSpanKey(span)] = value;
  updatePreviewSelection();
}

function applyDocumentReplacement() {
  if (!state.preview) return;
  const value = $("#preview-document-replacement")?.value.trim() || "";
  state.preview.replacements = {};
  if (value) {
    previewSpans().forEach((span) => {
      state.preview.replacements[previewSpanKey(span)] = value;
    });
  }
  $$("#preview-entity-list .preview-replacement").forEach((input) => {
    input.value = value;
  });
  updatePreviewSelection();
}

function addExtraPreviewText() {
  if (!state.preview) return;
  const input = $("#preview-extra-text");
  const phrase = input?.value.trim() || "";
  if (!phrase) return;
  const result = state.preview.job.result || {};
  const original = result.original_text || "";
  const haystack = original.toLocaleLowerCase("it-IT");
  const needle = phrase.toLocaleLowerCase("it-IT");
  const existing = previewSpans();
  const extra = [];
  let offset = 0;
  while (offset < haystack.length) {
    const start = haystack.indexOf(needle, offset);
    if (start === -1) break;
    const end = start + phrase.length;
    const overlaps = existing.some((span) => start < span.end && end > span.start);
    if (!overlaps) {
      extra.push({
        label: "manual_text",
        start,
        end,
        original: original.slice(start, end),
        placeholder: `[TESTO_${String((state.preview.extraSpans || []).length + extra.length + 1).padStart(3, "0")}]`,
        source: "selezione manuale nella preview",
      });
    }
    offset = Math.max(end, start + 1);
  }
  if (!extra.length) {
    toast(message("previewExtraNoMatch"), true);
    return;
  }
  const selected = selectedPreviewKeys();
  state.preview.extraSpans = [...(state.preview.extraSpans || []), ...extra];
  extra.forEach((span) => selected.add(previewSpanKey(span)));
  renderAnonymizationPreview(state.preview.job, selected);
  toast(message("previewExtraAdded")(extra.length));
}

function updatePreviewSelection() {
  if (!state.preview) return;
  const spans = previewSpans();
  const selected = selectedPreviewIndexes();
  $$("#preview-entity-list .preview-entity").forEach((node) => {
    node.classList.toggle("is-off", !selected.has(Number(node.dataset.previewEntity)));
  });
  const count = $("#preview-selected-count");
  if (count) count.textContent = message("previewSelected")(selected.size, spans.length);
  const output = $("#preview-output");
  if (output) output.innerHTML = buildPreviewOutput(state.preview.job.result || {}, selected);
  updatePreviewCategoryControls();
}

function updatePreviewCategoryControls() {
  $$("#preview-category-list .preview-category").forEach((button) => {
    const label = button.dataset.previewCategory;
    const inputs = $$(
      `#preview-entity-list input[data-preview-label="${CSS.escape(label)}"]`,
    );
    const selected = inputs.filter((input) => input.checked).length;
    button.classList.toggle("is-off", selected === 0);
    button.classList.toggle("is-partial", selected > 0 && selected < inputs.length);
  });
}

function togglePreviewCategory(label) {
  const inputs = $$(
    `#preview-entity-list input[data-preview-label="${CSS.escape(label)}"]`,
  );
  if (!inputs.length) return;
  const turnOn = inputs.some((input) => !input.checked);
  inputs.forEach((input) => { input.checked = turnOn; });
  const excluded = new Set(state.excludedCategories || []);
  if (turnOn) excluded.delete(label);
  else excluded.add(label);
  state.excludedCategories = [...excluded];
  localStorage.setItem(
    "privacy-studio-excluded-categories",
    JSON.stringify(state.excludedCategories),
  );
  updatePreviewSelection();
}

function setPreviewSelection(on) {
  $$("#preview-entity-list input[data-preview-index]").forEach((input) => {
    input.checked = on;
  });
  updatePreviewSelection();
}

function renderPreviewLoading(fileName) {
  $("#anonymization-preview-detail").innerHTML = `
    <div class="preview-shell">
      <div class="preview-header">
        <p class="eyebrow">${escapeHtml(message("previewTitle"))}</p>
        <h3>${escapeHtml(fileName)}</h3>
        <p>${escapeHtml(message("previewQueued"))}</p>
      </div>
      <div class="preview-loading" aria-live="polite">
        <div class="preview-progress-meta">
          <strong id="preview-progress-label">${escapeHtml(message("previewProgress")(0))}</strong>
          <span id="preview-progress-stage">${escapeHtml(message("previewQueued"))}</span>
        </div>
        <div class="preview-progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">
          <span id="preview-progress-bar" style="width:0%"></span>
        </div>
      </div>
    </div>
  `;
  const dialog = $("#anonymization-preview-dialog");
  if (!dialog.open) dialog.showModal();
}

function updatePreviewLoading(job) {
  const percent = Math.round(Math.max(0, Math.min(1, Number(job.progress || 0))) * 100);
  const label = $("#preview-progress-label");
  const stage = $("#preview-progress-stage");
  const bar = $("#preview-progress-bar");
  const track = bar?.parentElement;
  if (label) label.textContent = message("previewProgress")(percent);
  if (stage) stage.textContent = localizeServerText(job.stage || message("previewQueued"));
  if (bar) bar.style.width = `${percent}%`;
  if (track) {
    track.setAttribute("aria-valuenow", String(percent));
    track.setAttribute("aria-label", message("previewProgress")(percent));
  }
}

function renderAnonymizationPreview(job, selectedKeys = null) {
  const previous = state.preview?.job?.id === job.id ? state.preview : null;
  state.preview = {
    job,
    extraSpans: previous?.extraSpans || [],
    replacements: previous?.replacements || {},
    dictionary: previous?.dictionary || { save: false, password: "" },
  };
  const result = job.result || {};
  const spans = previewSpans();
  const excluded = new Set(state.excludedCategories || []);
  const selected = new Set(
    spans
      .map((span, index) => (!excluded.has(span.label) ? index : null))
      .filter((index) => index !== null),
  );
  if (selectedKeys) {
    selected.clear();
    spans.forEach((span, index) => {
      if (selectedKeys.has(previewSpanKey(span))) selected.add(index);
    });
  }
  const previewWarning = result.residual_warning
    ? `<div class="preview-warning"><strong>!</strong><span>${escapeHtml(message("previewResidualWarning"))}${result.short_value_labels?.length ? ` ${escapeHtml(message("previewShortWarning"))}` : ""}</span></div>`
    : "";
  const previewPdfWarning = result.pdf_preview_warning
    ? `<div class="preview-warning"><strong>!</strong><span>${escapeHtml(result.pdf_preview_warning)}</span></div>`
    : "";
  const pdfPreview = job.input_name.toLowerCase().endsWith(".pdf") && result.preview_pdf_path
    ? `<div class="preview-pdf-grid">
        <section class="preview-pane"><h4>${escapeHtml(message("previewPdfOriginal"))}</h4><iframe title="${escapeHtml(message("previewPdfOriginal"))}" src="/api/anonymization-previews/${encodeURIComponent(job.id)}/pdf?kind=original"></iframe></section>
        <section class="preview-pane"><h4>${escapeHtml(message("previewPdfRedacted"))}</h4><iframe title="${escapeHtml(message("previewPdfRedacted"))}" src="/api/anonymization-previews/${encodeURIComponent(job.id)}/pdf?kind=redacted"></iframe></section>
      </div>`
    : "";
  $("#anonymization-preview-detail").innerHTML = `
    <div class="preview-shell">
      <div class="preview-header">
        <p class="eyebrow">${escapeHtml(message("previewTitle"))}</p>
        <h3>${escapeHtml(job.input_name)}</h3>
        <p>${escapeHtml(message("previewIntro"))}</p>
      </div>
      <div class="preview-meta">
        <span class="preview-count" id="preview-selected-count">${escapeHtml(message("previewSelected")(spans.length, spans.length))}</span>
        <span class="preview-count">${escapeHtml(job.engine === "privacy_filter_rizzo" ? "Rizzo PII 0.3B" : "OpenAI Privacy Filter")}</span>
      </div>
      ${previewWarning}
      ${previewPdfWarning}
      <div class="preview-toolbar">
        <strong>${escapeHtml(message("previewOriginal"))}</strong>
        <div class="preview-actions">
          <button type="button" class="secondary-button" id="preview-select-all">${escapeHtml(message("previewSelectAll"))}</button>
          <button type="button" class="secondary-button" id="preview-select-none">${escapeHtml(message("previewSelectNone"))}</button>
        </div>
      </div>
      ${previewCategoryMarkup(spans).replace('class="preview-category-list"', 'class="preview-category-list" id="preview-category-list"')}
      <div class="preview-document-replacement">
        <label for="preview-document-replacement">${escapeHtml(message("previewDocumentReplacement"))}</label>
        <div class="preview-extra-form">
          <input type="text" id="preview-document-replacement" maxlength="180" placeholder="${escapeHtml(message("previewDocumentReplacementPlaceholder"))}">
          <button type="button" class="secondary-button" id="preview-apply-replacement">${escapeHtml(message("previewApplyReplacement"))}</button>
        </div>
      </div>
      <div class="preview-extra">
        <div class="preview-extra-heading">
          <strong>${escapeHtml(message("previewExtraTitle"))}</strong>
          <span>${escapeHtml(message("previewExtraHelp"))}</span>
        </div>
        <div class="preview-extra-form">
          <input type="text" id="preview-extra-text" maxlength="500" placeholder="${escapeHtml(message("previewExtraPlaceholder"))}">
          <button type="button" class="secondary-button" id="preview-add-extra">${escapeHtml(message("previewExtraAdd"))}</button>
        </div>
      </div>
      ${pdfPreview}
      <div class="preview-text-grid">
        <section class="preview-pane">
          <h4>${escapeHtml(message("previewOriginal"))}</h4>
          <div class="preview-document" id="preview-entity-list">${buildPreviewSource(result, selected)}</div>
        </section>
        <section class="preview-pane">
          <h4>${escapeHtml(message("previewOutput"))}</h4>
          <div class="preview-document preview-output" id="preview-output">${buildPreviewOutput(result, selected)}</div>
        </section>
      </div>
      <div class="preview-actions">
        <button type="button" class="secondary-button" id="preview-cancel">${escapeHtml(message("previewCancel"))}</button>
        <div class="preview-dictionary">
          <label class="check-row">
            <input type="checkbox" id="preview-save-dictionary"${state.preview.dictionary.save ? " checked" : ""}>
            <span>
              <strong>${escapeHtml(message("previewDictionaryTitle"))}</strong>
              <small>${escapeHtml(message("previewDictionaryDetail"))}</small>
            </span>
          </label>
          <label class="field${state.preview.dictionary.save ? "" : " hidden"}" id="preview-dictionary-password-wrap">
            <span>${escapeHtml(message("previewDictionaryPassword"))}</span>
            <input type="password" id="preview-dictionary-password" minlength="10" autocomplete="new-password" value="${escapeHtml(state.preview.dictionary.password)}" placeholder="${escapeHtml(message("previewDictionaryPasswordPlaceholder"))}">
            <small>${escapeHtml(message("previewDictionaryHint"))}</small>
          </label>
        </div>
        <button type="button" class="primary-button" id="preview-confirm">${escapeHtml(message("previewConfirm"))}</button>
      </div>
    </div>
  `;
  $("#preview-select-all").addEventListener("click", () => setPreviewSelection(true));
  $("#preview-select-none").addEventListener("click", () => setPreviewSelection(false));
  $("#preview-cancel").addEventListener("click", discardAnonymizationPreview);
  $("#preview-confirm").addEventListener("click", confirmAnonymizationPreview);
  $("#preview-entity-list").addEventListener("change", updatePreviewSelection);
  $("#preview-entity-list").addEventListener("input", updatePreviewReplacement);
  $("#preview-category-list")?.addEventListener("click", (event) => {
    const category = event.target.closest("[data-preview-category]");
    if (category) togglePreviewCategory(category.dataset.previewCategory);
  });
  $("#preview-apply-replacement").addEventListener("click", applyDocumentReplacement);
  $("#preview-add-extra").addEventListener("click", addExtraPreviewText);
  $("#preview-extra-text").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addExtraPreviewText();
    }
  });
  $("#preview-save-dictionary").addEventListener("change", (event) => {
    state.preview.dictionary.save = event.target.checked;
    $("#preview-dictionary-password-wrap").classList.toggle("hidden", !event.target.checked);
  });
  $("#preview-dictionary-password").addEventListener("input", (event) => {
    state.preview.dictionary.password = event.target.value;
  });
  updatePreviewSelection();
  const dialog = $("#anonymization-preview-dialog");
  if (!dialog.open) dialog.showModal();
}

async function openNextAnonymizationPreview() {
  const queue = state.previewQueue;
  if (!queue || !queue.remaining.length) {
    state.previewQueue = null;
    toast(message("jobsAdded")(queue?.submitted || 0));
    loadJobs();
    return;
  }
  const file = queue.remaining.shift();
  renderPreviewLoading(file.name);
  try {
    const queued = await createAnonymizationPreview(file, queue.engine, queue.extras);
    if (state.previewQueue !== queue) {
      const cancelled = await waitForJob(queued.id);
      if (cancelled.status === "completed") {
        await api(`/api/anonymization-previews/${queued.id}/discard`, { method: "POST" });
      }
      return;
    }
    queue.currentId = queued.id;
    const job = await waitForJob(queued.id, updatePreviewLoading);
    if (state.previewQueue !== queue) return;
    if (job.status !== "completed") throw new Error(job.error || message("sendFailed"));
    renderAnonymizationPreview(job);
    loadJobs();
  } catch (error) {
    state.preview = null;
    state.previewQueue = null;
    $("#anonymization-preview-dialog").close();
    toast(localizeServerText(error.message), true);
  }
}

async function startAnonymizationPreview(files, engine, extras) {
  if (state.previewQueue || state.preview) return toast(message("previewQueued"), true);
  if (!files.length) return toast(message("addFile"), true);
  state.previewQueue = {
    remaining: [...files],
    engine,
    extras,
    currentId: null,
    submitted: 0,
  };
  await openNextAnonymizationPreview();
}

async function confirmAnonymizationPreview() {
  const current = state.preview;
  const queue = state.previewQueue;
  if (!current || !queue) return;
  const button = $("#preview-confirm");
  button.disabled = true;
  const selected = [...selectedPreviewIndexes()].map((index) => {
    const span = previewSpans()[index];
    const item = { start: span.start, end: span.end, label: span.label };
    const replacement = previewReplacement(index, span);
    if (replacement) item.replacement = replacement;
    return item;
  });
  const saveDictionary = $("#preview-save-dictionary")?.checked || false;
  const dictionaryPassword = $("#preview-dictionary-password")?.value || "";
  if (saveDictionary && dictionaryPassword.length < 10) {
    button.disabled = false;
    toast(message("passwordLength"), true);
    $("#preview-dictionary-password")?.focus();
    return;
  }
  try {
    await api(`/api/anonymization-previews/${current.job.id}/commit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        selected_spans: selected,
        save_dictionary: saveDictionary,
        dictionary_password: saveDictionary ? dictionaryPassword : null,
      }),
    });
    queue.submitted += 1;
    state.preview = null;
    $("#anonymization-preview-dialog").close();
    if (queue.remaining.length) toast(message("previewNext"));
    await openNextAnonymizationPreview();
  } catch (error) {
    button.disabled = false;
    toast(localizeServerText(error.message), true);
  }
}

async function discardAnonymizationPreview() {
  const current = state.preview;
  const queue = state.previewQueue;
  state.preview = null;
  state.previewQueue = null;
  if (current?.job?.id) {
    try {
      await api(`/api/anonymization-previews/${current.job.id}/discard`, { method: "POST" });
    } catch (error) {
      console.error(error);
    }
  }
  $("#anonymization-preview-dialog").close();
  if (queue?.remaining?.length) {
    state.studioFiles = queue.remaining;
    renderSelectedFiles("studioFiles");
  }
  toast(message("previewCancel"));
}

function submitStudio(event) {
  event.preventDefault();
  const operation = currentOperation();
  const button = $("#studio-submit");
  if (operation === "anonymize") {
    button.disabled = true;
    const files = [...state.studioFiles];
    state.studioFiles = [];
    renderSelectedFiles("studioFiles");
    startAnonymizationPreview(files, $("#engine-select").value, {
      include_dates: $("#include-dates").checked,
    }).finally(() => { button.disabled = false; });
    return;
  }
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

function submitVaultGroup() {
  const password = $("#vault-group-password").value;
  const confirm = $("#vault-group-confirm").value;
  if (!state.vaultGroupFiles.length) return toast(message("addFile"), true);
  if (password.length < 10) return toast(message("passwordLength"), true);
  if (password !== confirm) return toast(message("passwordMismatch"), true);
  const form = new FormData();
  state.vaultGroupFiles.forEach((file) => form.append("files", file));
  form.append("group_name", $("#vault-group-name").value.trim() || "vault-documenti");
  form.append("password", password);
  form.append("paranoid", String($("#vault-group-paranoid").checked));
  form.append("recovery", String($("#vault-group-recovery").checked));
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
      state.vaultGroupFiles = [];
      renderSelectedFiles("vaultGroupFiles");
      $("#vault-group-password").value = "";
      $("#vault-group-confirm").value = "";
      $("#vault-group-name").value = "";
      toast(message("vaultGroupQueued"));
      loadJobs();
      loadVault();
    } else {
      let detail = message("sendFailed");
      try { detail = JSON.parse(xhr.responseText).detail || detail; } catch {}
      toast(localizeServerText(detail), true);
    }
  });
  xhr.addEventListener("error", () => {
    progressBox.classList.add("hidden");
    progressBar.style.width = "0";
    toast(message("connectionLost"), true);
  });
  xhr.open("POST", "/api/vault/groups");
  xhr.send(form);
}

function permanentVaultHeaders(headers = {}) {
  const merged = new Headers(headers);
  const session = state.permanentVault.session;
  if (session) merged.set("X-Privacy-Studio-Vault-Session", session);
  return merged;
}

async function permanentVaultApi(path, options = {}) {
  return api(path, {
    ...options,
    headers: permanentVaultHeaders(options.headers),
  });
}

function renderPermanentVault() {
  const target = $("#permanent-vault-panel");
  if (!target) return;
  const vault = state.permanentVault;
  if (!vault.unlocked) {
    const action = vault.exists ? "unlock" : "create";
    target.innerHTML = `
      <div class="permanent-vault-locked">
        <div class="permanent-vault-status">
          <i data-lucide="${vault.exists ? "lock-keyhole" : "sparkles"}"></i>
          <p>${escapeHtml(vault.exists ? message("vault.permanentLocked") : message("vault.permanentMissing"))}</p>
        </div>
        <form id="permanent-vault-auth" class="permanent-vault-auth">
          <label class="field">
            <span>${escapeHtml(message("vault.permanentPassword"))}</span>
            <input type="password" id="permanent-vault-password" minlength="10" autocomplete="new-password" required placeholder="${escapeHtml(message("vault.permanentPasswordPlaceholder"))}">
          </label>
          ${action === "create" ? `<label class="field"><span>${escapeHtml(message("vault.permanentConfirm"))}</span><input type="password" id="permanent-vault-confirm" minlength="10" autocomplete="new-password" required placeholder="${escapeHtml(message("vault.permanentConfirmPlaceholder"))}"></label>` : ""}
          <button type="submit" class="primary-button"><i data-lucide="${action === "create" ? "vault" : "unlock"}"></i> ${escapeHtml(action === "create" ? message("vault.createPermanent") : message("vault.unlockPermanent"))}</button>
        </form>
        <div class="permanent-vault-restore">
          <label class="field">
            <span>${escapeHtml(message("vault.permanentRestorePath"))}</span>
            <input type="text" id="permanent-vault-restore-path" placeholder="/percorso/privacy-studio-vault-…">
          </label>
          <button type="button" class="secondary-button" id="permanent-vault-restore"><i data-lucide="archive-restore"></i> ${escapeHtml(message("vault.permanentRestore"))}</button>
        </div>
      </div>
    `;
    $("#permanent-vault-auth").addEventListener("submit", unlockOrCreatePermanentVault);
    $("#permanent-vault-restore").addEventListener("click", restorePermanentVault);
    renderIcons();
    return;
  }

  target.innerHTML = `
    <div class="permanent-vault-open">
      <div class="permanent-vault-toolbar">
        <div class="permanent-vault-actions">
          <label class="file-button secondary-button"><i data-lucide="file-up"></i> ${escapeHtml(message("vault.permanentUpload"))}<input type="file" id="permanent-vault-files" multiple></label>
          <button type="button" class="secondary-button" id="permanent-vault-lock"><i data-lucide="lock-keyhole"></i> ${escapeHtml(message("vault.lockPermanent"))}</button>
        </div>
        <input type="search" id="permanent-vault-search" value="${escapeHtml(vault.query)}" placeholder="${escapeHtml(message("vault.permanentSearch"))}">
      </div>
      <div class="permanent-vault-files" id="permanent-vault-file-list">
        ${vault.files.length ? vault.files.map((file) => `
          <div class="permanent-vault-file">
            <div><strong>${escapeHtml(file.name)}</strong><small>${humanSize(file.size)} · ${humanDate(file.updated_at)}</small></div>
            <div class="vault-item-actions"><button type="button" data-permanent-download="${escapeHtml(file.id)}" data-permanent-name="${escapeHtml(file.name)}"><i data-lucide="download"></i> ${escapeHtml(message("vault.download"))}</button><button type="button" class="danger" data-permanent-delete="${escapeHtml(file.id)}" data-permanent-name="${escapeHtml(file.name)}">${escapeHtml(message("vault.delete"))}</button></div>
          </div>
        `).join("") : `<div class="empty-state">${escapeHtml(message("vault.permanentEmpty"))}</div>`}
      </div>
      <div class="permanent-vault-backup">
        <div><strong>${escapeHtml(message("vault.permanentBackup"))}</strong><small>${escapeHtml(message("vault.permanentCloudHint"))}</small></div>
        <div class="permanent-vault-backup-row"><input type="text" id="permanent-vault-backup-path" placeholder="${escapeHtml(message("vault.permanentBackupPlaceholder"))}"><button type="button" class="secondary-button" id="permanent-vault-backup"><i data-lucide="cloud-upload"></i> ${escapeHtml(message("vault.permanentBackup"))}</button></div>
      </div>
    </div>
  `;
  $("#permanent-vault-files").addEventListener("change", uploadPermanentVaultFiles);
  $("#permanent-vault-lock").addEventListener("click", lockPermanentVault);
  $("#permanent-vault-search").addEventListener("input", (event) => {
    state.permanentVault.query = event.target.value;
    clearTimeout(state.permanentVault.searchTimer);
    state.permanentVault.searchTimer = setTimeout(() => loadPermanentVaultFiles(), 180);
  });
  $("#permanent-vault-backup").addEventListener("click", backupPermanentVault);
  renderIcons();
}

async function loadPermanentVault() {
  try {
    const payload = await api("/api/permanent-vault", {
      headers: permanentVaultHeaders(),
    });
    state.permanentVault.exists = Boolean(payload.exists);
    state.permanentVault.unlocked = Boolean(payload.unlocked);
    if (!state.permanentVault.unlocked) {
      state.permanentVault.session = null;
      state.permanentVault.files = [];
    } else {
      await loadPermanentVaultFiles();
    }
    renderPermanentVault();
  } catch (error) {
    console.error(error);
  }
}

async function loadPermanentVaultFiles() {
  if (!state.permanentVault.unlocked) return;
  try {
    const payload = await permanentVaultApi(`/api/permanent-vault/files?q=${encodeURIComponent(state.permanentVault.query || "")}`);
    state.permanentVault.files = payload.files || [];
    renderPermanentVault();
  } catch (error) {
    if (error.message.includes("Sblocca") || error.message.includes("sessione")) {
      state.permanentVault.session = null;
      state.permanentVault.unlocked = false;
    }
    toast(localizeServerText(error.message), true);
    renderPermanentVault();
  }
}

async function unlockOrCreatePermanentVault(event) {
  event.preventDefault();
  const password = $("#permanent-vault-password").value;
  const confirm = $("#permanent-vault-confirm")?.value;
  const creating = !state.permanentVault.exists;
  if (password.length < 10) return toast(message("passwordLength"), true);
  if (creating && password !== confirm) return toast(message("passwordMismatch"), true);
  const form = new FormData();
  form.append("password", password);
  try {
    const payload = await api(`/api/permanent-vault/${creating ? "create" : "unlock"}`, { method: "POST", body: form });
    state.permanentVault.session = payload.session;
    state.permanentVault.exists = true;
    state.permanentVault.unlocked = true;
    toast(message(creating ? "vault.permanentCreated" : "vault.permanentOpened"));
    await loadPermanentVaultFiles();
    renderPermanentVault();
  } catch (error) {
    toast(localizeServerText(error.message), true);
  }
}

async function lockPermanentVault() {
  try {
    await permanentVaultApi("/api/permanent-vault/lock", { method: "POST" });
  } catch (error) {
    console.error(error);
  }
  state.permanentVault.session = null;
  state.permanentVault.unlocked = false;
  state.permanentVault.files = [];
  renderPermanentVault();
  toast(message("vault.permanentLockedToast"));
}

async function uploadPermanentVaultFiles(event) {
  const files = [...event.target.files];
  event.target.value = "";
  if (!files.length) return;
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  try {
    await permanentVaultApi("/api/permanent-vault/files", { method: "POST", body: form });
    toast(message("vault.permanentUploaded")(files.length));
    await loadPermanentVaultFiles();
  } catch (error) {
    toast(localizeServerText(error.message), true);
  }
}

async function downloadPermanentFile(id, name) {
  try {
    const response = await fetch(`/api/permanent-vault/files/${encodeURIComponent(id)}/download`, {
      credentials: "same-origin",
      headers: permanentVaultHeaders(),
    });
    if (!response.ok) throw new Error((await response.json()).detail || message("sendFailed"));
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = name;
    link.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    toast(localizeServerText(error.message), true);
  }
}

async function deletePermanentFile(id, name) {
  if (!window.confirm(message("vault.permanentDeleteConfirm")(name))) return;
  try {
    await permanentVaultApi(`/api/permanent-vault/files/${encodeURIComponent(id)}`, { method: "DELETE" });
    toast(message("vault.permanentDeleted"));
    await loadPermanentVaultFiles();
  } catch (error) {
    toast(localizeServerText(error.message), true);
  }
}

async function backupPermanentVault() {
  const folder = $("#permanent-vault-backup-path").value.trim();
  if (!folder) return toast(message("vault.permanentBackupFolder"), true);
  const form = new FormData();
  form.append("folder", folder);
  try {
    const payload = await permanentVaultApi("/api/permanent-vault/backup", { method: "POST", body: form });
    toast(message("vault.permanentBackedUp")(payload.path));
  } catch (error) {
    toast(localizeServerText(error.message), true);
  }
}

async function restorePermanentVault() {
  const backupPath = $("#permanent-vault-restore-path").value.trim();
  const password = $("#permanent-vault-password")?.value || "";
  if (!backupPath || password.length < 10) return toast(message("passwordLength"), true);
  const form = new FormData();
  form.append("backup_path", backupPath);
  form.append("password", password);
  try {
    const payload = await api("/api/permanent-vault/restore", { method: "POST", body: form });
    state.permanentVault.session = payload.session;
    state.permanentVault.exists = true;
    state.permanentVault.unlocked = true;
    toast(message("vault.permanentRestored"));
    await loadPermanentVaultFiles();
  } catch (error) {
    toast(localizeServerText(error.message), true);
  }
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

function buildInteractivePiiDocument(result) {
  if (!result || !result.spans || !result.spans.length || typeof result.original_text !== "string") return "";

  const originalText = result.original_text || result.redacted_text || "";
  const spans = [...result.spans].sort((a, b) => a.start - b.start);

  let htmlPieces = [];
  let cursor = 0;

  spans.forEach((span) => {
    if (span.start >= cursor) {
      htmlPieces.push(escapeHtml(originalText.substring(cursor, span.start)));
      const label = escapeHtml(span.label || "pii");
      const orig = escapeHtml(span.original || "");
      const place = escapeHtml(span.replacement || span.placeholder || `[${label.toUpperCase()}]`);

      htmlPieces.push(
        `<span class="pii-tag entity-${label.toLowerCase()}" ` +
        `data-original="${orig}" data-placeholder="${place}" ` +
        `data-pii-toggle title="Clicca per invertire (Originale / Anonimizzato)">` +
        `<span class="pii-label">${label}</span> ` +
        `<span class="pii-value">${place}</span>` +
        `</span>`
      );
      cursor = span.end;
    }
  });

  htmlPieces.push(escapeHtml(originalText.substring(cursor)));
  const piiHtml = htmlPieces.join("");

  return `
    <div class="pii-document-container printable-area">
      <div class="pii-toolbar">
        <strong>🛡️ Studio Anonimizzazione PII (Ispirato a Simone Rizzo PII)</strong>
        <div class="pii-toolbar-actions">
          <button type="button" class="pii-btn" id="global-toggle-btn" data-pii-action="toggle-all">
            👁️ Mostra Originale
          </button>
          <button type="button" class="pii-btn" data-pii-action="print">
            🖨️ Stampa Documento
          </button>
          <button type="button" class="pii-btn" data-pii-action="copy">
            📋 Copia Testo Anonimizzato
          </button>
        </div>
      </div>
      <div class="pii-document-body" id="pii-doc-content">${piiHtml}</div>
    </div>
  `;
}

function togglePiiTag(el) {
  const isOriginal = el.classList.contains("showing-original");
  const valEl = el.querySelector(".pii-value");
  if (isOriginal) {
    el.classList.remove("showing-original");
    valEl.textContent = el.dataset.placeholder;
  } else {
    el.classList.add("showing-original");
    valEl.textContent = el.dataset.original;
  }
}

function toggleAllPiiTags() {
  const btn = document.getElementById("global-toggle-btn");
  const tags = document.querySelectorAll(".pii-tag");
  if (!btn) return;
  const showOrig = btn.classList.toggle("active");

  btn.innerHTML = showOrig ? "🛡️ Mostra Anonimizzato" : "👁️ Mostra Originale";

  tags.forEach((tag) => {
    const valEl = tag.querySelector(".pii-value");
    if (showOrig) {
      tag.classList.add("showing-original");
      valEl.textContent = tag.dataset.original;
    } else {
      tag.classList.remove("showing-original");
      valEl.textContent = tag.dataset.placeholder;
    }
  });
}

function printPiiDocument() {
  window.print();
}

function copyRedactedText() {
  const doc = document.getElementById("pii-doc-content");
  if (!doc) return;
  
  let clone = doc.cloneNode(true);
  clone.querySelectorAll(".pii-tag").forEach((tag) => {
    tag.replaceWith(tag.dataset.placeholder);
  });
  
  navigator.clipboard.writeText(clone.textContent).then(() => {
    alert("Testo anonimizzato copiato negli appunti!");
  });
}

window.togglePiiTag = togglePiiTag;
window.toggleAllPiiTags = toggleAllPiiTags;
window.printPiiDocument = printPiiDocument;
window.copyRedactedText = copyRedactedText;

function showJob(jobId) {
  const job = state.jobs.find((item) => item.id === jobId);
  if (!job) return;
  const result = job.result || {};
  const counts = result.counts || {};
  const countHtml = Object.entries(counts).length
    ? `<div class="detail-counts">${Object.entries(counts).map(([key, value]) => `<span>${escapeHtml(key)} · ${value}</span>`).join("")}</div>`
    : "";
  const residualHtml = result.residual_warning
    ? `<div class="process-note warning"><span>!</span><p>${escapeHtml(message("residualWarning"))}</p></div>`
    : "";
  const pdfWarningHtml = result.pdf_redaction_warning
    ? `<div class="process-note warning"><span>!</span><p>${escapeHtml(result.pdf_redaction_warning)}</p></div>`
    : "";
  const dictionaryHtml = result.dictionary_vault_name
    ? `<div class="process-note"><span>✓</span><p>${escapeHtml(message("dictionarySaved")(result.dictionary_vault_name))}</p></div>`
    : "";
  const interactiveDoc = buildInteractivePiiDocument(result);
  const downloads = job.status === "completed" ? `
    <div class="download-actions">
      <a class="primary-button" href="/api/jobs/${job.id}/download">${escapeHtml(message("downloadResult"))}</a>
      ${job.bundle_path ? `<a class="secondary-button" href="/api/jobs/${job.id}/download?kind=bundle">${escapeHtml(message("downloadZip"))}</a>` : ""}
    </div>
  ` : "";
  $("#job-detail").innerHTML = `
    <div class="detail-header">
      <span class="detail-kind">${escapeHtml(localizeServerText(job.engine_name || job.engine))}</span>
      <h3>${escapeHtml(job.title || job.input_name)}</h3>
      <p>${escapeHtml(localizeServerText(job.message || job.stage || ""))}</p>
    </div>
    <div class="detail-stats">
      <div class="detail-stat"><strong>${Math.round(job.progress * 100)}%</strong><small>${escapeHtml(message("progress"))}</small></div>
      <div class="detail-stat"><strong>${humanSize(job.input_size)}</strong><small>${escapeHtml(message("size"))}</small></div>
      <div class="detail-stat"><strong>${result.detections ?? result.pages ?? result.chunks ?? "—"}</strong><small>${escapeHtml(message("items"))}</small></div>
    </div>
    ${job.error ? `<div class="detail-error">${escapeHtml(localizeServerText(job.error))}</div>` : ""}
    ${countHtml}
    ${residualHtml}
    ${pdfWarningHtml}
    ${dictionaryHtml}
    ${interactiveDoc}
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
              <small>${escapeHtml(text(`vault.${volume.kind || "file"}`))} · ${humanSize(volume.size)} · ${humanDate(volume.updated_at)}</small>
            </div>
            <div class="vault-item-actions">
              <a class="secondary-button" href="/api/vault/${encodeURIComponent(volume.name)}/download">${escapeHtml(text("vault.download"))}</a>
              <button type="button" data-decrypt-volume="${escapeHtml(volume.name)}">${escapeHtml(message("decrypt"))}</button>
              <button type="button" class="danger" data-delete-volume="${escapeHtml(volume.name)}">${escapeHtml(text("vault.delete"))}</button>
            </div>
          </div>
        `).join("")
      : `<div class="empty-state">${escapeHtml(message("vaultEmpty"))}</div>`;
  } catch (error) {
    toast(error.message, true);
  }
}

async function deleteVaultVolume(name) {
  if (!window.confirm(message("vaultDeleteConfirm")(name))) return;
  try {
    await api(`/api/vault/${encodeURIComponent(name)}`, { method: "DELETE" });
    toast(message("vaultDeleted"));
    loadVault();
  } catch (error) {
    toast(localizeServerText(error.message), true);
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
  const piiTag = event.target.closest("[data-pii-toggle]");
  if (piiTag) {
    event.preventDefault();
    togglePiiTag(piiTag);
    return;
  }
  const piiAction = event.target.closest("[data-pii-action]");
  if (piiAction) {
    event.preventDefault();
    if (piiAction.dataset.piiAction === "toggle-all") toggleAllPiiTags();
    if (piiAction.dataset.piiAction === "print") printPiiDocument();
    if (piiAction.dataset.piiAction === "copy") copyRedactedText();
    return;
  }
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
  const previewClose = event.target.closest("[data-preview-close]");
  if (previewClose) discardAnonymizationPreview();
  const decrypt = event.target.closest("[data-decrypt-volume]");
  if (decrypt) {
    $("#decrypt-volume-name").textContent = decrypt.dataset.decryptVolume;
    $("#decrypt-volume-value").value = decrypt.dataset.decryptVolume;
    $("#decrypt-dialog").showModal();
  }
  const removeVault = event.target.closest("[data-delete-volume]");
  if (removeVault) deleteVaultVolume(removeVault.dataset.deleteVolume);
  const permanentDownload = event.target.closest("[data-permanent-download]");
  if (permanentDownload) {
    downloadPermanentFile(
      permanentDownload.dataset.permanentDownload,
      permanentDownload.dataset.permanentName,
    );
  }
  const permanentDelete = event.target.closest("[data-permanent-delete]");
  if (permanentDelete) {
    deletePermanentFile(
      permanentDelete.dataset.permanentDelete,
      permanentDelete.dataset.permanentName,
    );
  }
});

$$('input[name="operation"]').forEach((input) => input.addEventListener("change", updateOperation));
$("#studio-form").addEventListener("submit", submitStudio);
$("#encrypt-button").addEventListener("click", () => submitVault("vault_encrypt"));
$("#decrypt-button").addEventListener("click", () => submitVault("vault_decrypt"));
$("#group-button").addEventListener("click", submitVaultGroup);
$("#stored-decrypt-form").addEventListener("submit", decryptStored);
$("#anonymization-preview-dialog").addEventListener("cancel", (event) => {
  event.preventDefault();
  discardAnonymizationPreview();
});
$("#anonymization-preview-dialog").addEventListener("click", (event) => {
  if (event.target === event.currentTarget) discardAnonymizationPreview();
});
$("#refresh-button").addEventListener("click", () => Promise.all([loadJobs(), loadStatus()]));
$("#refresh-vault").addEventListener("click", () => {
  loadVault();
  loadPermanentVault();
});

bindDropZone("#studio-drop", "#studio-files", "studioFiles");
bindDropZone("#vault-drop", "#vault-files", "vaultFiles");
bindDropZone("#vault-group-drop", "#vault-group-files", "vaultGroupFiles");
applyTranslations();
updateOperation();
renderIcons();
loadJobs();
loadStatus();
loadPermanentVault();
setInterval(loadJobs, 2500);
setInterval(loadStatus, 60000);
