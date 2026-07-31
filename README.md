<p align="center">
  <img src="static/icon.svg" width="88" height="88" alt="AI Privacy Studio">
</p>

<h1 align="center">AI Privacy Studio (No GPU)</h1>

<p align="center">
  <strong>Local document processing for teachers and professionals.</strong><br>
  Confidential documents stay on the computer. No GPU or cloud inference is
  required.
</p>

<p align="center">
  <a href="#english">English</a> · <a href="#italiano">Italiano</a>
</p>

---

<a id="english"></a>

## English

AI Privacy Studio was created in a personal homelab to solve a practical
problem: process confidential documents on ordinary, low- to mid-range
consumer hardware without sending their contents to external servers.

It is intended for teachers, independent professionals, small offices, and
anyone who needs local OCR, transcription, redaction, conversion, or encrypted
storage on a CPU-only computer.

### Download

Use the files attached to the
[latest GitHub release](https://github.com/davidealbertazzi97-jpg/AI-PRIVACY-STUDIO-NO-GPU/releases/latest).

| Platform | Download | Supported architecture |
| --- | --- | --- |
| Windows 10/11 | `AI-Privacy-Studio-Setup-1.0.0-windows-x86_64.exe` | x86-64 |
| Linux | `AI-Privacy-Studio-1.0.0-linux-x86_64.AppImage` | x86-64 |
| macOS 13+ | `AI-Privacy-Studio-1.0.0-macos-arm64.dmg` | Apple Silicon |

These are online installers. They contain the audited project source, not the
large models or downloaded runtimes. The first installation requires internet
access, several gigabytes of disk space, and time. The default full profile
installs GLM-OCR as well as the other engines.

The packages are currently unsigned. Windows SmartScreen and macOS Gatekeeper
may display a warning. Compare the file against `SHA256SUMS.txt` in the same
release before running it.

#### Windows

Run the `.exe` as the normal user. Administrative privileges are not required.
Leave the final installation option selected to download Python, the local
engines, and the models. The Start menu and optional desktop shortcut launch
the app afterward.

#### Linux

```bash
chmod +x AI-Privacy-Studio-1.0.0-linux-x86_64.AppImage
./AI-Privacy-Studio-1.0.0-linux-x86_64.AppImage
```

The first run opens a terminal for the verified installation. Later runs start
the app directly.

#### macOS

Open the `.dmg`, copy **AI Privacy Studio** to Applications, then open the app.
Because the package is not notarized, macOS may require an explicit approval
through Finder or Privacy & Security settings.

### Install from source

```bash
git clone https://github.com/davidealbertazzi97-jpg/AI-PRIVACY-STUDIO-NO-GPU.git
cd AI-PRIVACY-STUDIO-NO-GPU
./install.sh
./start.sh
```

On Windows, run `.\install.ps1` and then `.\start.ps1` in PowerShell.

The full installer prepares:

- managed Python 3.12 and isolated environments;
- Microsoft MarkItDown;
- OpenAI Privacy Filter and Rizzo PII 0.3B (Simone Rizzo);
- NVIDIA Parakeet TDT 0.6B v3;
- PaddleOCR and PP-StructureV3;
- Ollama and GLM-OCR Q8;
- FFmpeg and Picocrypt CLI.

Use `--without-glm` only when disk space matters more than the GLM-OCR option.
Use `--core-only --skip-desktop` for the lightweight conversion-only profile.

### Functions

- Italian or English interface with a saved local preference.
- PII redaction with a choice between OpenAI Privacy Filter (multilingual) or Rizzo PII 0.3B by Simone Rizzo (specialized Italian PII: Tax Code, VAT ID, Land Registry, Document ID, etc.), plus deterministic Italian patterns.
- Interactive PII Anonymization Viewer inspired by [Rizzo PII](https://github.com/Rizzo-AI-Academy/rizzo-pii) (Simone Rizzo / Rizzo AI Academy): color-coded entity badges (`PERSON`, `ADDRESS`, `EMAIL`, `PHONE`, `VAT_ID`, `TAX_CODE`, `IBAN`), click-to-reveal original text ("see what was there before"), and formatted print/copy views.
- Audio and video transcription with NVIDIA Parakeet.
- OCR for images and multi-page PDF files with PaddleOCR, PP-StructureV3, or
  GLM-OCR.
- Office, PDF, HTML, EPUB, and structured-data conversion with MarkItDown.
- Picocrypt-compatible `.pcv` encryption and decryption.
- Persistent local job queue and downloadable result bundles.

### Privacy and security model

- The service binds to `127.0.0.1` only.
- Every API request requires a random per-installation token.
- Runtime Python processes reject non-loopback network connections.
- Linux adds a native outbound-network guard when available.
- Ollama runs as a dedicated loopback-only process with cloud features
  disabled.
- The interface contains no telemetry, CDN asset, or remote inference call.
- Original files are not overwritten.
- Working plaintext and uploaded copies are removed after each job, including
  error paths covered by the test suite.
- Picocrypt passphrases remain in memory only while an operation is running.
- Public redaction reports contain labels and positions, not fragments of the
  detected private values.

Network access is required during installation to download verified software
and pinned models. The default browser is outside the application's network
guard and may perform its own background traffic.

Automated redaction, OCR, and transcription can be wrong. Review every output
before sharing it. Local processing does not by itself establish GDPR or other
regulatory compliance.

### Local data

| Platform | Application data and vault | Results |
| --- | --- | --- |
| Linux | `~/.local/share/privacy-studio` | `~/Documents/Privacy Studio - Results` |
| macOS | `~/Library/Application Support/Privacy Studio` | `~/Documents/Privacy Studio - Results` |
| Windows | `%LOCALAPPDATA%\Privacy Studio` | `%USERPROFILE%\Documents\Privacy Studio - Results` |

The AppImage launcher source is copied to
`$XDG_DATA_HOME/ai-privacy-studio/app`. The macOS app uses
`~/Library/Application Support/AI Privacy Studio/app`. Model caches and results
remain outside Git.

### Repository control files

`.gitignore` is intentionally included: it prevents environments, models,
tokens, databases, logs, encrypted volumes, and results from being committed.
`.github/` contains only CI, dependency-update, and installer-build workflows.
The `.git` directory itself is never tracked or included in GitHub source
archives or release installers.

### License

Original project code and documentation are licensed under
[GNU GPL version 3 only](LICENSE) (`GPL-3.0-only`). Distributed modified
versions must remain under GPLv3 and provide their corresponding source.
Third-party assets, libraries, models, and separate programs keep their own
licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and
[LICENSE-GUIDE.md](LICENSE-GUIDE.md).

This licensing summary is technical information, not legal advice. It assumes
the project owner holds the copyright in the original project code.

### Development and verification

```bash
./scripts/check.sh
.venv/bin/python tests/smoke_local.py --core-only
.venv/bin/python tests/smoke_local.py --skip-heavy
.venv/bin/python tests/smoke_local.py --skip-glm
```

Tests use synthetic fixtures only. Security reports should follow
[SECURITY.md](SECURITY.md), not a public issue.

---

<a id="italiano"></a>

## Italiano

AI Privacy Studio è nato nel mio homelab da una necessità concreta: elaborare
documenti riservati su hardware consumer di fascia medio-bassa senza inviarne
il contenuto a server esterni.

È pensato per insegnanti, liberi professionisti, piccoli uffici e per chiunque
abbia bisogno di OCR, trascrizione, anonimizzazione, conversione o archiviazione
cifrata in locale su un computer privo di GPU.

### Download

Usa i file allegati alla
[release GitHub più recente](https://github.com/davidealbertazzi97-jpg/AI-PRIVACY-STUDIO-NO-GPU/releases/latest).

| Sistema | Download | Architettura supportata |
| --- | --- | --- |
| Windows 10/11 | `AI-Privacy-Studio-Setup-1.0.0-windows-x86_64.exe` | x86-64 |
| Linux | `AI-Privacy-Studio-1.0.0-linux-x86_64.AppImage` | x86-64 |
| macOS 13+ | `AI-Privacy-Studio-1.0.0-macos-arm64.dmg` | Apple Silicon |

Sono installer online. Contengono il sorgente verificato del progetto, non i
modelli e i runtime di grandi dimensioni. La prima installazione richiede la
rete, diversi gigabyte di spazio e tempo. Il profilo completo predefinito
installa anche GLM-OCR.

I pacchetti al momento non sono firmati. Windows SmartScreen e macOS Gatekeeper
possono mostrare un avviso. Prima di eseguirli confronta il file con
`SHA256SUMS.txt` pubblicato nella stessa release.

#### Windows

Esegui il file `.exe` come utente normale. Non servono privilegi amministrativi.
Lascia selezionata l'opzione finale per scaricare Python, i motori locali e i
modelli. In seguito l'app si avvia dal menu Start o dal collegamento facoltativo
sul desktop.

#### Linux

```bash
chmod +x AI-Privacy-Studio-1.0.0-linux-x86_64.AppImage
./AI-Privacy-Studio-1.0.0-linux-x86_64.AppImage
```

Al primo avvio viene aperto un terminale per l'installazione verificata. Gli
avvii successivi aprono direttamente l'app.

#### macOS

Apri il file `.dmg`, copia **AI Privacy Studio** in Applicazioni e avvia l'app.
Poiché il pacchetto non è notarizzato, macOS può richiedere un'approvazione
esplicita dal Finder o dalle impostazioni Privacy e sicurezza.

### Installazione dal sorgente

```bash
git clone https://github.com/davidealbertazzi97-jpg/AI-PRIVACY-STUDIO-NO-GPU.git
cd AI-PRIVACY-STUDIO-NO-GPU
./install.sh
./start.sh
```

Su Windows esegui `.\install.ps1` e poi `.\start.ps1` in PowerShell.

L'installazione completa prepara:

- Python 3.12 gestito e ambienti isolati;
- Microsoft MarkItDown;
- OpenAI Privacy Filter e Rizzo PII 0.3B (Simone Rizzo);
- NVIDIA Parakeet TDT 0.6B v3;
- PaddleOCR e PP-StructureV3;
- Ollama e GLM-OCR Q8;
- FFmpeg e Picocrypt CLI.

Usa `--without-glm` soltanto se vuoi ridurre l'uso del disco rinunciando a
GLM-OCR. Usa `--core-only --skip-desktop` per il profilo leggero dedicato alla
conversione.

### Funzioni

- Interfaccia in italiano o inglese con preferenza salvata in locale.
- Anonimizzazione PII a scelta tra OpenAI Privacy Filter (Tutte le lingue) e Rizzo PII 0.3B di Simone Rizzo (Solo italiano: Codice Fiscale, P.IVA, Dati Catastali, Documento ID, ecc.), oltre a regole italiane deterministiche.
- Visualizzatore Interattivo Anonimizzazione PII ispirato a [Rizzo PII](https://github.com/Rizzo-AI-Academy/rizzo-pii) (Simone Rizzo / Rizzo AI Academy): tag cromatici per categoria di entità (`PERSONA`, `INDIRIZZO`, `EMAIL`, `TELEFONO`, `P.IVA`, `CODICE_FISCALE`, `IBAN`), toggle interattivo per mostrare/nascondere i valori originali ("vedere cosa c'era prima") e la visualizzazione di stampa formattata per la conservazione o il salvataggio in PDF.
- Trascrizione audio e video con NVIDIA Parakeet.
- OCR di immagini e PDF multipagina con PaddleOCR, PP-StructureV3 o GLM-OCR.
- Conversione di Office, PDF, HTML, EPUB e dati strutturati con MarkItDown.
- Cifratura e decifratura compatibile con volumi Picocrypt `.pcv`.
- Coda locale persistente e pacchetti di risultati scaricabili.

### Modello di privacy e sicurezza

- Il servizio ascolta soltanto su `127.0.0.1`.
- Ogni richiesta API richiede un token casuale dell'installazione.
- I processi Python rifiutano connessioni di rete non loopback.
- Su Linux viene aggiunto un guard nativo quando disponibile.
- Ollama usa un processo dedicato, solo loopback, con funzioni cloud disattivate.
- L'interfaccia non contiene telemetria, CDN o chiamate di inferenza remota.
- Gli originali non vengono sovrascritti.
- Le copie di lavoro in chiaro e gli upload vengono eliminati al termine del
  job, anche nei percorsi di errore coperti dai test.
- Le passphrase Picocrypt restano in memoria soltanto durante l'operazione.
- I rapporti di anonimizzazione pubblici contengono etichette e posizioni, non
  frammenti dei valori privati rilevati.

La rete serve durante l'installazione per scaricare software verificato e
modelli bloccati a versioni precise. Il browser predefinito è esterno al guard
dell'applicazione e può generare traffico proprio in background.

Anonimizzazione, OCR e trascrizione automatici possono sbagliare. Controlla ogni
risultato prima di condividerlo. L'elaborazione locale non dimostra da sola la
conformità al GDPR o ad altre norme.

### Dati locali

| Sistema | Dati applicativi e cassaforte | Risultati |
| --- | --- | --- |
| Linux | `~/.local/share/privacy-studio` | `~/Documents/Privacy Studio - Results` |
| macOS | `~/Library/Application Support/Privacy Studio` | `~/Documents/Privacy Studio - Results` |
| Windows | `%LOCALAPPDATA%\Privacy Studio` | `%USERPROFILE%\Documents\Privacy Studio - Results` |

Il launcher AppImage copia il sorgente in
`$XDG_DATA_HOME/ai-privacy-studio/app`. L'app macOS usa
`~/Library/Application Support/AI Privacy Studio/app`. Cache dei modelli e
risultati restano fuori da Git.

### File di controllo del repository

`.gitignore` è incluso intenzionalmente: impedisce di aggiungere a Git ambienti,
modelli, token, database, log, volumi cifrati e risultati. `.github/` contiene
soltanto workflow di CI, aggiornamento dipendenze e costruzione degli installer.
La directory `.git` non è tracciata e non viene inserita negli archivi sorgente
di GitHub né negli installer della release.

### Licenza

Il codice e la documentazione originali sono distribuiti sotto
[GNU GPL versione 3 soltanto](LICENSE) (`GPL-3.0-only`). Le versioni modificate
distribuite devono restare sotto GPLv3 e rendere disponibile il sorgente
corrispondente. Asset, librerie, modelli e programmi separati di terze parti
mantengono le loro licenze; consulta
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) e
[LICENSE-GUIDE.md](LICENSE-GUIDE.md).

Questo riepilogo è un'analisi tecnica, non un parere legale. Presuppone che il
titolare del progetto possieda i diritti sul codice originale.

### Sviluppo e verifica

```bash
./scripts/check.sh
.venv/bin/python tests/smoke_local.py --core-only
.venv/bin/python tests/smoke_local.py --skip-heavy
.venv/bin/python tests/smoke_local.py --skip-glm
```

I test usano soltanto fixture sintetiche. Per segnalazioni di sicurezza segui
[SECURITY.md](SECURITY.md), senza aprire una issue pubblica.
