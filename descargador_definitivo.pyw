# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Media Platform (Studio Master v1.0.0)
# Copyright (C) 2026 Autores y colaboradores de Media Platform
#
# Este programa es software libre: puede redistribuirlo y/o modificarlo bajo
# los términos de la Licencia Pública General de GNU publicada por la Free
# Software Foundation, ya sea la versión 3 de la Licencia o (a su elección)
# cualquier versión posterior (GPL-3.0-or-later).

# === LANZADOR MODULAR MEDIA PLATFORM PRO ===
import os
import sys


def _bootstrap_ssl_certificates() -> str:
    """
    Configura los certificados CA raíz de certifi antes de importar ssl, urllib o yt_dlp.
    Compatible con ejecución desde código fuente y con binarios empaquetados por PyInstaller (sys._MEIPASS).
    """
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "certifi", "cacert.pem"))
    try:
        import certifi
        candidates.append(certifi.where())
    except Exception:
        pass

    for ca_path in candidates:
        if ca_path and os.path.isfile(ca_path):
            os.environ["SSL_CERT_FILE"] = ca_path
            os.environ["REQUESTS_CA_BUNDLE"] = ca_path
            return ca_path
    return ""


_bootstrap_ssl_certificates()

# Activar ruta de plugins antes de cargar motores
from mpp.core import EngineHotSwapManager
EngineHotSwapManager.activate_plugins_path()

# Exportar todos los símbolos para compatibilidad total con tests y herramientas
from mpp.core import *
from mpp.workers import *
from mpp.themes import *
from mpp.ui import *

if __name__ == "__main__":
    main()
