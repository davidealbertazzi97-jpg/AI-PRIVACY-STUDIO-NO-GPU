# Prompt per agente di coding — Italiano

[English](CODING_AGENT_PROMPT.en.md) · **Italiano**

Sostituisci `<REPOSITORY_URL>` con l'URL pubblico del repository, poi copia
soltanto il blocco seguente nel tuo agente di coding.

```text
Devi installare e rendere operativo Privacy Studio Locale partendo da:
<REPOSITORY_URL>

Obiettivo: al termine l'app deve essere installata, verificata e pronta
all'avvio sul computer locale, usando esclusivamente gli installer presenti
nel repository.

Regole obbligatorie:
1. Lavora soltanto nella cartella scelta per Privacy Studio. Non modificare o
   cancellare file estranei e non usare comandi distruttivi.
2. Non usare sudo, privilegi amministrativi o gestori di pacchetti di sistema.
   Se il sistema richiede un'azione amministrativa, fermati e spiegala.
3. Non leggere, copiare, caricare o usare documenti personali, token,
   passphrase o altre credenziali. I test devono usare solo le fixture
   sintetiche incluse nel progetto.
4. La rete è autorizzata esclusivamente per clonare/scaricare il repository e
   per i download effettuati dall'installer. Non aggiungere servizi cloud,
   telemetria, CDN o inferenza remota.
5. Non disattivare il binding a 127.0.0.1, il token locale, il runtime_guard,
   i checksum o i pin di versione. Non aprire porte sul firewall.
6. Non fare commit, push o modifiche al repository, salvo una correzione
   strettamente necessaria per completare l'installazione; in tal caso mostrami
   prima il problema e la modifica proposta.

Procedura:
1. Rileva sistema operativo e architettura senza cambiare lo stato del
   computer. Il profilo completo supportato è Linux x86-64, macOS Apple
   Silicon arm64 o Windows x86-64. Se la combinazione è diversa, non forzare
   l'installazione: riferisci l'incompatibilità.
2. Se non sei già dentro una copia valida del progetto, clona
   <REPOSITORY_URL> in una nuova cartella PrivacyStudio. Se Git non è
   disponibile ma puoi scaricare l'archivio sorgente dalla stessa origine,
   scaricalo ed estrailo in una nuova cartella.
3. Leggi README.md, THIRD_PARTY_NOTICES.md e SECURITY.md. Controlla che
   install.sh/install.ps1, scripts/bootstrap.py e i file requirements siano
   presenti.
4. Mostra spazio libero e piano di installazione eseguendo:
   - Linux/macOS: python3 scripts/bootstrap.py --dry-run, se python3 è già
     disponibile; altrimenti prosegui con install.sh, che installa Python.
   - Windows: py scripts\bootstrap.py --dry-run, se il launcher py è già
     disponibile; altrimenti prosegui con install.ps1.
   Il profilo completo usa diversi gigabyte. Se lo spazio è chiaramente
   insufficiente, fermati senza fare installazioni parziali.
5. Esegui l'installer ufficiale completo:
   - Linux/macOS: chmod +x install.sh start.sh && ./install.sh
   - Windows PowerShell: .\install.ps1
   Non sostituire questi comandi con installazioni manuali. L'installer deve
   predisporre uv, Python 3.12, ambienti isolati, FFmpeg, Picocrypt, OpenAI
   Privacy Filter, Parakeet, PaddleOCR, Ollama e GLM-OCR. Se l'utente ha
   esplicitamente chiesto di risparmiare spazio, usa --without-glm.
6. Se un download o checksum fallisce, non aggirare la verifica e non usare un
   mirror casuale. Riporta URL, componente e messaggio d'errore, senza
   pubblicare token o percorsi sensibili.
7. Al termine esegui i controlli disponibili:
   - importa il nucleo con il Python dell'ambiente .venv;
   - esegui tests/smoke_local.py --core-only;
   - se l'installazione completa è riuscita, esegui
     tests/smoke_local.py --skip-glm;
   - su Linux esegui anche scripts/check.sh se gli strumenti di sviluppo sono
     presenti.
8. Avvia l'app senza aprire il browser per il solo tempo necessario a
   verificare /health su 127.0.0.1, poi arresta il processo in modo pulito.
   Usa scripts/start.py --no-browser con il Python di .venv. Non stampare il
   token locale nei log o nel resoconto.
9. Consegna un resoconto finale con: sistema rilevato, componenti installati,
   test superati/falliti, comando esatto di avvio (./start.sh oppure
   .\start.ps1), percorso dei risultati e ogni limitazione. Non dichiarare
   riuscito ciò che non hai verificato.

Procedi autonomamente finché resti entro queste regole. Chiedi conferma solo
se servono privilegi, una scelta che cambia il profilo richiesto o
un'operazione potenzialmente distruttiva.
```
