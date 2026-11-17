# Avisos de Componentes de Terceros y Licencias Libres (Third-Party Notices)

**Media Platform v1.0.0 (Studio Master — Dragon Forge)**  
Copyright (C) 2026 Media Platform Authors & Contributors  
Repositorio oficial: https://github.com/Zonbiusland/media-platform  

Se distribuye bajo los términos de la licencia **GNU General Public License v3.0 o posterior (`GPL-3.0-or-later`)**. Todo el código fuente propio, el motor local `SmartSponsorDetector`, la interfaz ergonómica y los activos generados del proyecto son software libre.

A continuación se detallan las licencias libres de las bibliotecas, herramientas y recursos con los que interactúa este proyecto:

---

## 1. PySide6 (Qt for Python / Qt6)
* **Uso en el proyecto:** Interfaz gráfica de escritorio multiplataforma (`QtCore`, `QtGui`, `QtWidgets`, `QtSvg`) y renderizado vectorial nativo (`QPainter`).
* **Licencia:** **GNU Lesser General Public License v3.0 (LGPL-3.0-only / GPL-3.0-only)**.
* **Compatibilidad con GPLv3:** Totalmente compatible con GNU GPLv3 (según la sección 2b/3 de la LGPLv3). PySide6 se enlaza dinámicamente a través del entorno de Python / PyInstaller sin modificar sus binarios.
* **Sitio oficial y código fuente:** https://wiki.qt.io/Qt_for_Python / https://www.qt.io/ / https://code.qt.io/cgit/pyside/pyside-setup.git

---

## 2. yt-dlp
* **Uso en el proyecto:** Motor de extracción de metadatos, subtítulos y flujos multimedia.
* **Licencia:** **The Unlicense (Dominio Público)**.
* **Compatibilidad con GPLv3:** Totalmente compatible (dominio público sin restricciones).
* **Sitio oficial y código fuente:** https://github.com/yt-dlp/yt-dlp

---

## 3. FFmpeg y FFprobe (Herramientas externas del sistema)
* **Uso en el proyecto:** Invocados como subprocesos independientes (`subprocess.Popen` con `shell=False`) para multiplexación sin pérdida (`-c copy`), recorte de segmentos patrocinados (`concat` demuxer), normalización de sonoridad EBU R128 (`loudnorm` en doble pasada) e inspección técnica de pistas (`ffprobe`).
* **Licencia:** **GNU Lesser General Public License (LGPL) v2.1+** o **GNU General Public License (GPL) v2+ / v3+** (según las banderas de compilación del paquete, como `--enable-gpl` para `libx264`).
* **Distribución:** El repositorio fuente **no almacena binarios precompilados** de FFmpeg ni FFprobe. En los paquetes portables de lanzamiento generados mediante GitHub Actions (`.github/workflows/build.yml`), se adjuntan binarios oficiales libres (`gyan.dev` essentials para Windows x64 y `BtbN/FFmpeg-Builds` GPL para GNU/Linux x64) junto con `LICENSE`, `README.md` y este archivo `THIRD_PARTY_NOTICES.md`.
* **Sitio oficial y código fuente:** https://ffmpeg.org/

---

## 4. faster-whisper (Respaldo opcional)
* **Uso en el proyecto:** Respaldo opcional para transcribir audio localmente (modelo `"base"`) cuando un vídeo no dispone de subtítulos manuales ni automáticos y `SponsorBlock` devuelve 0 segmentos.
* **Licencia:** **MIT License**.
* **Compatibilidad con GPLv3:** Totalmente compatible con GNU GPLv3.
* **Sitio oficial y código fuente:** https://github.com/SYSTRAN/faster-whisper

---

## 5. Activos Gráficos, Iconografía y Tipografías
* **Iconografía vectorial propia (`GPL-3.0-or-later`):** Todos los iconos de controles de la interfaz (`arrow_down.png`, `arrow_up.png`, `check_mark.png` y el emblema de aplicación generado dinámicamente) son dibujados matemáticamente en tiempo de ejecución mediante `PySide6.QtGui.QPainter` dentro de `ErgonomicThemeEngine` (`mpp/themes.py`), sin depender de activos privativos de terceros.
* **Tipografías libres del sistema:** La hoja de estilos (`mpp/themes.py` y `mpp/ui.py`) prioriza exclusivamente familias tipográficas libres estándar del sistema operativo:
  * **Interfaz general (Sans-Serif):** *Noto Sans* (SIL OFL 1.1), *Ubuntu* (Ubuntu Font Licence 1.0), *Cantarell* (SIL OFL 1.1), *DejaVu Sans* (Bitstream Vera / Public Domain) y *Liberation Sans* (SIL OFL 1.1).
  * **Consolas técnicas y registros (Monospace):** *JetBrains Mono* (SIL OFL 1.1), *DejaVu Sans Mono*, *Liberation Mono* y *Ubuntu Mono*.
