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

## Cos'è

Privacy Studio Locale è un'applicazione desktop open source per elaborare
documenti sensibili senza inviarli a servizi cloud. Offre un'interfaccia web
locale, una coda persistente e motori specializzati eseguiti sul dispositivo.

- anonimizzazione assistita con OpenAI Privacy Filter e regole italiane;
- trascrizione audio e video con NVIDIA Parakeet TDT 0.6B v3;
- OCR con PaddleOCR, PP-StructureV3 o GLM-OCR tramite Ollama;
- conversione di PDF e documenti Office con Microsoft MarkItDown;
- cifratura e decifratura di volumi Picocrypt `.pcv`;
- interfaccia responsive con font e icone open source serviti localmente.

Il progetto è indipendente e non è affiliato, sponsorizzato o approvato dai
produttori dei motori integrati.

## Privacy e sicurezza

Il server ascolta esclusivamente su `127.0.0.1` e richiede un token casuale
generato durante l'installazione. Gli originali non vengono sovrascritti; le
copie temporanee vengono eliminate al termine di ogni lavoro.

Il servizio e il browser dedicato caricano un piccolo guard nativo che nega le
connessioni IPv4 e IPv6 non loopback. Chromium viene inoltre avviato con un
profilo separato, proxy chiuso e risoluzione dei nomi esterni disabilitata.

La rete è necessaria durante l'installazione per scaricare pacchetti e modelli.
Dopo l'installazione i motori lavorano con file locali e cache locali. Il guard
è una misura di difesa in profondità, non sostituisce un firewall o una sandbox
del sistema operativo.

> [!WARNING]
> OpenAI Privacy Filter riduce il rischio di divulgare dati personali, ma non
> garantisce anonimizzazione completa o conformità legale. Revisiona sempre i
> risultati prima di condividerli.

## Requisiti

La procedura automatica è attualmente supportata e testata su:

- Linux x86_64 con sessione systemd utente;
- Python 3.10 o successivo, consigliato Python 3.12;
- [`uv`](https://docs.astral.sh/uv/), compilatore C, `curl` e `sha256sum`;
- FFmpeg e ffprobe;
- [Ollama](https://ollama.com/) per GLM-OCR;
- Chromium, Chromium Browser o Google Chrome.

I modelli richiedono diversi gigabyte di spazio. L'esecuzione è configurata per
CPU; GLM-OCR è accurato ma può essere molto lento senza accelerazione hardware.

## Installazione

Clona o scarica il repository, quindi:

```bash
cd PrivacyStudio
./scripts/install.sh
```

Lo script:

1. controlla i prerequisiti senza installare pacchetti di sistema;
2. crea tre ambienti Python isolati;
3. scarica e verifica Picocrypt CLI e la relativa licenza GPL;
4. compila il guard di rete dal sorgente C;
5. scarica e prepara tutti i modelli;
6. installa launcher e servizio systemd per il solo utente corrente.

Ogni script in `scripts/install-*.sh` è rilanciabile singolarmente. I download
di Picocrypt sono bloccati da checksum SHA-256; OpenAI Privacy Filter è fissato
a uno specifico commit Git.

## Avvio

Apri **Privacy Studio Locale** dal menu applicazioni. In alternativa:

```bash
./scripts/open.sh
```

Il servizio non viene esposto sulla rete locale e non è abilitato
automaticamente all'avvio del computer. Il launcher lo avvia quando serve.

## Dati locali

| Contenuto | Percorso predefinito |
| --- | --- |
| Coda, database e temporanei | `~/.local/share/privacy-studio` |
| Cassaforte Picocrypt | `~/.local/share/privacy-studio/vault` |
| Risultati | `~/Documenti/Privacy Studio - Risultati` |
| Token e porta | `~/.config/privacy-studio/environment` |
| Profilo Chromium isolato | `~/.local/state/privacy-studio/chrome-profile` |

Le directory contenenti dati hanno permessi `0700`; token, database e volumi
sono protetti con permessi privati. Le passphrase Picocrypt restano soltanto in
memoria durante il lavoro e non vengono salvate.

## Sviluppo e test

Controlli statici:

```bash
./scripts/check.sh
```

Smoke test leggero e isolato:

```bash
.venv/bin/python tests/smoke_local.py --core-only
```

Test locale di conversione, Privacy Filter e Picocrypt:

```bash
.venv/bin/python tests/smoke_local.py --skip-heavy
```

Test completo escluso il lento GLM-OCR:

```bash
.venv/bin/python tests/smoke_local.py --skip-glm
```

Tutti i test creano esclusivamente documenti sintetici in directory temporanee.
Le pull request eseguono Ruff, compilazione Python, validazione shell e
JavaScript, Bandit e lo smoke test del nucleo.

## Struttura

```text
app/         API, coda persistente e orchestrazione
workers/     processi isolati per AI e PaddleOCR
static/      interfaccia locale e asset vendorizzati
native/      sorgente del guard di rete
scripts/     installazione, avvio e controlli
packaging/   template desktop e systemd portabili
tests/       smoke test con fixture sintetiche
```

## Licenze

Il codice originale di Privacy Studio Locale è distribuito sotto
[licenza BSD Zero Clause (0BSD)](LICENSE), una licenza open source
estremamente permissiva che non impone condizioni sul riuso del codice
originale.

Le dipendenze conservano le proprie licenze. In particolare, Picocrypt CLI è un
programma separato GPL-3.0-only richiamato dalla riga di comando; il suo binario
non è incluso nel repository. Inter è OFL-1.1, Lucide è ISC e il modello
NVIDIA Parakeet è CC-BY-4.0. Consulta
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) per l'inventario completo e
le attribuzioni.

Questa valutazione di compatibilità è tecnica e prudenziale, non un parere
legale. Per una distribuzione commerciale in forma binaria è opportuno far
verificare il pacchetto finale da un professionista.

## Contribuire e sicurezza

Leggi [`CONTRIBUTING.md`](CONTRIBUTING.md) prima di inviare modifiche. Le
vulnerabilità non devono essere pubblicate in una issue: segui
[`SECURITY.md`](SECURITY.md).
