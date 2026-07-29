# License guide

## English

### Project license

The original AI Privacy Studio code and documentation are distributed under
the **GNU General Public License version 3 only** (`GPL-3.0-only`). The
authoritative terms are in [LICENSE](LICENSE).

GPLv3 was selected because it is a strong copyleft license and is compatible
with the permissive Apache-2.0, MIT, BSD, ISC, and HPND components used through
their documented interfaces. It is also the conservative project-level choice
in light of the separately executed GPLv3 Picocrypt CLI. AGPL was not selected
because no included or downloaded component requires network copyleft.

### What the project license covers

GPL-3.0-only covers the original source code, scripts, interface code, build
files, and original documentation in this repository. It does not replace the
licenses of third-party assets or programs.

- Inter remains under OFL-1.1.
- Lucide remains under ISC, with MIT terms for icons derived from Feather.
- Downloaded libraries and models retain the licenses listed in
  [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- Picocrypt, FFmpeg, Ollama, and uv are downloaded as separate programs and
  retain their own terms.
- The Windows and Linux package runtimes retain the Inno Setup and AppImage
  runtime notices stored in `licenses/`. The release includes corresponding
  source for the AppImage type-2 runtime.

### Main distributor duties

A person distributing the project or a modified version should, at minimum:

1. provide the complete corresponding source;
2. keep the GPL license and copyright notices;
3. license the covered modified work under GPLv3 only;
4. state significant modifications;
5. preserve all applicable third-party licenses and attributions;
6. repeat the inventory for any preassembled package that adds models,
   environments, libraries, or external executables.

The release installers produced by this repository contain the project source
and vendored interface assets. They download the large third-party components
on the user's computer rather than redistributing them inside the package.

This guide is a technical licensing analysis, not legal advice. Relicensing is
valid only if the person publishing the project owns or is authorized to
license all original contributions. Obtain qualified legal review before
commercial distribution or when ownership is uncertain.

---

## Italiano

### Licenza del progetto

Il codice e la documentazione originali di AI Privacy Studio sono distribuiti
sotto **GNU General Public License versione 3 soltanto**
(`GPL-3.0-only`). I termini giuridicamente rilevanti sono in
[LICENSE](LICENSE).

GPLv3 è stata scelta perché è una licenza copyleft forte ed è compatibile con i
componenti permissivi Apache-2.0, MIT, BSD, ISC e HPND usati tramite le loro
interfacce documentate. È anche la scelta prudenziale a livello di progetto
considerata l'esecuzione separata di Picocrypt CLI sotto GPLv3. AGPL non è stata
scelta perché nessun componente incluso o scaricato richiede il copyleft di
rete.

### Ambito della licenza

GPL-3.0-only copre il sorgente originale, gli script, il codice
dell'interfaccia, i file di build e la documentazione originale del repository.
Non sostituisce le licenze degli asset o dei programmi di terze parti.

- Inter resta sotto OFL-1.1.
- Lucide resta sotto ISC, con termini MIT per le icone derivate da Feather.
- Librerie e modelli scaricati conservano le licenze elencate in
  [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- Picocrypt, FFmpeg, Ollama e uv vengono scaricati come programmi separati e
  conservano i propri termini.
- I runtime dei pacchetti Windows e Linux conservano gli avvisi di Inno Setup e
  del runtime AppImage presenti in `licenses/`. La release include il sorgente
  corrispondente del runtime AppImage type-2.

### Principali obblighi del distributore

Chi distribuisce il progetto o una versione modificata dovrebbe almeno:

1. fornire il sorgente corrispondente completo;
2. conservare la GPL e gli avvisi di copyright;
3. applicare GPLv3 soltanto all'opera modificata coperta;
4. indicare le modifiche rilevanti;
5. conservare licenze e attribuzioni applicabili di terze parti;
6. ripetere l'inventario per ogni pacchetto preassemblato che aggiunga modelli,
   ambienti, librerie o eseguibili esterni.

Gli installer prodotti da questo repository contengono il sorgente del progetto
e gli asset dell'interfaccia inclusi. I componenti di terze parti più grandi
vengono scaricati sul computer dell'utente invece di essere ridistribuiti nel
pacchetto.

Questa guida è un'analisi tecnica delle licenze, non un parere legale. Il cambio
di licenza è valido soltanto se chi pubblica il progetto possiede o è
autorizzato a licenziare tutti i contributi originali. Prima di una
distribuzione commerciale o in caso di dubbi sulla titolarità serve una verifica
legale qualificata.
