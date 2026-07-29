# Third-party notices

Privacy Studio Locale is licensed under the 0BSD License. That license applies
only to the original code and documentation in this repository. Dependencies,
models, fonts, icons, and external programs remain under their respective
licenses.

This inventory is provided for transparency and release preparation. It is not
legal advice. Before distributing a bundled binary release, regenerate the
inventory for the exact artifacts included in that release.

## Vendored interface assets

These files are committed to the repository and served locally. No CDN or
remote font service is contacted at runtime.

| Component | Version | License | Local notice |
| --- | ---: | --- | --- |
| [Inter](https://github.com/rsms/inter) | 4.1 | SIL Open Font License 1.1 | `licenses/INTER-OFL-1.1.txt` |
| [Lucide](https://github.com/lucide-icons/lucide) | 1.27.0 | ISC | `licenses/LUCIDE-ISC.txt` |

## Installed Python dependencies

The repository does not commit virtual environments or Python wheels. The
installer obtains these packages from their upstream distribution channels.
The lock-style requirements files contain the versions used by this release.

| Component | Version/reference | License |
| --- | ---: | --- |
| FastAPI | 0.140.13 | MIT |
| Uvicorn | 0.51.0 | BSD-3-Clause |
| python-multipart | 0.0.32 | Apache-2.0 |
| HTTPX | 0.28.1 | BSD-3-Clause |
| Microsoft MarkItDown | 0.1.6 | MIT |
| pypdfium2 | 5.12.1 | BSD-3-Clause / Apache-2.0; its wheel carries PDFium and dependency notices |
| Pillow | 12.3.0 | HPND |
| Pexpect | 4.9.0 | ISC |
| PyTorch | 2.13.0 CPU | BSD-3-Clause |
| Hugging Face Transformers | 5.14.1 | Apache-2.0 |
| Hugging Face Accelerate | 1.14.0 | Apache-2.0 |
| NumPy | 2.3.5 | BSD-3-Clause plus bundled dependency notices |
| Numba | 0.63.1 | BSD-2-Clause |
| librosa | 0.11.0 | ISC |
| python-soundfile | 0.14.0 | BSD-3-Clause |
| PaddlePaddle | 3.3.1 | Apache-2.0 |
| PaddleOCR / PaddleX | 3.7.x | Apache-2.0 |
| OpenAI Privacy Filter package | commit `f7f00ca7fb869683eb732c010299d901457f19c3` | Apache-2.0 |

Transitive dependencies keep their upstream licenses. Their license metadata
is installed inside each virtual environment by the package manager.

Notable weak-copyleft transitive libraries currently installed by the pinned
dependency sets include `soxr` (LGPL-2.1-or-later), `crc32c` (LGPL-2.0-or-later),
`cssutils` (LGPL-3.0-or-later), `encutils` (LGPL-3.0-or-later), and
`python-bidi` (LGPL). They are not copied into this source repository. The
LGPL permits a larger work using these libraries through their interfaces to
use different terms; distributors of a bundled binary must still satisfy the
libraries' notice, source, and relinking requirements as applicable.

## Downloaded models

Model weights are deliberately excluded from Git. The installation scripts
download them into user caches.

| Model | License | Attribution/source |
| --- | --- | --- |
| OpenAI Privacy Filter | Apache-2.0 | [OpenAI Privacy Filter](https://github.com/openai/privacy-filter) |
| NVIDIA Parakeet TDT 0.6B v3 | CC-BY-4.0 | Revision `7c35754d166cca382ad1e53e68b01e7c575f3a1d`; [NVIDIA model card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) |
| GLM-OCR | MIT | [Z.ai model card](https://huggingface.co/zai-org/GLM-OCR) |
| PaddleOCR models | Apache-2.0 | [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) |

## Separate external programs

These programs are not part of the 0BSD-licensed source code. They communicate
with Privacy Studio through command-line arguments or a loopback API and retain
their own licenses.

| Program | Use | License/distribution |
| --- | --- | --- |
| Picocrypt CLI 1.49 | `.pcv` encryption and decryption | GPL-3.0-only. The binary is excluded from Git, downloaded unmodified from the official release, verified by SHA-256, and invoked as a separate process. The installer also downloads and verifies its complete GPL license. |
| Ollama | Local GLM-OCR runtime | MIT; installed separately by the user |
| FFmpeg / ffprobe | Local audio normalization | System package; license depends on the distribution build, commonly LGPL/GPL |
| Chromium or Google Chrome | Dedicated local application window | System browser; not redistributed by this repository |

The Free Software Foundation notes that command-line arguments are normally a
communication mechanism between separate programs. Whether programs form one
combined legal work ultimately depends on the facts and applicable law:
<https://www.gnu.org/licenses/gpl-faq.html#MereAggregation>.

## Deliberate licensing boundary

PyMuPDF is not a dependency of Privacy Studio Locale. PDF rendering uses
pypdfium2 to avoid introducing PyMuPDF's AGPL/commercial licensing terms into
the application.
