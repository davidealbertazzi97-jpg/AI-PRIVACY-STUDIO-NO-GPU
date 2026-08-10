# Audit Rizzo PII e piano di integrazione

Data dell’analisi: 9 agosto 2026

## Riferimento verificato

La copia upstream analizzata è Rizzo PII 2.0.0, pubblicata l’8 agosto 2026, con
modello `rizzo-pii-0.3B` v1.5.0. Il progetto è MIT e mantiene un’architettura
local-first: il modello, la rete regex/checksum e il dizionario reversibile
restano sul computer.

## Novità principali di Rizzo PII 2.0.0

1. **Filtro per tag**: le 23 categorie possono essere abilitate o disabilitate
   singolarmente. Un tag disabilitato continua a essere rilevato ma resta in
   chiaro; la scelta viene salvata nelle preferenze.
2. **Preview del documento**: per i PDF l’app mostra le pagine originali
   renderizzate localmente. Dopo l’analisi aggiunge una vista del PDF redatto,
   oltre alle viste testo e PII evidenziate.
3. **PDF redatto realmente**: il testo PII viene rimosso dal content stream e
   sostituito in posizione; vengono inoltre puliti metadati, XMP, annotazioni,
   campi modulo e segnalibri, mentre gli allegati incorporati vengono rimossi.
4. **Anteprima senza doppia elaborazione**: `/pdf/preview` prepara una volta il
   PDF e lo conserva in una cache LRU in memoria per la visualizzazione e il
   download.
5. **Anonimizzazione reversibile o definitiva**: il dizionario locale può essere
   disattivato; in quel caso non viene costruita né restituita la mappa
   placeholder → valore.
6. **API locale e container offline**: endpoint HTTP per health, analisi,
   preview, PDF e impostazioni; Docker con modello incluso e modalità offline a
   runtime.
7. **Miglioramenti del motore**: modello v1.5.0 con supervisione di tutti i
   subword, metriche entity-level, più dati italiani-legali e due epoche di
   training; rete regex/checksum aggiornata per IBAN, CF omocodici, carte,
   telefoni e targhe nei formati tipici dei documenti.
8. **Correttezza e robustezza**: merge delle span non più quadratico, confini di
   parola più sicuri, preservazione di righe/colonne incollate da Excel, pulizia
   effettiva del dizionario locale e recupero da conflitti di porta.

## Cosa è stato portato in Privacy Studio

Privacy Studio ora usa una revisione in due passaggi per entrambi i motori,
OpenAI Privacy Filter e Rizzo PII:

- prima viene eseguito un job locale di rilevazione;
- la UI mostra testo rilevato e output previsto affiancati;
- ogni span ha una checkbox, con seleziona tutto e deseleziona tutto;
- la barra mostra l’avanzamento reale del job di preview e la fase corrente;
- l’utente può aggiungere parole o frasi non rilevate: le occorrenze trovate
  diventano span manuali indipendenti e possono essere deselezionate;
- il server accetta solo rilevazioni presenti nella preview o span manuali
  validi entro il testo originale, quindi non può introdurre posizioni arbitrarie;
- il file originale resta nell’inbox privata solo fino a conferma o annullamento;
- il job finale riusa quel file e anonimizza soltanto gli elementi confermati;
- la selezione per categoria viene salvata localmente e può essere invertita
  con un clic;
- ogni occorrenza ha una sostituzione personalizzata e si può applicare una
  sostituzione uniforme all’intero documento;
- le rilevazioni vengono conservate in una cache temporanea con permessi
  restrittivi, verificata tramite SHA-256 e cancellata dopo conferma o annullamento;
- per i PDF sono disponibili anteprima originale/redatta; con il profilo PDF
  editabile opzionale il PII viene rimosso mantenendo ricercabile e modificabile
  il testo restante, mentre l’installer predefinito usa il fallback rasterizzato
  quando tutte le rilevazioni sono localizzabili. Se una rilevazione OCR non può
  essere mappata sulla pagina, il PDF viene trattenuto invece di consegnare una
  copia potenzialmente incompleta. PyMuPDF non viene incluso senza una scelta
  esplicita sui vincoli AGPL/commerciali;
- il dizionario reversibile è opzionale e viene cifrato in un volume Picocrypt
  separato; il vault locale supporta anche gruppi di documenti in un unico
  archivio, con download ed eliminazione dei volumi.
- è stato aggiunto un vault permanente incrementale separato dai volumi
  Picocrypt: indice cifrato, documenti cifrati singolarmente, sblocco temporaneo,
  ricerca, download, eliminazione e backup/ripristino da cartella sincronizzata;
  il cloud diretto resta escluso per non indebolire il guard di rete.

La modifica non copia il codice di Rizzo PII: integra gli stessi principi di
revisione nel modello di coda e nei due motori già presenti in Privacy Studio.
Il server API autonomo e il container Docker di Rizzo non sono stati aggiunti,
come richiesto, perché Privacy Studio è già un’applicazione locale monolitica.

## Valutazione delle funzioni da adottare

Sono state implementate le funzioni utili all’uso desktop: filtro per categoria,
preview PDF, selezione manuale, sostituzioni personalizzate, cache della
preview, dizionario opzionale cifrato, checksum italiani, avvisi sui residui,
PDF redatto sicuro e vault locale di gruppo.

Restano intenzionalmente fuori il server API autonomo e il container Docker.
La differenza tecnica rispetto al PDF di Rizzo dipende dal profilo installato:
con `requirements-pdf-editable.txt` Privacy Studio mantiene ricercabile e
modificabile il testo non-PPI usando PyMuPDF; nel profilo predefinito usa invece
un PDF rasterizzato tramite PDFium/Pillow, più sicuro contro il recupero del
testo originale ma privo di testo ricercabile. Se il PDF è una scansione e le
coordinate OCR non sono disponibili, il risultato PDF viene omesso. PyMuPDF non
viene incluso di default per la sua licenza AGPL/commerciale.

La priorità successiva consigliata è aggiungere test con PDF testuali e immagini
scansionate reali del proprio archivio, poi valutare se il compromesso
rasterizzato è sufficiente per la stampa e la conservazione documentale.

## Fonti

- Repository: https://github.com/Rizzo-AI-Academy/rizzo-pii
- Release 2.0.0: https://github.com/Rizzo-AI-Academy/rizzo-pii/releases/tag/v2.0.0
