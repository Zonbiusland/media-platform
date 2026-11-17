# Media Platform — Studio Master v1.0.0 (Dragon Forge)

[![Version: v1.0.0](https://img.shields.io/badge/Version-v1.0.0-brightgreen.svg)](https://github.com/Zonbiusland/media-platform/releases)
[![License: GPL v3+](https://img.shields.io/badge/License-GPLv3%2B-red.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6%20(LGPLv3)-green.svg)](https://wiki.qt.io/Qt_for_Python)

> **[English](#english-documentation-v100)** • **[Español](#documentaci%C3%B3n-en-espa%C3%B1ol-v100)** • **[GitHub Repository](https://github.com/Zonbiusland/media-platform)**

---

## English Documentation (v1.0.0)

**Media Platform v1.0.0 ("Dragon Forge")** is a free, open-source (`GPL-3.0-or-later`), portable desktop media workstation for Windows and GNU/Linux focused on privacy, security, and lossless post-processing.

### 1. Key Features

* **Bilingual UI (`English` / `Español`):** Auto-detects your OS locale (`QLocale.system().name()`) on first run and switches languages live via external JSON catalogs (`locales/`).
* **Simple & Advanced Modes:** Starts in clean **Simple Mode** (URL/search bar, preview, quality/format picker, output folder, Download) and toggles instantaneously to **Advanced Mode** (fragment threads, subtitles, SponsorBlock + local SmartSponsor transcript cutter, time trim, chapters, `-14 LUFS`, live DVR).
* **Smart Queue & Safe Defaults:** Non-destructive defaults (`SponsorBlock`, `SmartSponsor`, `LUFS`, and full-playlist auto-downloads off by default), `2` concurrent downloads (`4` fragment threads), explicit `Already downloaded (skipped)` status, optional `--force-overwrites` / **Force re-download**, and one-click **Show file**.
* **Local Library & FFmpeg Lab:** Indexed SQLite (`WAL` mode) history with `SHA-256` file checks, lossless `.mp4`/`.mkv` remuxing, Discord/WhatsApp size-target compression (`< 10/25/50 MB`), and audio extraction/normalization.
* **Security & Clean Lifecycle:** SSRF / DNS-rebinding guard (`SecurityGuard`), Zip-Slip defense, `SHA-256`-verified PyPI `yt-dlp` hot-swap updates, and clean child-process shutdown (`ProcessAndThreadRegistry`).

### 2. Quick Start

#### Option A — Portable Releases (Recommended)
Download ready-to-use packages from **[GitHub Releases](https://github.com/Zonbiusland/media-platform/releases)** (no Python installation required; bundles `FFmpeg`/`FFprobe`, `locales/`, and `mpp/assets/`):
* **Windows (64-bit):** Extract `MediaPlatform-Windows-x64.zip` and double-click **`MediaPlatform.exe`**.
* **GNU/Linux (64-bit):**
  ```bash
  tar -xzf MediaPlatform-Linux-x64.tar.gz
  cd MediaPlatform
  ./MediaPlatform
  ```

<details>
<summary><strong>Integrity Verification (SHA-256 / GitHub Attestations) & Windows SmartScreen</strong></summary>

* **Windows (PowerShell):**
  ```powershell
  Get-FileHash .\MediaPlatform-Windows-x64.zip -Algorithm SHA256
  Get-FileHash .\MediaPlatform.exe -Algorithm SHA256
  ```
  Compare against `SHA256SUMS.txt` (or verify GitHub Build Attestations on public releases via `gh attestation verify MediaPlatform-Windows-x64.zip --owner Zonbiusland`).
* **GNU/Linux:**
  ```bash
  sha256sum -c SHA256SUMS.txt --ignore-missing
  ```
* **SmartScreen Notice:** Because this is free `GPLv3` software without a paid Authenticode certificate, Windows SmartScreen may warn on first launch. After checking the `SHA-256` hash, click **"More info" → "Run anyway"**.

</details>

#### Option B — Run from Source
```bash
git clone https://github.com/Zonbiusland/media-platform.git
cd media-platform

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python descargador_definitivo.pyw
```

### 3. Quick Help / FAQ

* **Where is `portable_data/` stored?**
  Directly alongside the executable (`MediaPlatform.exe` / `MediaPlatform`) or inside the project root when running from source. It holds `settings.json`, `media_library.db`, hot-swapped `plugins/`, `bin/` (`ffmpeg`/`ffprobe`), and `temp/`. Deleting or moving the folder keeps everything self-contained.
* **How do I update `yt-dlp` and `FFmpeg`?**
  * **`yt-dlp`:** Open **System & Security → Update yt-dlp Engine Now** (or keep auto-update enabled). It downloads the official PyPI wheel, verifies its `SHA-256` digest, installs it into `portable_data/plugins/`, and supports one-click rollback.
  * **`FFmpeg` / `FFprobe`:** Portable builds already bundle them in `portable_data/bin/`. When running from source or replacing them manually, install FFmpeg system-wide (`PATH`) or drop updated binaries into `portable_data/bin/`.
* **What should I do if a video fails to download?**
  1. Run **Update yt-dlp Engine Now** in **System & Security** (fixes most platform extractor changes).
  2. For age-restricted, login-required, or HTTP `429` links, select your browser or a Netscape `cookies.txt` file under **Settings & Network** (or configure an HTTP/SOCKS5 proxy).
  3. Reduce queue concurrency (`1`–`2`) or try **Web Sniffer** for direct `.m3u8`/`.mpd` streams. If the file already exists on disk (`Already downloaded (skipped)`), enable **Overwrite existing files** or use **Force re-download** in the queue.

### 4. Project Structure, Tests (`pytest`) & Adding a Language

```text
media-platform/
├── descargador_definitivo.pyw   # Entry point & SSL/plugin bootstrap
├── locales/                     # External JSON catalogs (en.json, es.json)
├── mpp/
│   ├── __init__.py              # Package exports & version (1.0.0)
│   ├── core.py                  # Settings, SecurityGuard, SQLite, FFmpeg & engine updater
│   ├── workers.py               # Async QThread workers (yt-dlp, SmartSponsor, FFmpeg)
│   ├── themes.py                # Dragon Forge / ergonomic QSS & asset loader
│   ├── i18n.py                  # Locale detection & translation loader
│   ├── ui.py                    # MainWindow & controller logic
│   ├── assets/                  # Dragon Forge visual assets
│   └── views/                   # Modular UI tabs (capturer, queue, library, ffmpeg_lab, settings)
└── tests/                       # Automated pytest suite (54 tests)
    ├── test_database.py         # SQLite WAL & strict privacy mode
    ├── test_engine_update.py    # Hot-swap SHA-256, rollback, retry & overwrite flags
    ├── test_i18n.py             # JSON parity, placeholders, locale detection & safe defaults
    ├── test_security.py         # SSRF, redirect, Zip-Slip & path/template sanitization
    └── test_sponsor_detector.py # Offline VTT/SRT SmartSponsor transcript detection
```

* **Run the test suite:**
  ```bash
  .venv/bin/pip install -r requirements-dev.txt
  QT_QPA_PLATFORM=offscreen .venv/bin/pytest -v
  ```
* **Add a new language (`locales/<code>.json`):**
  1. Copy `locales/en.json` to `locales/<code>.json` (e.g., `fr.json`) and translate every value while keeping all JSON keys and `{placeholders}` intact.
  2. Register `<code>` in `I18nManager.SUPPORTED_LANGUAGES`, `LANGUAGE_LABELS`, `detect_system_language()`, and `normalize_lang()` inside `mpp/i18n.py`.
  3. Add the language option to `combo_header_lang` (`mpp/ui.py`) and `combo_language` (`mpp/views/settings.py`), then run `pytest -v`.

---

## Documentación en Español (v1.0.0)

**Media Platform v1.0.0 ("Dragon Forge")** es una estación multimedia libre (`GPL-3.0-or-later`), portable y multiplataforma (Windows y GNU/Linux), diseñada con foco en privacidad, seguridad y posprocesado sin pérdida.

### 1. Características principales

* **Interfaz bilingüe (`Español` / `English`):** Detecta el idioma del sistema al iniciar (`QLocale.system().name()`) y permite cambiarlo en caliente desde la cabecera o ajustes mediante catálogos JSON (`locales/`).
* **Modo Simple y Modo Avanzado:** Arranca en **Modo Simple** (barra de enlace/búsqueda, vista previa, selector de calidad/formato, carpeta y Descargar) y cambia al instante a **Modo Avanzado** (hilos por fragmento, subtítulos, SponsorBlock + SmartSponsor local, recorte temporal, capítulos, `-14 LUFS` y DVR).
* **Cola inteligente y valores seguros:** Filtros destructivos desactivados por defecto (`SponsorBlock`, `SmartSponsor`, `LUFS` y listas completas), `2` descargas simultáneas (`4` hilos por vídeo), estado claro `Ya descargado (omitido)`, opción `--force-overwrites` / **Forzar redescarga** y botón directo **Mostrar archivo**.
* **Videoteca SQLite y Laboratorio FFmpeg:** Historial indexado (`WAL`) con verificación `SHA-256`, remultiplexado `.mp4`/`.mkv` sin pérdida, compresión por tamaño objetivo (`< 10/25/50 MB` para Discord/WhatsApp) y extracción/normalización de audio.
* **Seguridad y ciclo de vida limpio:** Protección anti-SSRF / DNS-rebinding (`SecurityGuard`), defensa Zip-Slip, actualización en caliente de `yt-dlp` desde PyPI con verificación `SHA-256` y cierre ordenado de subprocesos (`ProcessAndThreadRegistry`).

### 2. Guía rápida de uso

#### Opción A — Paquetes portables (Recomendado)
Descarga el paquete listo para usar desde **[GitHub Releases](https://github.com/Zonbiusland/media-platform/releases)** (sin instalar Python; incluye `FFmpeg`/`FFprobe`, `locales/` y `mpp/assets/`):
* **Windows (64 bits):** Descomprime `MediaPlatform-Windows-x64.zip` y ejecuta **`MediaPlatform.exe`**.
* **GNU/Linux (64 bits):**
  ```bash
  tar -xzf MediaPlatform-Linux-x64.tar.gz
  cd MediaPlatform
  ./MediaPlatform
  ```

<details>
<summary><strong>Verificación de integridad (SHA-256 / Attestations) y Windows SmartScreen</strong></summary>

* **Windows (PowerShell):**
  ```powershell
  Get-FileHash .\MediaPlatform-Windows-x64.zip -Algorithm SHA256
  Get-FileHash .\MediaPlatform.exe -Algorithm SHA256
  ```
  Compara los hashes con `SHA256SUMS.txt` (o verifica la procedencia en lanzamientos públicos con `gh attestation verify MediaPlatform-Windows-x64.zip --owner Zonbiusland`).
* **GNU/Linux:**
  ```bash
  sha256sum -c SHA256SUMS.txt --ignore-missing
  ```
* **Aviso de SmartScreen:** Al ser software libre `GPLv3` sin certificado comercial de pago, Windows SmartScreen puede mostrar un aviso preventivo la primera vez. Tras validar el `SHA-256`, pulsa **"Más información" → "Ejecutar de todas formas"**.

</details>

#### Opción B — Ejecución desde código fuente
```bash
git clone https://github.com/Zonbiusland/media-platform.git
cd media-platform

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python descargador_definitivo.pyw
```

### 3. Ayuda rápida / FAQ

* **¿Dónde se guarda `portable_data/`?**
  Junto al ejecutable (`MediaPlatform.exe` / `MediaPlatform`) o en la raíz del proyecto si ejecutas desde fuente. Contiene `settings.json`, `media_library.db`, `plugins/`, `bin/` (`ffmpeg`/`ffprobe`) y `temp/`.
* **¿Cómo se actualizan `yt-dlp` y `FFmpeg`?**
  * **`yt-dlp`:** Desde **Sistema y Seguridad → Actualizar Motor yt-dlp Ahora** (o con auto-actualización activa). Descarga el wheel oficial de PyPI, valida su `SHA-256`, lo instala en `portable_data/plugins/` y permite rollback en un clic.
  * **`FFmpeg` / `FFprobe`:** Los paquetes portables ya los incluyen en `portable_data/bin/`. Desde código fuente o para actualizarlos manualmente, instálalos en el sistema (`PATH`) o copia los binarios dentro de `portable_data/bin/`.
* **¿Qué hago si falla la descarga de un vídeo?**
  1. Pulsa **Actualizar Motor yt-dlp Ahora** en **Sistema y Seguridad** (resuelve la mayoría de cambios en plataformas).
  2. Para vídeos con restricción de edad, sesión o error HTTP `429`, selecciona las cookies de tu navegador o un archivo `cookies.txt` (Netscape) en **Ajustes y Red** (o configura un proxy HTTP/SOCKS5).
  3. Reduce la concurrencia (`1`–`2`) o prueba **Cazador Web** para flujos directos `.m3u8`/`.mpd`. Si aparece `Ya descargado (omitido)`, activa **Sobrescribir archivos ya descargados** o usa **Forzar redescarga** en la cola.

### 4. Estructura del proyecto, `pytest` y añadir un idioma

```text
media-platform/
├── descargador_definitivo.pyw   # Punto de entrada y arranque SSL/plugins
├── locales/                     # Catálogos JSON externos (en.json, es.json)
├── mpp/
│   ├── __init__.py              # Exportación del paquete y versión (1.0.0)
│   ├── core.py                  # Ajustes, SecurityGuard, SQLite, FFmpeg y actualizador
│   ├── workers.py               # Hilos QThread (yt-dlp, SmartSponsor, FFmpeg)
│   ├── themes.py                # Temas Dragon Forge / ergonómicos y carga de activos
│   ├── i18n.py                  # Detección de idioma y gestor de traducciones
│   ├── ui.py                    # MainWindow y coordinador de interfaz
│   ├── assets/                  # Activos visuales Dragon Forge
│   └── views/                   # Vistas modulares (capturer, queue, library, ffmpeg_lab, settings)
└── tests/                       # Suite automatizada pytest (54 tests)
    ├── test_database.py         # SQLite WAL y modo privacidad estricta
    ├── test_engine_update.py    # Hot-swap SHA-256, rollback, reintento y sobrescritura
    ├── test_i18n.py             # Paridad JSON, marcadores, idioma y valores seguros
    ├── test_security.py         # SSRF, redirecciones, Zip-Slip y sanitización de rutas
    └── test_sponsor_detector.py # Detección offline VTT/SRT de SmartSponsor
```

* **Ejecutar los tests (`pytest`):**
  ```bash
  .venv/bin/pip install -r requirements-dev.txt
  QT_QPA_PLATFORM=offscreen .venv/bin/pytest -v
  ```
* **Añadir un nuevo idioma (`locales/<código>.json`):**
  1. Copia `locales/en.json` a `locales/<código>.json` (p. ej. `fr.json`) y traduce los textos manteniendo intactas todas las claves y variables `{...}`.
  2. Registra el código en `I18nManager.SUPPORTED_LANGUAGES`, `LANGUAGE_LABELS`, `detect_system_language()` y `normalize_lang()` dentro de `mpp/i18n.py`.
  3. Añade el idioma a `combo_header_lang` (`mpp/ui.py`) y `combo_language` (`mpp/views/settings.py`), y verifica ejecutando `pytest -v`.

---

## License / Licencia

Copyright (C) 2026 Media Platform Authors & Contributors.  
Repository / Repositorio oficial: [https://github.com/Zonbiusland/media-platform](https://github.com/Zonbiusland/media-platform)

This program is free software: you can redistribute it and/or modify it under the terms of the **GNU General Public License** as published by the Free Software Foundation, either **version 3** of the License, or (at your option) any later version (`GPL-3.0-or-later`). See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for full details.
