# Third-party notices

AI Privacy Studio is licensed under GNU GPL version 3 only. That license
applies only to the original code and documentation in this repository.
Dependencies, models, fonts, icons, and external programs remain under their
respective licenses.

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
The requirements files pin direct dependencies used by this release.
Transitive resolutions can vary by supported platform and must be inventoried
again when distributing a preassembled environment.

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
| Wexpect | 4.0.0 | MIT |
| Setuptools | 83.0.0 | MIT |
| imageio-ffmpeg | 0.6.0 | BSD-2-Clause; platform wheels include a separate FFmpeg executable |
| python-zstandard | 0.25.0 | BSD-3-Clause |
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
| Rizzo PII 0.3B (Simone Rizzo / Rizzo AI Academy) | 0.3B (ModernBERT) | MIT (Base model mmBERT: Apache-2.0) |

### Interactive Anonymization UI & Color Palette Attribution
- **Source**: Rizzo PII (`https://github.com/Rizzo-AI-Academy/rizzo-pii`) by Simone Rizzo / Rizzo AI Academy
- **License**: MIT License
- **Usage**: PII Entity Tag color system, inline placeholder/original toggle design, and formatted document print preview.

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
| OpenAI Privacy Filter | Apache-2.0 | Package commit `f7f00ca7fb869683eb732c010299d901457f19c3`; model revision `7ffa9a043d54d1be65afb281eddf0ffbe629385b`; [OpenAI Privacy Filter](https://github.com/openai/privacy-filter) |
| NVIDIA Parakeet TDT 0.6B v3 | CC-BY-4.0 | Revision `7c35754d166cca382ad1e53e68b01e7c575f3a1d`; [NVIDIA model card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) |
| GLM-OCR | MIT | Ollama tag `glm-ocr:q8_0`, manifest digest `2a5a0f1a93017fc9db321ec196efb4b9bbba97c4d890df8e39429ed771f2ed25`; [Z.ai model card](https://huggingface.co/zai-org/GLM-OCR) |
| PaddleOCR models | Apache-2.0 | [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) |

## Separate external programs

These programs are not part of the GPL-3.0-only project code. They
communicate with Privacy Studio through command-line arguments, pipes, or a
loopback API and retain their own licenses.

| Program | Use | License/distribution |
| --- | --- | --- |
| [Picocrypt CLI 1.49](https://github.com/Picocrypt/CLI) | `.pcv` encryption and decryption | GPL-3.0-only. The binary is excluded from Git, downloaded unmodified from the official release, verified by SHA-256, and invoked as a separate process. The installer also downloads and verifies its complete GPL license. Its upstream repository has been archived since August 2025 and no longer receives maintenance updates. |
| Ollama 0.32.5 | Local GLM-OCR runtime | MIT. Excluded from Git; the installer downloads an official unmodified archive and verifies its SHA-256 digest. |
| FFmpeg 7.0.2 | Local audio normalization | The `imageio-ffmpeg` wheel supplies and Privacy Studio invokes it as a separate process. The inspected Linux x86-64 wheel reports `--enable-gpl --enable-version3`, making that executable GPL-3.0-or-later; other wheel builds must be checked individually. It is excluded from Git. |
| uv 0.11.16 | Verified Python and environment bootstrap | Apache-2.0 OR MIT. Excluded from Git; the root installer downloads the official release and verifies its SHA-256 digest. |
| Default web browser | Local user interface | Already installed by the user; not redistributed by this repository |

The Free Software Foundation notes that command-line arguments are normally a
communication mechanism between separate programs. Whether programs form one
combined legal work ultimately depends on the facts and applicable law:
<https://www.gnu.org/licenses/gpl-faq.html#MereAggregation>.

## Installer container runtimes

The release packages contain the project source and the two vendored interface
assets above. Large downloaded runtimes, Python environments, model weights,
Picocrypt, Ollama, and FFmpeg are not embedded in the `.exe`, `.AppImage`, or
`.dmg`.

| Component | Package | License/notice |
| --- | --- | --- |
| AppImage type-2 runtime | Linux `.AppImage` | MIT plus the statically linked notices listed in `licenses/APPIMAGE-RUNTIME-MIT.txt`. The release also provides `AppImage-runtime-corresponding-source-75849dce7cc37e4319b633df1f116ca895c71a12.tar.gz`. |
| Official appimagetool | Linux package build only; not included in the release | MIT; `licenses/APPIMAGETOOL-MIT.txt` |
| Inno Setup runtime | Windows `.exe` | Inno Setup License; `licenses/INNO-SETUP.txt` |
| Apple `hdiutil` disk-image format | macOS `.dmg` | Built with the operating-system tool; no third-party runtime is added by this repository |

## Deliberate licensing boundary

PyMuPDF is not a dependency of AI Privacy Studio. PDF rendering uses
pypdfium2 to avoid introducing PyMuPDF's AGPL/commercial licensing terms into
the application.
