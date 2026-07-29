<p align="center">
  <img src="static/icon.svg" width="88" height="88" alt="Privacy Studio">
</p>

<h1 align="center">Privacy Studio Locale</h1>

<p align="center">
  Documenti, OCR, trascrizione, anonimizzazione assistita e cifratura.<br>
  Tutto sul tuo computer.
</p>

<p align="center">
  <strong>Italiano</strong> · <a href="README.en.md">English</a>
</p>

## Cosa fa

Privacy Studio Locale è un'applicazione open source per elaborare documenti
sensibili senza affidare il contenuto a servizi cloud:

- anonimizzazione assistita con OpenAI Privacy Filter e regole italiane;
- trascrizione audio/video con NVIDIA Parakeet TDT 0.6B v3;
- OCR con PaddleOCR, PP-StructureV3 o GLM-OCR tramite Ollama;
- conversione di PDF e documenti Office con Microsoft MarkItDown;
- cifratura e decifratura di volumi Picocrypt `.pcv`;
- coda persistente e interfaccia responsive con asset serviti localmente.

Il progetto è indipendente e non è affiliato ai produttori dei motori
integrati.

## Installazione automatica

Il profilo completo è predisposto per:

| Sistema | Architettura |
| --- | --- |
| Linux | x86-64 |
| macOS | Apple Silicon (arm64) |
| Windows 10/11 | x86-64 |

Su Linux o macOS:

```bash
cd PrivacyStudio
chmod +x install.sh start.sh
./install.sh
```

Su Windows, da PowerShell:

```powershell
cd PrivacyStudio
.\install.ps1
```

Da Prompt dei comandi si può usare `install.cmd`; il wrapper applica
l'eccezione alla policy PowerShell soltanto al proprio processo, senza
modificare le impostazioni del sistema.

Non occorre installare manualmente Python, `uv`, FFmpeg, Picocrypt, Ollama o i
modelli. L'installer scarica `uv` e ne verifica il checksum, installa Python
3.12 in modo gestito, crea tre ambienti isolati e prepara tutti i motori. I
download diretti di Picocrypt e Ollama sono versionati e verificati con
SHA-256. Parakeet e Privacy Filter sono fissati a commit precisi; il manifest
GLM-OCR viene verificato tramite digest, mentre PaddleOCR deriva dalla release
Python bloccata e viene validato con un'inferenza sintetica.

L'installazione completa richiede la rete, tempo e diversi gigabyte di spazio.
Per evitare il runtime Ollama e GLM-OCR, che da soli aggiungono circa 3 GB:

```bash
./install.sh --without-glm
```

In PowerShell si usa lo stesso flag con `.\install.ps1`. Per installare soltanto
il nucleo leggero: `--core-only --skip-desktop`.

Il profilo completo e gli smoke test dei motori sono stati verificati su Linux
x86-64. Il nucleo viene verificato dalla CI anche su macOS e Windows; le
combinazioni indicate seguono le wheel ufficiali di PyTorch, PaddlePaddle e
degli altri componenti. NVIDIA indica Linux come sistema preferito per
Parakeet, quindi la trascrizione sui due sistemi non-Linux va considerata
supporto best effort finché non sarà coperta da test hardware completi.

## Avvio

Su Linux/macOS:

```bash
./start.sh
```

Su Windows:

```powershell
.\start.ps1
```

Da Prompt dei comandi è disponibile anche `start.cmd`.

Il launcher genera una chiave privata, avvia gli eventuali servizi locali,
attende il controllo di salute e apre il browser. `Ctrl+C` arresta i processi
avviati dalla sessione. Su Linux l'installer può inoltre creare la voce
**Privacy Studio Locale** nel menu applicazioni.

## Privacy e limiti di sicurezza

Il server ascolta soltanto su `127.0.0.1` e ogni API richiede un token casuale.
I processi Python ricevono un guard multipiattaforma che rifiuta connessioni
non loopback; su Linux viene aggiunto, quando compilabile, un secondo guard
nativo. Il launcher avvia un'istanza Ollama privata su una porta loopback
dedicata, con le funzioni cloud disattivate, e non riutilizza eventuali server
Ollama di sistema. Non ci sono telemetria, CDN o inferenza remota.

La rete è consentita durante l'installazione per ottenere software e modelli.
Al runtime i motori usano file e cache locali. Il browser predefinito rimane un
programma esterno e può effettuare il proprio traffico di background; il server
non gli espone contenuti su interfacce di rete esterne.

Gli originali non vengono sovrascritti. Le copie di lavoro vengono eliminate
al termine del job e le passphrase Picocrypt rimangono soltanto in RAM durante
l'operazione.

> [!WARNING]
> L'anonimizzazione automatica riduce il rischio, ma non garantisce che ogni
> dato personale venga riconosciuto né costituisce una verifica di conformità
> legale. Controlla sempre il risultato prima di condividerlo.

## Dati locali

| Sistema | Dati e cassaforte | Token e log | Risultati |
| --- | --- | --- | --- |
| Linux | `~/.local/share/privacy-studio` | `~/.config/privacy-studio` | `~/Documents/Privacy Studio - Results` |
| macOS | `~/Library/Application Support/Privacy Studio` | stessa cartella | `~/Documents/Privacy Studio - Results` |
| Windows | `%LOCALAPPDATA%\Privacy Studio` | stessa cartella | `%USERPROFILE%\Documents\Privacy Studio - Results` |

Su un sistema Linux italiano che possiede `~/Documenti` ma non `~/Documents`,
il launcher usa automaticamente la cartella localizzata. Gli artefatti
scaricati (`.venv*`, `bin`, `models`) sono esclusi da Git.

## Installazione tramite agente IA

Chi usa un agente di coding può copiare il prompt già pronto:

- [prompt in italiano](docs/CODING_AGENT_PROMPT.it.md);
- [English prompt](docs/CODING_AGENT_PROMPT.en.md).

Il prompt ordina all'agente di rilevare sistema e architettura, usare
l'installer ufficiale, non richiedere privilegi amministrativi, eseguire i
test locali e non caricare documenti o segreti.

## Sviluppo e test

```bash
./scripts/check.sh
.venv/bin/python tests/smoke_local.py --core-only
.venv/bin/python tests/smoke_local.py --skip-heavy
.venv/bin/python tests/smoke_local.py --skip-glm
```

I test usano soltanto documenti sintetici in directory temporanee. Il primo
comando esegue controlli statici; gli altri provano rispettivamente nucleo,
motori leggeri e profilo completo escluso GLM-OCR.

## Struttura

```text
app/             API, coda e orchestrazione
workers/         processi isolati per AI e PaddleOCR
static/          interfaccia e asset locali
runtime_guard/   blocco di rete Python multipiattaforma
native/          guard di rete aggiuntivo per Linux
scripts/         bootstrap, avvio e controlli
packaging/       integrazione desktop Linux
tests/           smoke test con fixture sintetiche
```

## Licenza

Il codice originale è distribuito sotto
[Apache License 2.0](LICENSE). È una licenza open source permissiva che
consente uso, modifica e ridistribuzione, include una concessione esplicita di
brevetti e contiene esclusioni di garanzia e limitazioni di responsabilità.
Richiede di conservare licenza e avvisi e di segnalare i file modificati.

È stata preferita alla 0BSD per la tutela brevettuale esplicita, pur restando
molto permissiva. Le dipendenze mantengono le loro licenze: Picocrypt CLI è un
programma separato GPL-3.0-only scaricato dall'utente tramite installer; anche
il binario FFmpeg fornito dalla wheel ispezionata è un processo separato GPL;
Parakeet è CC-BY-4.0; Inter è OFL-1.1 e Lucide è ISC. Consulta
[gli avvisi di terze parti](THIRD_PARTY_NOTICES.md).

Questa è una valutazione tecnica prudenziale, non un parere legale. Il
repository sorgente non include ambienti Python, modelli o binari scaricati.
Chi distribuisce un pacchetto binario già assemblato deve rigenerare
l'inventario e rispettare anche gli obblighi dei singoli artefatti inclusi.

## Avvertenze

Questo è un progetto personale e sperimentale, realizzato anche tramite
"vibe coding" assistito dall'intelligenza artificiale e reso disponibile
gratuitamente. È fornito "così com'è", senza garanzie; l'uso è a rischio
dell'utente e l'autore e i contributori non si assumono responsabilità nei
limiti massimi consentiti dalla legge.

Anonimizzazione, OCR e trascrizione possono sbagliare: ogni risultato va
controllato manualmente prima di essere usato o condiviso. Leggi le
[avvertenze complete in italiano](DISCLAIMER.md) o
[in inglese](DISCLAIMER.en.md).

## Contribuire e sicurezza

Prima di contribuire leggi [CONTRIBUTING.md](CONTRIBUTING.md). Per le
vulnerabilità segui [SECURITY.md](SECURITY.md) senza aprire issue pubbliche.
