# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Media Platform (Studio Master) — Núcleo del Sistema (GPLv3+)
# Este archivo es software libre distribuido bajo la licencia GNU GPL v3.0 o posterior.
import os
import io
import re
import gc
import sys


def configure_ssl_certificates() -> str:
    """
    Configura SSL_CERT_FILE y REQUESTS_CA_BUNDLE apuntando al bundle de certifi
    antes de importar ssl, urllib o yt_dlp (compatible con PyInstaller sys._MEIPASS).
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


configure_ssl_certificates()

import csv
import glob
import json
import math
import time
import uuid
import shutil
import ctypes
import socket
import sqlite3
import hashlib
import tempfile
import zipfile
import zipimport
import importlib
import importlib.util
import ipaddress
import threading
import subprocess
import urllib.error
import urllib.request
import urllib.parse
from datetime import datetime
from urllib.parse import urlparse, urljoin

# Asegurar descriptores estándar en entornos GUI sin consola (.pyw / frozen)
if sys.stdout is None or not hasattr(sys.stdout, "write"):
    sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="ignore")
if sys.stderr is None or not hasattr(sys.stderr, "write"):
    sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="ignore")
if sys.stdin is None or not hasattr(sys.stdin, "read"):
    sys.stdin = open(os.devnull, "r", encoding="utf-8", errors="ignore")

# Evitar ventanas emergentes de consola en subprocesos bajo Windows
if os.name == "nt" and not getattr(subprocess, "_mpp_patched_popen", False):
    _orig_popen = subprocess.Popen

    class _SafePopen(_orig_popen):
        def __init__(self, *args, **kwargs):
            if "stdin" not in kwargs or kwargs["stdin"] is None:
                kwargs["stdin"] = subprocess.DEVNULL
            if "creationflags" not in kwargs:
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)

    subprocess.Popen = _SafePopen
    subprocess._mpp_patched_popen = True


def get_app_root_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_portable_data_dir() -> str:
    p_dir = os.path.join(get_app_root_dir(), "portable_data")
    os.makedirs(p_dir, exist_ok=True)
    return p_dir


def get_app_data_dir() -> str:
    """Alias unificado hacia portable_data para garantizar portabilidad total en Linux y Windows."""
    return get_portable_data_dir()


def setup_isolated_temp_dir() -> str:
    t_dir = os.path.join(get_portable_data_dir(), "temp")
    os.makedirs(t_dir, exist_ok=True)
    os.environ["TEMP"] = t_dir
    os.environ["TMP"] = t_dir
    os.environ["TMPDIR"] = t_dir
    tempfile.tempdir = t_dir
    return t_dir


def get_default_download_dir() -> str:
    """Detecta un directorio de descargas válido y escribible en Linux y Windows."""
    candidates = []

    if os.name != "nt":
        xdg_bin = shutil.which("xdg-user-dir")
        if xdg_bin:
            try:
                res = subprocess.run(
                    [xdg_bin, "DOWNLOAD"],
                    capture_output=True, text=True, timeout=2, shell=False
                )
                xdg_dir = (res.stdout or "").strip()
                if xdg_dir and os.path.isabs(xdg_dir):
                    candidates.append(xdg_dir)
            except Exception:
                pass

    home = os.path.expanduser("~")
    if home:
        candidates.extend([
            os.path.join(home, "Descargas"),
            os.path.join(home, "Downloads"),
        ])

    for cand in candidates:
        if os.path.isdir(cand) and os.access(cand, os.W_OK):
            return os.path.realpath(cand)

    local_dl = os.path.join(get_app_root_dir(), "Descargas")
    os.makedirs(local_dl, exist_ok=True)
    return os.path.realpath(local_dl)


def get_resource_path(filename: str) -> str | None:
    if not filename:
        return None
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, filename))
    root_dir = get_app_root_dir()
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.extend([
        os.path.join(root_dir, filename),
        os.path.join(root_dir, "_internal", filename),
        os.path.join(get_portable_data_dir(), filename),
        os.path.join(get_portable_data_dir(), "bin", filename),
        os.path.join(exe_dir, filename),
        os.path.join(exe_dir, "_internal", filename),
        os.path.join(script_dir, filename),
    ])
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def resource_path(rel_path: str) -> str:
    """Resuelve rutas relativas de recursos (ej. 'mpp/assets/dragon_emblem.png') en fuente y PyInstaller (_MEIPASS)."""
    norm_rel = os.path.normpath(str(rel_path or "").strip()).lstrip("/\\")
    if not norm_rel:
        return ""
    bases = []
    if hasattr(sys, "_MEIPASS"):
        bases.append(sys._MEIPASS)
    root_dir = get_app_root_dir()
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    bases.extend([
        root_dir,
        os.path.join(root_dir, "_internal"),
        exe_dir,
        os.path.join(exe_dir, "_internal"),
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ])
    for base in bases:
        cand = os.path.join(base, norm_rel)
        if os.path.exists(cand):
            return cand
    return os.path.join(root_dir, norm_rel)


PORTABLE_DATA_DIR = get_portable_data_dir()
PORTABLE_TEMP_DIR = setup_isolated_temp_dir()


class EngineHotSwapManager:
    APP_DIR = PORTABLE_DATA_DIR
    PLUGINS_DIR = os.path.join(APP_DIR, "plugins")
    ALLOWED_WHEEL_HOST = "files.pythonhosted.org"
    MAX_WHEEL_BYTES = 50 * 1024 * 1024
    _update_lock = threading.Lock()

    @classmethod
    def _rebind_yt_dlp_global(cls, mod):
        globals()["yt_dlp"] = mod
        for m_name in ("mpp.core", "mpp.workers", "mpp.ui", "descargador_definitivo"):
            m_obj = sys.modules.get(m_name)
            if m_obj is not None:
                setattr(m_obj, "yt_dlp", mod)

    @classmethod
    def _get_yt_dlp_version(cls, mod) -> str:
        try:
            ver_mod = getattr(mod, "version", None)
            if ver_mod is not None and hasattr(ver_mod, "__version__"):
                return str(ver_mod.__version__)
            return str(getattr(mod, "__version__", "?"))
        except Exception:
            return "?"

    @classmethod
    def has_external_plugin(cls) -> bool:
        cls.APP_DIR = get_portable_data_dir()
        cls.PLUGINS_DIR = os.path.join(cls.APP_DIR, "plugins")
        return os.path.isfile(os.path.join(cls.PLUGINS_DIR, "yt_dlp", "__init__.py"))

    @classmethod
    def has_backup_plugin(cls) -> bool:
        cls.APP_DIR = get_portable_data_dir()
        cls.PLUGINS_DIR = os.path.join(cls.APP_DIR, "plugins")
        return os.path.isfile(os.path.join(cls.PLUGINS_DIR, "yt_dlp.bak", "__init__.py"))

    @classmethod
    def can_rollback(cls) -> bool:
        return cls.has_external_plugin() or cls.has_backup_plugin()

    @classmethod
    def load_plugin_yt_dlp(cls):
        """
        Carga yt_dlp directamente desde portable_data/plugins/yt_dlp con prioridad absoluta
        sobre el paquete congelado en PyInstaller o el entorno virtual, sin secuestrar la stdlib.
        """
        cls.APP_DIR = get_portable_data_dir()
        cls.PLUGINS_DIR = os.path.join(cls.APP_DIR, "plugins")
        pkg_dir = os.path.realpath(os.path.join(cls.PLUGINS_DIR, "yt_dlp"))
        init_py = os.path.join(pkg_dir, "__init__.py")
        if not os.path.isfile(init_py):
            return None

        try:
            for k in list(sys.modules.keys()):
                if k == "yt_dlp" or k.startswith("yt_dlp."):
                    sys.modules.pop(k, None)

            spec = importlib.util.spec_from_file_location(
                "yt_dlp",
                init_py,
                submodule_search_locations=[pkg_dir]
            )
            if spec is None or spec.loader is None:
                return None
            mod = importlib.util.module_from_spec(spec)
            sys.modules["yt_dlp"] = mod
            spec.loader.exec_module(mod)
            cls._rebind_yt_dlp_global(mod)
            return mod
        except Exception:
            return None

    @classmethod
    def activate_plugins_path(cls) -> str:
        cls.APP_DIR = get_portable_data_dir()
        cls.PLUGINS_DIR = os.path.join(cls.APP_DIR, "plugins")
        os.makedirs(cls.PLUGINS_DIR, exist_ok=True)
        plugins_str = str(cls.PLUGINS_DIR)
        if plugins_str not in sys.path:
            sys.path.append(plugins_str)
        cls.load_plugin_yt_dlp()
        return cls.PLUGINS_DIR

    @classmethod
    def update_yt_dlp_plugin(cls) -> tuple[bool, str]:
        with cls._update_lock:
            cls.activate_plugins_path()
            tmp_whl = os.path.join(cls.PLUGINS_DIR, "yt_dlp_update.whl")
            pkg_dir = os.path.join(cls.PLUGINS_DIR, "yt_dlp")
            bak_dir = os.path.join(cls.PLUGINS_DIR, "yt_dlp.bak")
            moved_to_backup = False
            try:
                req = urllib.request.Request(
                    "https://pypi.org/pypi/yt-dlp/json",
                    headers={"User-Agent": "MediaPlatform/1.0.0"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read(5 * 1024 * 1024).decode("utf-8"))
                version = data.get("info", {}).get("version", "")
                wheel_url = ""
                expected_sha256 = ""
                for item in data.get("urls", []):
                    if item.get("packagetype") == "bdist_wheel" and item.get("filename", "").endswith(".whl"):
                        wheel_url = str(item.get("url") or "").strip()
                        expected_sha256 = str((item.get("digests") or {}).get("sha256") or "").strip().lower()
                        break
                if not wheel_url:
                    return False, "No se encontró paquete wheel oficial en PyPI."

                parsed_whl = urlparse(wheel_url)
                if parsed_whl.scheme.lower() != "https" or (parsed_whl.hostname or "").lower() != cls.ALLOWED_WHEEL_HOST:
                    return False, f"Dominio de descarga no autorizado: {parsed_whl.hostname}"

                if len(expected_sha256) != 64 or not all(c in "0123456789abcdef" for c in expected_sha256):
                    return False, "PyPI no proporcionó un hash SHA-256 válido para verificar el paquete."

                req_whl = urllib.request.Request(wheel_url, headers={"User-Agent": "MediaPlatform/1.0.0"})
                hasher = hashlib.sha256()
                downloaded = 0
                with urllib.request.urlopen(req_whl, timeout=25) as resp_whl, open(tmp_whl, "wb") as out_f:
                    while True:
                        chunk = resp_whl.read(65536)
                        if not chunk:
                            break
                        downloaded += len(chunk)
                        if downloaded > cls.MAX_WHEEL_BYTES:
                            raise RuntimeError("El archivo wheel excede el límite de tamaño seguro (50 MB).")
                        hasher.update(chunk)
                        out_f.write(chunk)

                actual_sha256 = hasher.hexdigest().lower()
                if actual_sha256 != expected_sha256:
                    try:
                        os.remove(tmp_whl)
                    except Exception:
                        pass
                    return False, "Fallo de seguridad: el hash SHA-256 del paquete descargado no coincide con PyPI."

                real_plugins_dir = os.path.realpath(cls.PLUGINS_DIR)
                cls.safe_extract_wheel(tmp_whl, real_plugins_dir, dry_run=True)

                if os.path.isdir(pkg_dir):
                    shutil.rmtree(bak_dir, ignore_errors=True)
                    shutil.move(pkg_dir, bak_dir)
                    moved_to_backup = True

                cls.safe_extract_wheel(tmp_whl, real_plugins_dir, dry_run=False)
                cls.load_plugin_yt_dlp()

                return True, f"Motor yt-dlp {version} actualizado en caliente (SHA-256 verificado)."
            except Exception as e:
                if moved_to_backup and os.path.isdir(bak_dir) and not os.path.isdir(pkg_dir):
                    try:
                        shutil.move(bak_dir, pkg_dir)
                        cls.load_plugin_yt_dlp()
                    except Exception:
                        pass
                return False, f"Error actualizando plugin: {e}"
            finally:
                try:
                    if os.path.isfile(tmp_whl):
                        os.remove(tmp_whl)
                except Exception:
                    pass

    @classmethod
    def rollback_yt_dlp_plugin(cls) -> tuple[bool, str]:
        """Revierte yt-dlp a la versión anterior en respaldo (yt_dlp.bak) o al motor nativo integrado."""
        with cls._update_lock:
            cls.APP_DIR = get_portable_data_dir()
            cls.PLUGINS_DIR = os.path.join(cls.APP_DIR, "plugins")
            pkg_dir = os.path.join(cls.PLUGINS_DIR, "yt_dlp")
            bak_dir = os.path.join(cls.PLUGINS_DIR, "yt_dlp.bak")

            try:
                if os.path.isfile(os.path.join(bak_dir, "__init__.py")):
                    shutil.rmtree(pkg_dir, ignore_errors=True)
                    shutil.move(bak_dir, pkg_dir)
                    mod = cls.load_plugin_yt_dlp()
                    ver = cls._get_yt_dlp_version(mod) if mod else "?"
                    return True, f"Motor yt-dlp revertido a la versión anterior ({ver})."

                if os.path.isdir(pkg_dir):
                    shutil.rmtree(pkg_dir, ignore_errors=True)
                    for k in list(sys.modules.keys()):
                        if k == "yt_dlp" or k.startswith("yt_dlp."):
                            sys.modules.pop(k, None)
                    plugins_str = str(cls.PLUGINS_DIR)
                    removed_from_path = False
                    if plugins_str in sys.path:
                        sys.path.remove(plugins_str)
                        removed_from_path = True
                    try:
                        mod = importlib.import_module("yt_dlp")
                    finally:
                        if removed_from_path:
                            sys.path.append(plugins_str)
                    cls._rebind_yt_dlp_global(mod)
                    ver = cls._get_yt_dlp_version(mod)
                    return True, f"Plugin externo eliminado; restaurado motor nativo integrado ({ver})."

                return False, "No existe ninguna actualización externa ni copia de seguridad para revertir."
            except Exception as e:
                return False, f"Error al revertir motor yt-dlp: {e}"

    @classmethod
    def validate_zip_member(cls, member: str, target_dir: str) -> tuple[bool, str]:
        """Valida que una entrada de archivo ZIP/Wheel no contenga secuencias Zip Slip ('..', rutas absolutas)."""
        raw = str(member or "")
        if not raw or "\x00" in raw:
            return False, "Nombre de entrada ZIP vacío o con byte nulo."
        norm_slashes = raw.replace("\\", "/")
        norm_parts = norm_slashes.split("/")
        if os.path.isabs(raw) or norm_slashes.startswith("/") or re.match(r"^[a-zA-Z]:", norm_slashes) or ".." in norm_parts:
            return False, f"Entrada ZIP maliciosa bloqueada (Zip Slip): {raw}"
        real_base = os.path.realpath(target_dir)
        dest_real = os.path.realpath(os.path.join(real_base, norm_slashes))
        try:
            common = os.path.commonpath([real_base, dest_real])
        except ValueError:
            return False, f"Unidad de destino distinta bloqueada: {raw}"
        if common != real_base:
            return False, f"Intento de escritura fuera de PLUGINS_DIR bloqueado: {raw}"
        return True, dest_real

    @classmethod
    def safe_extract_wheel(cls, whl_path: str, target_dir: str, required_prefix: str = "yt_dlp/", dry_run: bool = False) -> list[str]:
        """Extrae de forma segura un archivo .whl/.zip verificando cada miembro contra Zip Slip antes de escribir."""
        real_base = os.path.realpath(target_dir)
        extracted = []
        with zipfile.ZipFile(whl_path, "r") as zf:
            members_to_extract = []
            for info_member in zf.infolist():
                member = info_member.filename
                ok_zip, msg_or_dest = cls.validate_zip_member(member, real_base)
                if not ok_zip:
                    raise RuntimeError(msg_or_dest)
                if required_prefix and not member.replace("\\", "/").startswith(required_prefix):
                    continue
                members_to_extract.append((info_member, msg_or_dest))

            if dry_run:
                return [dest_path for _, dest_path in members_to_extract]

            for info_member, dest_path in members_to_extract:
                zf.extract(info_member, real_base)
                extracted.append(dest_path)
        return extracted

    @staticmethod
    def _version_tuple(ver_str: str) -> tuple[int, ...]:
        parts = []
        for token in re.findall(r"\d+", str(ver_str or "")):
            try:
                parts.append(int(token))
            except Exception:
                pass
        return tuple(parts)

    @classmethod
    def check_pypi_update(cls, timeout: float = 6.0) -> tuple[bool, str, str]:
        """Comprueba silenciosamente en PyPI si existe una versión más reciente de yt-dlp."""
        try:
            curr_ver = str(getattr(yt_dlp.version, "__version__", "") or "").strip()
            req = urllib.request.Request(
                "https://pypi.org/pypi/yt-dlp/json",
                headers={"User-Agent": "MediaPlatform/1.0.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read(2 * 1024 * 1024).decode("utf-8", errors="ignore"))
            latest_ver = str((data.get("info") or {}).get("version") or "").strip()
            if not latest_ver or not curr_ver:
                return False, curr_ver, latest_ver
            if cls._version_tuple(latest_ver) > cls._version_tuple(curr_ver):
                return True, curr_ver, latest_ver
            return False, curr_ver, latest_ver
        except Exception:
            return False, "", ""


class ProcessAndThreadRegistry:
    """Registro centralizado y seguro para hilos (QThread) y subprocesos hijos (FFmpeg / ffprobe)."""
    _lock = threading.Lock()
    _subprocesses: set[subprocess.Popen] = set()
    _threads: set = set()

    @classmethod
    def register_subprocess(cls, proc: subprocess.Popen):
        if proc is not None:
            with cls._lock:
                cls._subprocesses.add(proc)

    @classmethod
    def unregister_subprocess(cls, proc: subprocess.Popen):
        if proc is not None:
            with cls._lock:
                cls._subprocesses.discard(proc)

    @classmethod
    def register_thread(cls, thread_obj):
        if thread_obj is not None:
            with cls._lock:
                cls._threads.add(thread_obj)

    @classmethod
    def unregister_thread(cls, thread_obj):
        if thread_obj is not None:
            with cls._lock:
                cls._threads.discard(thread_obj)

    @classmethod
    def active_subprocesses(cls) -> list[subprocess.Popen]:
        with cls._lock:
            alive = [p for p in cls._subprocesses if p.poll() is None]
            cls._subprocesses = set(alive)
            return list(alive)

    @classmethod
    def active_threads(cls) -> list:
        with cls._lock:
            alive = [t for t in cls._threads if hasattr(t, "isRunning") and t.isRunning()]
            cls._threads = set(alive)
            return list(alive)

    @classmethod
    def terminate_all_subprocesses(cls):
        """Termina de forma limpia (y mata si no responden) todos los subprocesos hijos activos."""
        procs = cls.active_subprocesses()
        for p in procs:
            try:
                if p.poll() is None:
                    p.terminate()
            except Exception:
                pass
        for p in procs:
            try:
                if p.poll() is None:
                    p.wait(timeout=0.8)
            except Exception:
                try:
                    if p.poll() is None:
                        p.kill()
                except Exception:
                    pass
        with cls._lock:
            cls._subprocesses.clear()

    @classmethod
    def shutdown_all(cls, extra_threads=None, wait_ms: int = 1200):
        """Señaliza cancelación en todos los QThreads registrados, termina subprocesos y espera su cierre."""
        threads = list(cls.active_threads())
        if extra_threads:
            for t in extra_threads:
                if t is not None and t not in threads and hasattr(t, "isRunning") and t.isRunning():
                    threads.append(t)

        for t in threads:
            try:
                if hasattr(t, "is_cancelled"):
                    t.is_cancelled = True
                if hasattr(t, "is_paused"):
                    t.is_paused = False
            except Exception:
                pass

        cls.terminate_all_subprocesses()

        for t in threads:
            try:
                if t.isRunning():
                    t.wait(wait_ms)
            except Exception:
                pass


def _bootstrap_updated_engine():
    EngineHotSwapManager.activate_plugins_path()
    engine_file = os.path.join(get_portable_data_dir(), "engine", "yt-dlp")
    if os.path.isfile(engine_file):
        try:
            if engine_file not in sys.path:
                sys.path.append(engine_file)
            importer = zipimport.zipimporter(engine_file)
            mod = importer.load_module("yt_dlp")
            sys.modules["yt_dlp"] = mod
        except Exception:
            pass


_bootstrap_updated_engine()
import yt_dlp
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl, QSize
from PySide6.QtGui import QDesktopServices, QFont, QIcon, QPixmap, QAction, QCloseEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QProgressBar, QStackedWidget, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QTextEdit, QSpinBox, QFrame, QMenu, QAbstractItemView,
    QDialog, QSystemTrayIcon
)


class _YtdlpSilentLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass


from .i18n import I18nManager, detect_system_language, set_language, get_language, tr


class SettingsManager:
    def __init__(self):
        self.app_dir = get_portable_data_dir()
        self.filepath = os.path.join(self.app_dir, "settings.json")
        self.defaults = {
            "download_dir": get_default_download_dir(),
            "language": "auto",
            "simple_mode": True,
            "auto_update_engine": True,
            "dark_mode": True,
            "dark_theme": True,
            "quality": "Mejor Calidad Disponible",
            "container": "MP4",
            "fragments": 4,
            "max_concurrent": 2,
            "allow_playlist": False,
            "speed_limit_kb": 0,
            "proxy": "",
            "cookies_browser": "Ninguno",
            "cookies_file": "",
            "naming_template": "%(title).100s [%(resolution)s] [%(id)s].%(ext)s",
            "auto_organize": False,
            "skip_duplicates": True,
            "overwrite_existing": False,
            "clip_monitor": False,
            "clipboard_monitor": False,
            "privacy_mode": False,
            "minimize_to_tray": False,
            "embed_thumbnail": False,
            "sponsorblock": False,
            "smart_sponsor": False,
            "split_chapters": False,
            "live_from_start": False,
            "loudnorm": False,
            "sub_langs": "Español (España) [es-ES]",
            "ui_preset_name": "Dragon Forge (Obsidiana y Oro)",
            "ui_theme": {}
        }
        self.data = self.load()

    @staticmethod
    def _is_valid_download_dir(path_str: str) -> bool:
        if not path_str:
            return False
        # Rechazar rutas de unidad de Windows (ej. C:\...) cuando se ejecuta en Linux/POSIX
        if os.name != "nt" and re.match(r"^[a-zA-Z]:\\", path_str):
            return False
        return os.path.isdir(path_str) and os.access(path_str, os.W_OK)

    def load(self) -> dict:
        self.filepath = os.path.join(get_portable_data_dir(), "settings.json")
        example_path = os.path.join(get_portable_data_dir(), "settings.example.json")
        base = dict(self.defaults)
        source_file = self.filepath if os.path.isfile(self.filepath) else (example_path if os.path.isfile(example_path) else "")
        if source_file:
            try:
                with open(source_file, "r", encoding="utf-8", errors="replace") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    base.update(loaded)
            except Exception:
                pass

        lang_val = str(base.get("language") or "auto").strip().lower()
        if lang_val in ("", "auto"):
            base["language"] = detect_system_language()
        else:
            base["language"] = I18nManager.normalize_lang(lang_val)
        I18nManager.set_language(base["language"])

        dl_dir = str(base.get("download_dir") or "").strip()
        if not self._is_valid_download_dir(dl_dir):
            base["download_dir"] = get_default_download_dir()
        else:
            base["download_dir"] = os.path.realpath(dl_dir)

        self.data = base
        if not os.path.isfile(self.filepath):
            self.save(base)
        return base

    def save(self, data: dict = None):
        try:
            self.filepath = os.path.join(get_portable_data_dir(), "settings.json")
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            merged = dict(getattr(self, "data", None) or self.load())
            if isinstance(data, dict):
                merged.update(data)
            self.data = merged
            tmp_file = self.filepath + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_file, self.filepath)
        except Exception:
            pass


class SecurityGuard:
    ALLOWED_SCHEMES = {"http", "https"}
    ALLOWED_PROXY_SCHEMES = ("http://", "https://", "socks4://", "socks5://", "socks5h://")
    BLOCKED_HOSTS = {"localhost", "localhost.localdomain", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254"}
    CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")
    WINDOWS_RESERVED_NAMES = {
        "CON", "PRN", "AUX", "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    ALLOWED_MEDIA_EXTS = {
        ".mp4", ".mkv", ".webm", ".mov", ".mp3", ".flac", ".m4a",
        ".opus", ".wav", ".ogg", ".srt", ".vtt", ".ass", ".gif",
        ".jpg", ".jpeg", ".png", ".webp", ".txt"
    }
    DANGEROUS_EXTS = {
        ".exe", ".bat", ".cmd", ".ps1", ".vbs", ".scr", ".msi",
        ".dll", ".com", ".hta", ".jar", ".reg", ".wsf", ".pif", ".sh", ".run"
    }

    @classmethod
    def is_url(cls, text: str) -> bool:
        return str(text or "").strip().lower().startswith(("http://", "https://"))

    @classmethod
    def _is_forbidden_ip(cls, ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        if getattr(ip_obj, "ipv4_mapped", None) is not None:
            ip_obj = ip_obj.ipv4_mapped
        elif getattr(ip_obj, "sixtofour", None) is not None:
            ip_obj = ip_obj.sixtofour
        elif getattr(ip_obj, "teredo", None) is not None:
            for t_ip in ip_obj.teredo:
                if cls._is_forbidden_ip(t_ip):
                    return True

        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
            or not ip_obj.is_global
        ):
            return True

        if ip_obj.version == 4 and ip_obj in cls.CGNAT_NETWORK:
            return True
        return False

    @classmethod
    def _try_parse_ip_literal(cls, host: str):
        """
        Detecta y parsea literales IPv4/IPv6 estándar, IPv4 mapeadas en IPv6 y notaciones
        alternativas enteras (ej. 2130706433), hexadecimales (0x7f000001) u octales (0177.0.0.1).
        Devuelve:
          - objeto IPv4Address / IPv6Address si el host es un literal IP válido,
          - ValueError si el host intenta usar notación IP no estándar/ofuscada o inválida,
          - None si el host es un nombre de dominio convencional.
        """
        clean = host.strip().strip("[]")
        if not clean:
            raise ValueError("Host vacío.")

        # 1. Intentar parseo estándar IPv4 / IPv6
        try:
            return ipaddress.ip_address(clean.split("%")[0])
        except ValueError:
            pass

        # 2. Detectar notación entera, hexadecimal u octal en 1 a 4 segmentos separados por punto
        parts = clean.split(".")
        if 1 <= len(parts) <= 4 and all(
            re.fullmatch(r"(?:0x[0-9a-fA-F]+|0[0-7]+|\d+)", p) for p in parts
        ):
            # Rechazar explícitamente notaciones octales/hexadecimales o de menos de 4 octetos para evitar bypass SSRF
            if len(parts) != 4 or any(
                p.lower().startswith("0x") or (len(p) > 1 and p.startswith("0"))
                for p in parts
            ):
                raise ValueError("Notación IP ofuscada (hexadecimal, octal o entera) bloqueada.")
            try:
                return ipaddress.IPv4Address(clean)
            except Exception as e:
                raise ValueError("Dirección IPv4 no válida.") from e

        return None

    @classmethod
    def validate_url(cls, raw_url: str) -> tuple[bool, str]:
        url = str(raw_url or "").strip()
        if not url:
            return False, "El enlace está vacío."
        if url.startswith("-"):
            return False, "Bloqueado: intento de inyección de argumentos."
        if any(c in url for c in ["\n", "\r", "\x00", ";", "|", "`", "$("]):
            return False, "Bloqueado: caracteres de control no permitidos."

        try:
            parsed = urlparse(url)
        except Exception:
            return False, "Formato de enlace no válido."

        if parsed.scheme.lower() not in cls.ALLOWED_SCHEMES:
            return False, f"Protocolo '{parsed.scheme}' no permitido (solo HTTP/HTTPS)."

        host = (parsed.hostname or "").strip().lower()
        if (
            not host
            or host in cls.BLOCKED_HOSTS
            or host.endswith((".localhost", ".local", ".internal", ".home.arpa"))
        ):
            return False, "Dirección local o privada bloqueada."

        try:
            ip_lit = cls._try_parse_ip_literal(host)
        except ValueError as ip_err:
            return False, f"Bloqueado: {ip_err}"

        if ip_lit is not None:
            if cls._is_forbidden_ip(ip_lit):
                return False, f"Dirección IP privada, loopback o reservada bloqueada ({ip_lit})."
            return True, url

        # Si es un dominio, resolver mediante socket.getaddrinfo y verificar que todas las IPs sean globales
        try:
            port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
            addr_info = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            for _fam, _type, _proto, _canon, sockaddr in addr_info:
                raw_ip = str(sockaddr[0]).split("%")[0]
                resolved_ip = ipaddress.ip_address(raw_ip)
                if cls._is_forbidden_ip(resolved_ip):
                    return False, f"Dominio bloqueado por seguridad: resuelve a IP interna ({resolved_ip})."
        except socket.gaierror:
            # Si no hay conectividad DNS en el entorno actual, permitir solo dominios públicos bien formados
            if "." not in host:
                return False, "Nombre de host interno sin dominio público bloqueado."
        except ValueError:
            return False, "Dirección de red no válida."

        return True, url

    @classmethod
    def validate_proxy(cls, proxy_str: str) -> tuple[bool, str]:
        raw = str(proxy_str or "").strip()
        if not raw:
            return True, ""
        if any(c in raw for c in ("\r", "\n", "\x00")):
            return False, "El proxy contiene caracteres de control no permitidos."
        low = raw.lower()
        if not low.startswith(cls.ALLOWED_PROXY_SCHEMES):
            return False, "Esquema de proxy no permitido (usa http://, https://, socks4://, socks5:// o socks5h://)."
        try:
            parsed = urlparse(raw)
            if not parsed.hostname:
                return False, "El proxy especificado no tiene un host válido."
        except Exception:
            return False, "Formato de proxy no válido."
        return True, raw

    @classmethod
    def sanitize_filename(cls, name: str, default: str = "Archivo") -> str:
        clean = re.sub(r'[\x00-\x1f\x7f\\/*?:"<>|]', "", str(name or "")).strip()
        clean = clean.lstrip("-").strip(". ")
        if not clean or clean in (".", ".."):
            clean = default
        stem = os.path.splitext(clean)[0].strip().upper()
        if stem in cls.WINDOWS_RESERVED_NAMES:
            clean = f"_{clean}"
        return clean[:120]

    @classmethod
    def sanitize_naming_template(cls, template: str) -> str:
        default_tmpl = "%(title).100s [%(resolution)s] [%(id)s].%(ext)s"
        raw = str(template or "").strip()
        if not raw:
            return default_tmpl
        if any(c in raw for c in ("\r", "\n", "\x00", "/", "\\")):
            return default_tmpl
        if ".." in raw or os.path.isabs(raw) or re.match(r"^[a-zA-Z]:", raw):
            return default_tmpl
        return raw

    @classmethod
    def verify_safe_path(cls, filepath: str, base_dir: str) -> tuple[bool, str]:
        if not filepath:
            return False, "Ruta vacía."
        real_base = os.path.realpath(base_dir)
        real_target = os.path.realpath(filepath)

        try:
            common = os.path.commonpath([real_base, real_target])
            is_inside = (common == real_base) if os.name != "nt" else (common.lower() == real_base.lower())
        except ValueError:
            is_inside = False

        if not is_inside:
            return False, "Intento de escritura fuera de la carpeta de destino."

        _, ext = os.path.splitext(real_target.lower())
        if ext in cls.DANGEROUS_EXTS:
            try:
                if os.path.exists(real_target):
                    os.remove(real_target)
            except Exception:
                pass
            return False, f"Archivo bloqueado por extensión peligrosa ({ext})."

        return True, "OK"

    @staticmethod
    def compute_sha256(filepath: str) -> str:
        if not filepath or not os.path.isfile(filepath):
            return "N/A"
        try:
            with open(filepath, "rb") as f:
                if hasattr(hashlib, "file_digest"):
                    return hashlib.file_digest(f, "sha256").hexdigest()
                h = hashlib.sha256()
                for chunk in iter(lambda: f.read(8388608), b""):
                    h.update(chunk)
                return h.hexdigest()
        except Exception:
            return "N/A"

    @classmethod
    def safe_open_file(cls, filepath: str):
        if not filepath or not os.path.exists(filepath):
            return
        _, ext = os.path.splitext(filepath.lower())
        if ext in cls.DANGEROUS_EXTS or ext not in cls.ALLOWED_MEDIA_EXTS:
            QMessageBox.critical(
                None, "Seguridad",
                f"No se permite ejecutar directamente archivos con extensión '{ext}'."
            )
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))

    @staticmethod
    def reveal_in_explorer(filepath: str, fallback_dir: str):
        target = filepath if (filepath and os.path.exists(filepath)) else fallback_dir
        if not target or not os.path.exists(target):
            return
        if os.name == "nt" and os.path.isfile(target):
            subprocess.run(["explorer.exe", f"/select,{os.path.normpath(target)}"], shell=False)
        else:
            folder = os.path.dirname(os.path.abspath(target)) if os.path.isfile(target) else target
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Valida cada salto de redirección HTTP (301/302/307/308) contra SecurityGuard.validate_url."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target_url = urljoin(req.full_url, str(newurl or "").strip())
        ok, reason = SecurityGuard.validate_url(target_url)
        if not ok:
            raise urllib.error.URLError(f"Redirección bloqueada por seguridad ({code}): {reason}")
        return super().redirect_request(req, fp, code, msg, headers, target_url)


class MediaCore:
    def __init__(self):
        self.ffmpeg_path = self._find_binary("ffmpeg")
        self.ffprobe_path = self._find_binary("ffprobe")

    def _find_binary(self, name: str) -> str | None:
        exe = f"{name}.exe" if os.name == "nt" else name
        bundled = get_resource_path(exe)
        if bundled and os.access(bundled, os.X_OK if os.name != "nt" else os.R_OK):
            return bundled

        sys_path = shutil.which(name)
        if sys_path:
            return sys_path

        if os.name == "nt":
            local_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local"))
            winget_link = os.path.join(local_appdata, "Microsoft", "WinGet", "Links", exe)
            if os.path.exists(winget_link):
                return winget_link

            pattern = os.path.join(local_appdata, "Microsoft", "WinGet", "Packages", "*FFmpeg*", "**", exe)
            matches = glob.glob(pattern, recursive=True)
            if matches:
                return matches[0]
        return None

    @staticmethod
    def extract_ffmpeg_error(stderr_text: str) -> str:
        lines = [
            ln.strip() for ln in str(stderr_text or "").splitlines()
            if ln.strip() and not ln.strip().startswith(("ffmpeg version", "built with", "configuration:", "lib"))
        ]
        if not lines:
            return "Error desconocido en subproceso FFmpeg."
        return " | ".join(lines[-3:])[:280]

    def run_ffmpeg_cmd(
        self,
        cmd: list[str],
        cancel_check=None,
        timeout: float | None = None
    ) -> tuple[bool, str, str]:
        """Ejecuta un comando FFmpeg de forma controlable y cancelable, capturando stdout/stderr."""
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            creationflags=creation_flags
        )
        ProcessAndThreadRegistry.register_subprocess(proc)
        start_t = time.monotonic()
        stdout_chunks = []
        stderr_chunks = []
        try:
            while True:
                if cancel_check is not None and cancel_check():
                    proc.terminate()
                    try:
                        proc.wait(timeout=1.5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    raise RuntimeError("CANCELLED_BY_USER")

                if timeout is not None and (time.monotonic() - start_t) > timeout:
                    proc.terminate()
                    try:
                        proc.wait(timeout=1.5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                    return False, "", "Tiempo de espera agotado en FFmpeg."

                try:
                    out, err = proc.communicate(timeout=0.25)
                    if out:
                        stdout_chunks.append(out)
                    if err:
                        stderr_chunks.append(err)
                    break
                except subprocess.TimeoutExpired:
                    continue
        finally:
            ProcessAndThreadRegistry.unregister_subprocess(proc)
            if proc.poll() is None:
                proc.kill()

        full_out = "".join(stdout_chunks)
        full_err = "".join(stderr_chunks)
        return (proc.returncode == 0), full_out, full_err

    def probe_file(self, filepath) -> dict:
        if not self.ffprobe_path or not os.path.isfile(filepath):
            return {}
        cmd = [
            self.ffprobe_path, "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", "--", filepath
        ]
        try:
            ok, out, _ = self.run_ffmpeg_cmd(cmd, timeout=15)
            return json.loads(out) if ok and out else {}
        except Exception:
            return {}

    def get_duration(self, filepath) -> float:
        info = self.probe_file(filepath)
        try:
            return float(info.get("format", {}).get("duration", 0.0))
        except Exception:
            return 0.0

    def _build_process_cmd(self, input_file, output_file, mode, vcodec, target_mb):
        cmd = [self.ffmpeg_path, "-hide_banner", "-y", "-i", input_file]
        if mode == "remux":
            cmd += ["-c", "copy", output_file]
        elif mode == "audio_mp3":
            cmd += ["-vn", "-c:a", "libmp3lame", "-b:a", "320k", output_file]
        elif mode == "loudnorm_audio":
            cmd += ["-vn", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "libmp3lame", "-b:a", "320k", output_file]
        elif mode == "loudnorm_video":
            cmd += ["-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", output_file]
        elif mode == "gif":
            cmd += ["-vf", "fps=12,scale=540:-1:flags=lanczos", output_file]
        elif mode == "compress_size" and target_mb > 0:
            dur = self.get_duration(input_file)
            if dur <= 0:
                dur = 60.0
            total_kbps = int(((target_mb * 0.95) * 8192) / dur)
            audio_kbps = 96 if target_mb <= 10 else 128
            video_kbps = max(150, total_kbps - audio_kbps)
            cmd += [
                "-c:v", vcodec, "-b:v", f"{video_kbps}k",
                "-maxrate", f"{int(video_kbps * 1.15)}k", "-bufsize", f"{video_kbps * 2}k",
                "-c:a", "aac", "-b:a", f"{audio_kbps}k", output_file
            ]
        else:
            preset_args = ["-preset", "fast"] if vcodec == "libx264" else []
            cmd += ["-c:v", vcodec, *preset_args, "-c:a", "aac", "-b:a", "192k", output_file]
        return cmd

    def process_media(self, input_file, output_file, mode="remux", hw_accel="cpu", target_mb=0, cancel_check=None):
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg no está disponible.")

        if mode in ("loudnorm_audio", "loudnorm_video"):
            shutil.copy2(input_file, output_file)
            ok_ln, msg_ln = self.normalize_loudnorm_two_pass(
                output_file, is_audio_only=(mode == "loudnorm_audio"), cancel_check=cancel_check
            )
            if not ok_ln:
                try:
                    if os.path.isfile(output_file):
                        os.remove(output_file)
                except Exception:
                    pass
                raise RuntimeError(msg_ln)
            return

        encoder_map = {
            "nvenc": "h264_nvenc",
            "qsv": "h264_qsv",
            "amf": "h264_amf",
            "cpu": "libx264"
        }
        vcodec = encoder_map.get(hw_accel, "libx264")
        cmd = self._build_process_cmd(input_file, output_file, mode, vcodec, target_mb)
        ok, _, err_txt = self.run_ffmpeg_cmd(cmd, cancel_check=cancel_check)

        # Fallback automático a CPU (libx264) si el codificador por hardware no está disponible
        if not ok and vcodec != "libx264" and mode in ("compress_size", "convert"):
            cmd_cpu = self._build_process_cmd(input_file, output_file, mode, "libx264", target_mb)
            ok, _, err_txt = self.run_ffmpeg_cmd(cmd_cpu, cancel_check=cancel_check)

        if not ok:
            try:
                if os.path.isfile(output_file) and os.path.getsize(output_file) == 0:
                    os.remove(output_file)
            except Exception:
                pass
            raise RuntimeError(f"FFmpeg falló: {self.extract_ffmpeg_error(err_txt)}")

    def normalize_loudnorm_two_pass(self, filepath: str, is_audio_only: bool = False, cancel_check=None) -> tuple[bool, str]:
        if not self.ffmpeg_path or not filepath or not os.path.isfile(filepath):
            return False, "Archivo o FFmpeg no disponible"

        pass1_cmd = [
            self.ffmpeg_path, "-hide_banner", "-nostats", "-i", filepath,
            "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
            "-f", "null", "-"
        ]
        _, _, stderr_txt = self.run_ffmpeg_cmd(pass1_cmd, cancel_check=cancel_check)

        af_filter = "loudnorm=I=-14:TP=-1.5:LRA=11"
        mode_used = "1-pass-fallback"

        json_matches = re.findall(r'\{[^{}]*"input_i"[^{}]*\}', stderr_txt, flags=re.DOTALL)
        if json_matches:
            try:
                stats = json.loads(json_matches[-1])
                in_i = float(stats.get("input_i"))
                in_tp = float(stats.get("input_tp"))
                in_lra = float(stats.get("input_lra"))
                in_th = float(stats.get("input_thresh"))
                t_off = float(stats.get("target_offset", 0.0))
                if all(math.isfinite(v) for v in (in_i, in_tp, in_lra, in_th, t_off)):
                    af_filter = (
                        f"loudnorm=I=-14:TP=-1.5:LRA=11:"
                        f"measured_I={in_i:.2f}:measured_TP={in_tp:.2f}:measured_LRA={in_lra:.2f}:"
                        f"measured_thresh={in_th:.2f}:offset={t_off:.2f}:linear=true"
                    )
                    mode_used = "2-pass-linear"
            except Exception:
                pass

        base_f, ext_f = os.path.splitext(filepath)
        tmp_out = f"{base_f}.ln2p{ext_f}"

        if is_audio_only:
            ext_low = ext_f.lower()
            if ext_low == ".mp3":
                pass2_cmd = [
                    self.ffmpeg_path, "-hide_banner", "-y", "-i", filepath,
                    "-map", "0:a:0", "-map", "0:v?", "-c:v", "copy",
                    "-af", af_filter, "-c:a", "libmp3lame", "-b:a", "192k", "-id3v2_version", "3", tmp_out
                ]
            elif ext_low in (".m4a", ".aac"):
                pass2_cmd = [
                    self.ffmpeg_path, "-hide_banner", "-y", "-i", filepath,
                    "-map", "0:a:0", "-map", "0:v?", "-c:v", "copy",
                    "-af", af_filter, "-c:a", "aac", "-b:a", "192k", tmp_out
                ]
            else:
                pass2_cmd = [self.ffmpeg_path, "-hide_banner", "-y", "-i", filepath, "-af", af_filter, tmp_out]
        else:
            pass2_cmd = [
                self.ffmpeg_path, "-hide_banner", "-y", "-i", filepath,
                "-map", "0", "-c:v", "copy", "-c:s", "copy",
                "-af", af_filter, "-c:a", "aac", "-b:a", "192k", tmp_out
            ]

        try:
            ok2, _, err2 = self.run_ffmpeg_cmd(pass2_cmd, cancel_check=cancel_check)
            if ok2 and os.path.isfile(tmp_out) and os.path.getsize(tmp_out) > 0:
                os.replace(tmp_out, filepath)
                return True, mode_used
            if os.path.isfile(tmp_out):
                os.remove(tmp_out)
            return False, f"Fallo al normalizar audio: {self.extract_ffmpeg_error(err2)}"
        except Exception:
            if os.path.isfile(tmp_out):
                try:
                    os.remove(tmp_out)
                except Exception:
                    pass
            raise


class DatabaseManager:
    def __init__(self, privacy_mode: bool = False, db_path: str = None):
        self.privacy_mode = privacy_mode
        self.app_dir = get_portable_data_dir()
        self.db_path = db_path if db_path is not None else os.path.join(self.app_dir, "media_library.db")
        self._mem_conn = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem_conn.execute("PRAGMA temp_store=MEMORY;")
        self._init_db()

    def _connect(self):
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA temp_store=MEMORY;")
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT,
                    title TEXT,
                    channel TEXT,
                    platform TEXT,
                    resolution TEXT,
                    fps TEXT,
                    hdr TEXT,
                    vcodec TEXT,
                    acodec TEXT,
                    filepath TEXT,
                    filesize INTEGER,
                    file_hash TEXT,
                    downloaded_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_title ON downloads(title);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_video_id ON downloads(video_id);")

    def find_existing_download(self, video_id: str, platform: str = "") -> dict | None:
        """Comprueba si un video_id ya fue descargado y su archivo sigue existiendo en disco."""
        vid = str(video_id or "").strip()
        if not vid:
            return None
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            if platform:
                rows = conn.execute(
                    "SELECT * FROM downloads WHERE video_id = ? AND lower(platform) = lower(?) ORDER BY id DESC",
                    (vid, str(platform))
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM downloads WHERE video_id = ? ORDER BY id DESC",
                    (vid,)
                ).fetchall()
            for r in rows:
                d = dict(r)
                fpath = d.get("filepath") or ""
                if fpath and os.path.isfile(fpath) and os.path.getsize(fpath) > 0:
                    return d
        return None

    def add_record(self, meta):
        if self.privacy_mode or not isinstance(meta, dict) or meta.get("_already_in_db"):
            return
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO downloads (
                    video_id, title, channel, platform, resolution, fps, hdr,
                    vcodec, acodec, filepath, filesize, file_hash, downloaded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meta.get("video_id", ""),
                meta.get("title", "Desconocido"),
                meta.get("channel", "Desconocido"),
                meta.get("platform", "Web"),
                meta.get("resolution", "N/A"),
                str(meta.get("fps", "N/A")),
                meta.get("hdr", "SDR"),
                meta.get("vcodec", "N/A"),
                meta.get("acodec", "N/A"),
                meta.get("filepath", ""),
                meta.get("filesize", 0),
                meta.get("file_hash", "N/A"),
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ))

    def search_library(self, query=""):
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            if query:
                escaped = str(query).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                q = f"%{escaped}%"
                rows = conn.execute(
                    "SELECT * FROM downloads WHERE title LIKE ? ESCAPE '\\' OR channel LIKE ? ESCAPE '\\' OR platform LIKE ? ESCAPE '\\' ORDER BY id DESC LIMIT 500",
                    (q, q, q)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM downloads ORDER BY id DESC LIMIT 500").fetchall()
            return [dict(r) for r in rows]

    def delete_record(self, record_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM downloads WHERE id = ?", (record_id,))

    def clear_history(self):
        with self._connect() as conn:
            conn.execute("DELETE FROM downloads")


class DiagnosticEngine:
    @staticmethod
    def analyze_error(error_str):
        err = str(error_str or "").lower()
        if "ffmpeg is not installed" in err or "ffprobe" in err or "ffmpeg no está disponible" in err:
            return (
                "FFmpeg no está accesible para procesar o unir vídeo y audio.",
                "Comprueba el estado de FFmpeg en la pestaña 'Sistema y Seguridad'."
            )
        if "ffmpeg falló" in err or "fallo al normalizar audio" in err:
            return (
                "FFmpeg encontró un error durante el posprocesado o conversión.",
                f"Detalle de FFmpeg: {str(error_str)[:240]}"
            )
        if any(k in err for k in ("cookie", "dpapi", "keyring", "secretstorage", "kwallet")) and any(
            k in err for k in ("permission denied", "locked", "failed to decrypt", "could not find", "sign in", "403")
        ):
            return (
                "No se pudieron leer las cookies del navegador (bloqueado o cifrado por el sistema).",
                "Usa un archivo 'cookies.txt' exportado en 'Ajustes y Red', usa Firefox o cierra el navegador."
            )
        if "429" in err or "too many requests" in err:
            return (
                "El servidor ha limitado temporalmente las peticiones (Error HTTP 429).",
                "Configura un archivo 'cookies.txt' o selecciona Firefox en 'Ajustes y Red -> Cookies'."
            )
        if "sign in" in err or "private" in err or "403" in err or "not a bot" in err:
            return (
                "El vídeo requiere iniciar sesión, verificación anti-bot, es privado o tiene restricción de edad.",
                "Selecciona un navegador con sesión iniciada o importa un archivo 'cookies.txt' en 'Ajustes y Red'."
            )
        if "no space left on device" in err or "disk full" in err:
            return (
                "No queda espacio libre suficiente en el disco de destino.",
                "Libera espacio o cambia la carpeta de descargas."
            )
        if "certificate_verify_failed" in err or "ssl" in err:
            return (
                "Error de verificación de certificado SSL en la conexión.",
                "Comprueba tu conexión de red, proxy o fecha/hora del sistema."
            )
        return (
            "Fallo técnico durante la extracción o descarga.",
            f"Detalle exacto: {str(error_str)[:220]}"
        )


class SubtitleResolver:
    PRESETS = [
        "Español (España) [es-ES]",
        "Inglés (EE. UU.) [en-US]",
        "Inglés (Inglaterra / UK) [en-GB]",
        "Español (España) + Inglés (EE. UU.)",
        "Español (España) + Inglés (Inglaterra / UK)",
        "Los 3 (ES-España + EN-EE.UU. + EN-Inglaterra)"
    ]

    CHAINS = {
        "es_es": ["es-es", "es-orig", "es", "es-419", "es-mx"],
        "en_us": ["en-us", "en-orig", "en", "en-gb"],
        "en_gb": ["en-gb", "en-orig", "en", "en-us"],
    }

    @classmethod
    def get_target_groups(cls, preset_text: str) -> list[list[str]]:
        preset_text = str(preset_text or "")
        if "Los 3" in preset_text or ("Inglaterra" in preset_text and "EE.UU." in preset_text):
            return [cls.CHAINS["es_es"], cls.CHAINS["en_us"], cls.CHAINS["en_gb"]]
        if ("Espa" in preset_text) and ("EE. UU." in preset_text):
            return [cls.CHAINS["es_es"], cls.CHAINS["en_us"]]
        if ("Espa" in preset_text) and ("Inglaterra" in preset_text):
            return [cls.CHAINS["es_es"], cls.CHAINS["en_gb"]]
        if "EE. UU." in preset_text:
            return [cls.CHAINS["en_us"]]
        if "Inglaterra" in preset_text:
            return [cls.CHAINS["en_gb"]]
        return [cls.CHAINS["es_es"]]

    @classmethod
    def resolve_tracks(cls, info: dict, preset_text: str) -> tuple[list[str], bool, bool]:
        info = info if isinstance(info, dict) else {}
        manual_subs = info.get("subtitles") or {}
        auto_subs = info.get("automatic_captions") or {}
        manual_map = {str(k).lower(): str(k) for k in manual_subs.keys()} if isinstance(manual_subs, dict) else {}
        auto_map = {str(k).lower(): str(k) for k in auto_subs.keys()} if isinstance(auto_subs, dict) else {}

        chosen = []
        need_manual = False
        need_auto = False

        for chain in cls.get_target_groups(preset_text):
            found_key = None
            is_auto = False
            exact_code = chain[0]

            if exact_code in manual_map and manual_map[exact_code] not in chosen:
                found_key = manual_map[exact_code]
            elif exact_code in auto_map and auto_map[exact_code] not in chosen:
                found_key = auto_map[exact_code]
                is_auto = True

            if not found_key:
                for candidate in chain:
                    if candidate in manual_map and manual_map[candidate] not in chosen:
                        found_key = manual_map[candidate]
                        break
            if not found_key:
                prefix = exact_code.split("-")[0]
                for k_low, k_real in manual_map.items():
                    if k_low.startswith(prefix + "-") and k_real not in chosen:
                        found_key = k_real
                        break

            if not found_key:
                for candidate in chain:
                    if candidate in auto_map and auto_map[candidate] not in chosen:
                        found_key = auto_map[candidate]
                        is_auto = True
                        break
            if not found_key:
                prefix = exact_code.split("-")[0]
                for k_low, k_real in auto_map.items():
                    if k_low.startswith(prefix + "-") and k_real not in chosen:
                        found_key = k_real
                        is_auto = True
                        break

            if found_key and found_key not in chosen:
                chosen.append(found_key)
                if is_auto:
                    need_auto = True
                else:
                    need_manual = True

        return chosen, need_manual, need_auto


class SurfaceCard(QFrame):
    _forge_overlay_painter = None

    def __init__(self, title="", subtitle=""):
        super().__init__()
        self.setObjectName("SurfaceCard")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(18, 15, 18, 15)
        self.main_layout.setSpacing(10)
        self.lbl_title = None
        self.lbl_subtitle = None

        if title:
            header_box = QVBoxLayout()
            header_box.setSpacing(2)
            self.lbl_title = QLabel(title)
            self.lbl_title.setObjectName("SectionHeader")
            header_box.addWidget(self.lbl_title)
            if subtitle:
                self.lbl_subtitle = QLabel(subtitle)
                self.lbl_subtitle.setObjectName("SectionSub")
                header_box.addWidget(self.lbl_subtitle)
            self.main_layout.addLayout(header_box)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter_fn = SurfaceCard._forge_overlay_painter
        if painter_fn is not None:
            painter_fn(self, event)

    def set_texts(self, title: str = None, subtitle: str = None):
        if title is not None and self.lbl_title is not None:
            self.lbl_title.setText(title)
        if subtitle is not None and self.lbl_subtitle is not None:
            self.lbl_subtitle.setText(subtitle)


class MetricTile(QFrame):
    def __init__(self, label_text, initial_value="—"):
        super().__init__()
        self.setObjectName("MetricTile")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        self.lbl_title = QLabel(label_text)
        self.lbl_title.setObjectName("TileLabel")
        self.lbl_val = QLabel(initial_value)
        self.lbl_val.setObjectName("TileValue")
        self.lbl_val.setWordWrap(True)

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_val)

    def set_value(self, text):
        self.lbl_val.setText(str(text))


class CookieHelper:
    @classmethod
    def get_configured_cookies_file(cls) -> str:
        try:
            sm_path = os.path.join(get_portable_data_dir(), "settings.json")
            if os.path.isfile(sm_path):
                with open(sm_path, "r", encoding="utf-8", errors="ignore") as f:
                    s_cfg = json.load(f)
                cfile = str(s_cfg.get("cookies_file") or "").strip()
                if cfile and os.path.isfile(cfile):
                    return cfile
        except Exception:
            pass
        return ""

    @classmethod
    def apply_cookies(cls, ydl_opts: dict, cookies_browser: str = "Ninguno", cookies_file: str = ""):
        cfile = str(cookies_file or "").strip() or cls.get_configured_cookies_file()
        if cfile and os.path.isfile(cfile):
            ydl_opts["cookiefile"] = cfile
            ydl_opts.pop("cookiesfrombrowser", None)
            return "file"
        cbrowser = str(cookies_browser or "Ninguno").strip()
        if cbrowser and cbrowser.lower() != "ninguno":
            ydl_opts["cookiesfrombrowser"] = (cbrowser.lower(),)
            ydl_opts.pop("cookiefile", None)
            return "browser"
        ydl_opts.pop("cookiefile", None)
        ydl_opts.pop("cookiesfrombrowser", None)
        return "none"


_OrigYoutubeDL = yt_dlp.YoutubeDL


class SafeYoutubeDL(_OrigYoutubeDL):
    COOKIE_ERR_TOKENS = (
        "cookie", "permission denied", "locked", "dpapi",
        "keyring", "secretstorage", "kwallet", "failed to decrypt"
    )

    def __init__(self, params=None, auto_init=True):
        opts = dict(params or {})
        opts.setdefault("socket_timeout", 15)
        opts.setdefault("source_address", "0.0.0.0")
        opts.setdefault("nocheckcertificate", False)
        opts.setdefault("logger", _YtdlpSilentLogger())
        opts.setdefault("color", "no_color")
        opts["cachedir"] = False

        cfile = str(opts.get("cookiefile") or "").strip() or CookieHelper.get_configured_cookies_file()
        if cfile and os.path.isfile(cfile):
            opts["cookiefile"] = cfile
            opts.pop("cookiesfrombrowser", None)

        self._cookie_fallback_error = ""
        self._raw_init_opts = dict(opts)
        try:
            super().__init__(opts, auto_init=auto_init)
        except Exception as e:
            self._cookie_fallback_error = str(e)
            opts.pop("cookiesfrombrowser", None)
            opts.pop("cookiefile", None)
            self._raw_init_opts = dict(opts)
            super().__init__(opts, auto_init=auto_init)

    def extract_info(self, url, *args, **kwargs):
        try:
            return super().extract_info(url, *args, **kwargs)
        except Exception as e:
            err_str = str(e)
            err_low = err_str.lower()

            # 1. Fallback controlado ante fallo de certificado SSL:
            #    eliminar obligatoriamente cookies y cabeceras Cookie para impedir filtración por MitM
            if "certificate_verify_failed" in err_low and not self.params.get("nocheckcertificate"):
                self.params["nocheckcertificate"] = True
                self.params.pop("cookiesfrombrowser", None)
                self.params.pop("cookiefile", None)
                try:
                    self.cookiejar.clear()
                except Exception:
                    pass
                hdrs = self.params.get("http_headers")
                if isinstance(hdrs, dict):
                    for hk in [k for k in list(hdrs.keys()) if str(k).lower() == "cookie"]:
                        hdrs.pop(hk, None)
                return super().extract_info(url, *args, **kwargs)

            # 2. Fallback controlado ante bloqueo/cifrado de cookies del navegador
            if any(tok in err_low for tok in self.COOKIE_ERR_TOKENS) and (
                "cookiesfrombrowser" in self.params or "cookiefile" in self.params
            ):
                self._cookie_fallback_error = err_str
                self.params.pop("cookiesfrombrowser", None)
                self.params.pop("cookiefile", None)
                try:
                    self.cookiejar.clear()
                except Exception:
                    pass
                try:
                    return super().extract_info(url, *args, **kwargs)
                except Exception as retry_err:
                    raise RuntimeError(
                        f"Fallo de cookies ({err_str}) seguido de error de acceso: {retry_err}"
                    ) from retry_err
            raise


yt_dlp.YoutubeDL = SafeYoutubeDL


class SmartSponsorDetector:
    """
    Detector local de segmentos patrocinados (SmartSponsorDetector).
    Actúa como respaldo automático cuando SponsorBlock devuelve 0 segmentos
    o como modo de detección inteligente por transcripción (VTT/SRT o faster-whisper).
    """

    # Patrones ancla de alta confianza (ES + EN) — expresiones lineales sin cuantificadores anidados ambiguos
    ANCHOR_PATTERNS = [
        (r"\b(?:este\s+v[ií]deo\s+est[aá]\s+)?patrocinado\s+por\b", "patrocinado por"),
        (r"\bv[ií]deo\s+patrocinado\s+por\b", "vídeo patrocinado por"),
        (r"\bpatrocina\s+este\s+(?:v[ií]deo|canal|episodio)\b", "patrocina este vídeo"),
        (r"\bgracias\s+a\s+[^\n.,;:!?]{1,50}\s+por\s+(?:patrocinar|apoyar|hacer\s+posible)\b", "gracias a ... por patrocinar"),
        (r"\b(?:el\s+)?patrocinador\s+de\s+(?:hoy|este\s+v[ií]deo|este\s+episodio)\b", "patrocinador de hoy"),
        (r"\bnuestro\s+patrocinador\b", "nuestro patrocinador"),
        (r"\ben\s+colaboraci[oó]n\s+con\b", "en colaboración con"),
        (r"\bespacio\s+patrocinado\b", "espacio patrocinado"),
        (r"\bsegmento\s+patrocinado\b", "segmento patrocinado"),
        (r"\bmensaje\s+de\s+nuestro\s+patrocinador\b", "mensaje de nuestro patrocinador"),
        (r"\b(?:this\s+video\s+is\s+|today'?s\s+video\s+is\s+)?sponsored\s+by\b", "sponsored by"),
        (r"\bthanks?\s+(?:so\s+much\s+)?to\s+[^\n.,;:!?]{1,50}\s+for\s+sponsoring\b", "thanks to ... for sponsoring"),
        (r"\bthank\s+you\s+to\s+[^\n.,;:!?]{1,50}\s+for\s+sponsoring\b", "thank you to ... for sponsoring"),
        (r"\bbrought\s+to\s+you\s+by\b", "brought to you by"),
        (r"\btoday'?s\s+sponsor\b", "today's sponsor"),
        (r"\bsponsor\s+of\s+today'?s\s+video\b", "sponsor of today's video"),
        (r"\ba\s+word\s+from\s+our\s+sponsor\b", "a word from our sponsor"),
    ]

    # Patrones promocionales / Call-To-Action (ES + EN)
    CTA_PATTERNS = [
        (r"\bc[oó]digo\s+de\s+descuento\b", "código de descuento"),
        (r"\bc[oó]digo\s+promocional\b", "código promocional"),
        (r"\b(?:usa|usando|con|aplicar?)\s+(?:el|mi|nuestro)\s+c[oó]digo\b", "usa el código"),
        (r"\b(?:enlaces?|links?)\s+(?:que\s+(?:te\s+|os\s+|les\s+)?dejo\s+)?(?:en|de)\s+la\s+descripci[oó]n\b", "enlace en la descripción"),
        (r"\bprimer\s+(?:enlace|link)\s+de\s+la\s+descripci[oó]n\b", "primer enlace de la descripción"),
        (r"\b(?:enlaces?|links?)\s+aqu[ií]\s+abajo\b", "enlace aquí abajo"),
        (r"\b(?:entra|haz\s+clic|pincha)\s+en\s+el\s+(?:enlace|link)\b", "haz clic en el enlace"),
        (r"\bescanea\s+el\s+(?:c[oó]digo\s+)?qr\b", "escanea el código QR"),
        (r"\bc[oó]digo\s+qr\s+en\s+pantalla\b", "código QR en pantalla"),
        (r"\bdescuento\s+exclusivo\b", "descuento exclusivo"),
        (r"\b(?:\d+\s*%\s*de\s+descuento|por\s+ciento\s+de\s+descuento)\b", "% de descuento"),
        (r"\bprueba\s+gratuita\b|\bprueba\s+gratis\b", "prueba gratis"),
        (r"\bpromo\s+code\b", "promo code"),
        (r"\bdiscount\s+code\b", "discount code"),
        (r"\bcoupon\s+code\b", "coupon code"),
        (r"\b(?:use|using|with)\s+(?:my\s+|our\s+|the\s+)?code\b", "use code"),
        (r"\blink\s+in\s+the\s+description\b", "link in the description"),
        (r"\bfirst\s+link\s+in\s+the\s+description\b", "first link in the description"),
        (r"\bclick\s+the\s+link\s+(?:below|in\s+the\s+description)\b", "click the link below"),
        (r"\bscan\s+the\s+qr\s+code\b", "scan the QR code"),
        (r"\bqr\s+code\s+on\s+(?:the\s+)?screen\b", "QR code on screen"),
        (r"\bfree\s+trial\b", "free trial"),
        (r"\b\d+\s*%\s*off\b|\bpercent\s+off\b", "% off"),
        (r"\bexclusive\s+(?:discount|offer|deal)\b", "exclusive discount"),
    ]

    # Frases de apertura suave justo antes del bloque patrocinado
    LEAD_IN_PATTERNS = [
        r"\bpero\s+antes\b",
        r"\bantes\s+de\s+(?:empezar|comenzar|continuar|seguir|ir|pasar|nada)\b",
        r"\b(?:dejadme|d[eé]jame|perm[ií]teme)\s+que\s+(?:os\s+|te\s+|les\s+)?hable\b",
        r"\bhablando\s+de\b",
        r"\bpor\s+cierto\b",
        r"\bbut\s+first\b",
        r"\bbefore\s+we\s+(?:start|begin|continue|get\s+into)\b",
        r"\bspeaking\s+of\b",
    ]

    # Frases de cierre / retorno al contenido principal
    CLOSING_PATTERNS = [
        r"\bvolvamos\s+(?:al|con\s+el)\s+v[ií]deo\b",
        r"\bseguimos\s+con\s+el\s+v[ií]deo\b",
        r"\bcontinuamos\s+con\s+el\s+v[ií]deo\b",
        r"\bdicho\s+esto\b",
        r"\bahora\s+s[ií]\s+(?:empezamos|vamos|comenzamos)\b",
        r"\bvamos\s+(?:con\s+el|al)\s+v[ií]deo\b",
        r"\bempecemos\s+con\s+el\s+v[ií]deo\b",
        r"\bmuchas\s+gracias\s+a\s+[^\n.,;:!?]{1,45}\s+por\b",
        r"\bback\s+to\s+the\s+video\b",
        r"\blet'?s\s+get\s+back\s+to\b",
        r"\bnow\s+back\s+to\b",
        r"\bwithout\s+further\s+ado\b",
        r"\bon\s+with\s+the\s+video\b",
        r"\bthanks\s+again\s+to\b",
    ]

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        seconds = max(0.0, float(seconds or 0.0))
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = seconds % 60
        if hrs > 0:
            return f"{hrs:02d}:{mins:02d}:{secs:05.2f}"
        return f"{mins:02d}:{secs:05.2f}"

    @staticmethod
    def _parse_time_str(ts: str) -> float:
        ts = ts.strip().replace(",", ".")
        parts = ts.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(parts[0])

    @classmethod
    def parse_vtt_srt_text(cls, raw_text: str) -> list[dict]:
        """
        Parsea subtítulos VTT/SRT extrayendo intervalos [start, end] y texto limpio,
        desduplicando líneas solapadas típicas de los subtítulos automáticos de YouTube.
        """
        if not raw_text:
            return []

        text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        blocks = re.split(r"\n\s*\n", text)
        ts_re = re.compile(
            r"((?:\d{1,2}:)?\d{2}:\d{2}[.,]\d{1,3})\s*-->\s*((?:\d{1,2}:)?\d{2}:\d{2}[.,]\d{1,3})"
        )

        raw_cues = []
        for block in blocks:
            lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
            if not lines:
                continue
            first_up = lines[0].upper()
            if first_up.startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
                continue

            ts_idx = -1
            ts_match = None
            for idx, ln in enumerate(lines):
                m = ts_re.search(ln)
                if m:
                    ts_idx = idx
                    ts_match = m
                    break
            if ts_match is None:
                continue

            try:
                start_s = cls._parse_time_str(ts_match.group(1))
                end_s = cls._parse_time_str(ts_match.group(2))
            except Exception:
                continue

            if end_s <= start_s:
                continue

            content_lines = []
            for ln in lines[ts_idx + 1:]:
                clean_ln = re.sub(r"<[^>]+>", "", ln)
                clean_ln = (
                    clean_ln.replace("&nbsp;", " ")
                    .replace("&amp;", "&")
                    .replace("&quot;", '"')
                    .replace("&#39;", "'")
                    .replace("&lt;", "<")
                    .replace("&gt;", ">")
                )
                clean_ln = re.sub(r"\s+", " ", clean_ln).strip()
                if clean_ln and not re.match(r"^\[.*\]$", clean_ln):
                    if not content_lines or content_lines[-1] != clean_ln:
                        content_lines.append(clean_ln)

            if not content_lines:
                continue

            raw_cues.append({
                "start": start_s,
                "end": end_s,
                "lines": content_lines,
                "text": " ".join(content_lines)
            })

        # Desduplicar subtítulos progresivos/auto-generados (rolling captions)
        cleaned_cues = []
        prev_lines = []
        for cue in raw_cues:
            curr_lines = cue["lines"]
            # Filtrar líneas que ya estaban al final del cue anterior
            new_lines = [ln for ln in curr_lines if ln not in prev_lines]
            if not new_lines:
                # Si es repetición exacta (micro-cue de transición), extender el final del cue previo
                if cleaned_cues and cue["end"] > cleaned_cues[-1]["end"] and (cue["end"] - cue["start"]) < 0.5:
                    cleaned_cues[-1]["end"] = cue["end"]
                prev_lines = curr_lines
                continue

            new_text = " ".join(new_lines).strip()
            if cleaned_cues and cleaned_cues[-1]["text"].lower() == new_text.lower():
                cleaned_cues[-1]["end"] = max(cleaned_cues[-1]["end"], cue["end"])
            else:
                cleaned_cues.append({
                    "start": round(cue["start"], 3),
                    "end": round(cue["end"], 3),
                    "text": new_text
                })
            prev_lines = curr_lines

        return cleaned_cues

    MAX_SUBTITLE_BYTES = 15 * 1024 * 1024

    @classmethod
    def parse_subtitle_file(cls, filepath: str) -> list[dict]:
        if not filepath or not os.path.isfile(filepath):
            return []
        try:
            if os.path.getsize(filepath) > cls.MAX_SUBTITLE_BYTES:
                return []
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                return cls.parse_vtt_srt_text(f.read(cls.MAX_SUBTITLE_BYTES))
        except Exception:
            return []

    @classmethod
    def fetch_cues_with_ytdlp(
        cls,
        url: str,
        cookies_browser: str = "Ninguno",
        cookies_file: str = "",
        ffmpeg_path: str = None,
        proxy: str = "",
        log_fn=None
    ) -> tuple[list[dict], dict]:
        """
        Descarga subtítulos manuales o automáticos en formato VTT/SRT con skip_download=True
        en una pasada rápida de yt-dlp y devuelve (cues, info_meta).
        """
        temp_root = os.path.join(get_portable_data_dir(), "temp")
        os.makedirs(temp_root, exist_ok=True)
        tmp_dir = tempfile.mkdtemp(prefix="smartsponsor_", dir=temp_root)

        try:
            probe_opts = {
                "skip_download": True,
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "nocheckcertificate": False,
                "socket_timeout": 15,
                "logger": _YtdlpSilentLogger()
            }
            ok_px, clean_px = SecurityGuard.validate_proxy(proxy)
            if ok_px and clean_px:
                probe_opts["proxy"] = clean_px
            CookieHelper.apply_cookies(probe_opts, cookies_browser, cookies_file)

            with yt_dlp.YoutubeDL(probe_opts) as ydl:
                info = ydl.extract_info(url, download=False) or {}
                if isinstance(info.get("entries"), list) and info["entries"]:
                    info = info["entries"][0] or {}

            manual_subs = info.get("subtitles") or {}
            auto_subs = info.get("automatic_captions") or {}

            # Seleccionar mejor idioma disponible (priorizando español e inglés, luego idioma original)
            orig_lang = str(info.get("language") or "").strip()
            pref_prefixes = ["es-ES", "es-MX", "es-419", "es", "en-US", "en-GB", "en"]
            if orig_lang and orig_lang not in pref_prefixes:
                pref_prefixes.insert(0, orig_lang)

            selected_lang = None
            use_auto = False

            # 1. Buscar en manuales (excluyendo live_chat)
            manual_keys = [k for k in manual_subs.keys() if k != "live_chat"]
            for pref in pref_prefixes:
                for k in manual_keys:
                    if k.lower() == pref.lower() or k.lower().startswith(pref.lower() + "-"):
                        selected_lang = k
                        use_auto = False
                        break
                if selected_lang:
                    break

            # 2. Buscar en automáticos si no hay manual en idioma preferido
            if not selected_lang:
                auto_keys = [k for k in auto_subs.keys() if k != "live_chat"]
                for pref in pref_prefixes:
                    for k in auto_keys:
                        if k.lower() == pref.lower() or k.lower().startswith(pref.lower() + "-"):
                            selected_lang = k
                            use_auto = True
                            break
                    if selected_lang:
                        break

            # 3. Cualquier idioma disponible
            if not selected_lang:
                if manual_keys:
                    selected_lang = manual_keys[0]
                    use_auto = False
                elif auto_keys:
                    selected_lang = auto_keys[0]
                    use_auto = True

            if not selected_lang:
                if callable(log_fn):
                    log_fn("El vídeo no dispone de subtítulos manuales ni automáticos en el servidor.")
                return [], info

            dl_opts = {
                "skip_download": True,
                "writesubtitles": not use_auto,
                "writeautomaticsub": use_auto,
                "subtitleslangs": [selected_lang],
                "subtitlesformat": "vtt/srt/best",
                "outtmpl": os.path.join(tmp_dir, "sub.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "socket_timeout": 15,
                "logger": _YtdlpSilentLogger()
            }
            if ffmpeg_path:
                dl_opts["ffmpeg_location"] = ffmpeg_path
            if ok_px and clean_px:
                dl_opts["proxy"] = clean_px
            CookieHelper.apply_cookies(dl_opts, cookies_browser, cookies_file)

            with yt_dlp.YoutubeDL(dl_opts) as ydl:
                ydl.download([url])

            sub_files = (
                glob.glob(os.path.join(tmp_dir, "*.vtt"))
                + glob.glob(os.path.join(tmp_dir, "*.srt"))
                + glob.glob(os.path.join(tmp_dir, "sub.*"))
            )
            if not sub_files:
                return [], info

            cues = cls.parse_subtitle_file(sub_files[0])
            info["_selected_sub_lang"] = selected_lang
            info["_selected_sub_auto"] = use_auto
            return cues, info
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @classmethod
    def is_faster_whisper_available(cls) -> bool:
        try:
            import importlib.util
            return importlib.util.find_spec("faster_whisper") is not None
        except Exception:
            return False

    @classmethod
    def transcribe_with_faster_whisper(cls, media_path: str, log_fn=None) -> list[dict]:
        """
        Respaldo local con faster-whisper (modelo 'base') cuando el vídeo no tiene subtítulos.
        Si no está instalado, registra un aviso limpio y devuelve [] sin fallar.
        """
        if not media_path or not os.path.isfile(media_path):
            return []

        if not cls.is_faster_whisper_available():
            if callable(log_fn):
                log_fn(
                    "[SmartSponsor] Aviso: El vídeo no tiene subtítulos y 'faster-whisper' no está instalado. "
                    "Se omite el análisis por voz y continúa la descarga normal."
                )
            return []

        try:
            from faster_whisper import WhisperModel
            if callable(log_fn):
                log_fn("[SmartSponsor] Transcribiendo audio local con faster-whisper (modelo 'base')...")
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, _info = model.transcribe(media_path, beam_size=3, vad_filter=True)
            cues = []
            for seg in segments:
                txt = str(seg.text or "").strip()
                if txt:
                    cues.append({
                        "start": round(float(seg.start), 3),
                        "end": round(float(seg.end), 3),
                        "text": txt
                    })
            return cues
        except Exception as e:
            if callable(log_fn):
                log_fn(f"[SmartSponsor] Aviso: No se pudo completar faster-whisper ({e}). Continuando sin recorte.")
            return []

    @classmethod
    def detect_sponsor_segments(
        cls,
        cues: list[dict],
        chapters: list[dict] = None,
        duration: float = 0.0,
        min_window: float = 30.0,
        max_window: float = 90.0
    ) -> list[dict]:
        """
        Analiza los cues de subtítulos buscando indicadores de patrocinio en español e inglés,
        agrupa líneas contiguas en una ventana de 30 a 90s hasta el cierre del bloque o cambio
        de capítulo y devuelve la lista de intervalos detectados.
        """
        if not cues:
            return []

        compiled_anchors = [(re.compile(pat, re.IGNORECASE), label) for pat, label in cls.ANCHOR_PATTERNS]
        compiled_ctas = [(re.compile(pat, re.IGNORECASE), label) for pat, label in cls.CTA_PATTERNS]
        compiled_leads = [re.compile(pat, re.IGNORECASE) for pat in cls.LEAD_IN_PATTERNS]
        compiled_closings = [re.compile(pat, re.IGNORECASE) for pat in cls.CLOSING_PATTERNS]

        hits = []
        n = len(cues)

        for i in range(n):
            cue = cues[i]
            # Evaluar cue individual y ventana de 2 cues consecutivos para frases partidas entre líneas
            single_text = cue["text"]
            pair_text = single_text
            pair_end = cue["end"]
            if i + 1 < n and (cues[i + 1]["start"] - cue["end"]) <= 2.5:
                pair_text = f"{single_text} {cues[i + 1]['text']}"
                pair_end = cues[i + 1]["end"]

            matched_anchors = []
            matched_ctas = []

            for rx, label in compiled_anchors:
                m = rx.search(single_text) or rx.search(pair_text)
                if m:
                    matched_anchors.append((label, m.group(0).strip()))

            for rx, label in compiled_ctas:
                m = rx.search(single_text) or rx.search(pair_text)
                if m:
                    matched_ctas.append((label, m.group(0).strip()))

            if matched_anchors or matched_ctas:
                hits.append({
                    "cue_idx": i,
                    "start": cue["start"],
                    "end": cue["end"],
                    "pair_end": pair_end,
                    "text": single_text,
                    "anchors": matched_anchors,
                    "ctas": matched_ctas
                })

        if not hits:
            return []

        # Agrupar hits cercanos dentro de la ventana máxima (hasta 90s entre el inicio del bloque y el último hit)
        clusters = []
        for h in hits:
            if not clusters:
                clusters.append([h])
            else:
                prev_cluster = clusters[-1]
                gap_from_last = h["start"] - prev_cluster[-1]["end"]
                span_from_first = h["end"] - prev_cluster[0]["start"]
                if gap_from_last <= 55.0 and span_from_first <= (max_window + 15.0):
                    prev_cluster.append(h)
                else:
                    clusters.append([h])

        detected_segments = []
        chapter_bounds = []
        if isinstance(chapters, list):
            for ch in chapters:
                if isinstance(ch, dict) and ch.get("start_time") is not None and ch.get("end_time") is not None:
                    chapter_bounds.append({
                        "start": float(ch["start_time"]),
                        "end": float(ch["end_time"]),
                        "title": str(ch.get("title") or "")
                    })

        for cluster in clusters:
            all_anchors = []
            all_ctas = []
            phrase_details = []

            for h in cluster:
                for lbl, exact in h["anchors"]:
                    all_anchors.append(lbl)
                    entry = f"{lbl} («{exact}» @ {cls.format_timestamp(h['start'])})"
                    if entry not in phrase_details:
                        phrase_details.append(entry)
                for lbl, exact in h["ctas"]:
                    all_ctas.append(lbl)
                    entry = f"{lbl} («{exact}» @ {cls.format_timestamp(h['start'])})"
                    if entry not in phrase_details:
                        phrase_details.append(entry)

            unique_cta_types = set(all_ctas)
            # Confirmar bloque: al menos 1 frase ancla explícita O >=2 indicadores CTA distintos en el mismo bloque
            has_strong_cta = any(
                k in unique_cta_types
                for k in ("código de descuento", "código promocional", "usa el código", "promo code", "discount code", "use code")
            )
            if not all_anchors and len(unique_cta_types) < 2 and not has_strong_cta:
                continue

            first_idx = cluster[0]["cue_idx"]
            last_idx = cluster[-1]["cue_idx"]

            # 1. Determinar inicio del bloque (buscar lead-in hasta 10s antes del primer hit)
            start_idx = first_idx
            for back_i in range(max(0, first_idx - 4), first_idx):
                if (cues[first_idx]["start"] - cues[back_i]["start"]) <= 12.0:
                    if any(rx.search(cues[back_i]["text"]) for rx in compiled_leads):
                        start_idx = back_i
                        break

            block_start = cues[start_idx]["start"]

            # Ajustar a inicio de capítulo si coincide cerca (±12s)
            for ch in chapter_bounds:
                if abs(ch["start"] - block_start) <= 12.0:
                    block_start = ch["start"]
                    break

            # 2. Determinar fin del bloque (agrupando líneas contiguas dentro de ventana 30s-90s
            #    hasta frase de cierre, cambio de capítulo o final del CTA)
            end_idx = last_idx
            found_closing = False

            # Buscar frase de cierre explícita dentro de la ventana [block_start + 15, block_start + max_window + 10]
            for fwd_i in range(first_idx, n):
                c_start = cues[fwd_i]["start"]
                c_end = cues[fwd_i]["end"]
                if c_start - block_start > (max_window + 10.0):
                    break
                if (c_end - block_start) >= 15.0 and any(rx.search(cues[fwd_i]["text"]) for rx in compiled_closings):
                    end_idx = fwd_i
                    found_closing = True
                    break

            block_end = cues[end_idx]["end"]

            # Verificar si hay un límite de capítulo dentro de la ventana [30s, 90s]
            snapped_chapter_end = None
            for ch in chapter_bounds:
                if (block_start + min_window - 5.0) <= ch["end"] <= (block_start + max_window + 10.0):
                    snapped_chapter_end = ch["end"]
                    break

            if snapped_chapter_end is not None:
                block_end = snapped_chapter_end
            elif not found_closing:
                # Extender por líneas contiguas tras el último indicador hasta alcanzar ventana mínima (30s)
                # o hasta encontrar una pausa natural / límite de ventana (30-90s)
                curr_i = end_idx
                while curr_i + 1 < n:
                    nxt = cues[curr_i + 1]
                    curr_dur = nxt["end"] - block_start
                    gap = nxt["start"] - cues[curr_i]["end"]

                    if curr_dur > max_window:
                        break
                    # Si aún no llegamos a 30s, seguir agrupando líneas contiguas del discurso promocional
                    if (cues[curr_i]["end"] - block_start) < min_window:
                        curr_i += 1
                        block_end = cues[curr_i]["end"]
                        if any(rx.search(cues[curr_i]["text"]) for rx in compiled_closings):
                            break
                    else:
                        # Ya superamos los 30s: si la frase del último CTA quedó abierta (sin punto final),
                        # avanzar únicamente 1 cue si cierra la oración (ej. "...aquí en pantalla.")
                        if curr_i == last_idx and not cues[curr_i]["text"].rstrip().endswith((".", "!", "?")) and gap <= 1.0:
                            curr_i += 1
                            block_end = cues[curr_i]["end"]
                        break

                # Garantizar ventana entre 30s y 90s si el vídeo tiene duración suficiente
                raw_dur = block_end - block_start
                if raw_dur < min_window:
                    target_end = block_start + min_window
                    if duration > 0:
                        target_end = min(duration, target_end)
                    elif cues:
                        target_end = min(cues[-1]["end"], target_end)
                    block_end = max(block_end, target_end)
                elif raw_dur > max_window:
                    block_end = block_start + max_window

            # Recopilar texto del tramo detectado
            block_cues = [c for c in cues if c["end"] > block_start and c["start"] < block_end]
            snippet_text = " ".join(c["text"] for c in block_cues)
            if len(snippet_text) > 360:
                snippet_text = snippet_text[:357] + "..."

            matched_labels = []
            for lbl in all_anchors + all_ctas:
                if lbl not in matched_labels:
                    matched_labels.append(lbl)

            detected_segments.append({
                "start": round(block_start, 2),
                "end": round(block_end, 2),
                "duration": round(block_end - block_start, 2),
                "start_str": cls.format_timestamp(block_start),
                "end_str": cls.format_timestamp(block_end),
                "phrases": matched_labels,
                "phrase_details": phrase_details,
                "snippet": snippet_text,
                "cues": block_cues
            })

        # Fusionar segmentos si se solapan
        merged = []
        for seg in sorted(detected_segments, key=lambda x: x["start"]):
            if not merged or seg["start"] > (merged[-1]["end"] + 3.0):
                merged.append(seg)
            else:
                prev = merged[-1]
                prev["end"] = round(max(prev["end"], seg["end"]), 2)
                prev["duration"] = round(prev["end"] - prev["start"], 2)
                prev["end_str"] = cls.format_timestamp(prev["end"])
                for p in seg["phrases"]:
                    if p not in prev["phrases"]:
                        prev["phrases"].append(p)
                for pd in seg["phrase_details"]:
                    if pd not in prev["phrase_details"]:
                        prev["phrase_details"].append(pd)

        return merged

    @classmethod
    def cut_segments_ffmpeg(
        cls,
        filepath: str,
        segments: list[dict],
        ffmpeg_path: str = None,
        total_duration: float = 0.0,
        cancel_check=None
    ) -> tuple[bool, str]:
        """
        Recorta los intervalos [start, end] de patrocinio usando el demuxer concat de FFmpeg
        con -c copy para no perder calidad ni recodificar.
        """
        if not filepath or not os.path.isfile(filepath) or not segments:
            return False, "Sin segmentos que recortar o archivo inexistente."

        if any(c in str(filepath) for c in ("\n", "\r", "\x00")):
            return False, "Ruta de archivo rechazada por seguridad: contiene saltos de línea o bytes nulos."

        mc = MediaCore()
        if ffmpeg_path:
            mc.ffmpeg_path = ffmpeg_path
        if not mc.ffmpeg_path:
            return False, "FFmpeg no está disponible para recortar el segmento patrocinado."

        if total_duration <= 0:
            try:
                probe = mc.probe_file(filepath)
                total_duration = float(probe.get("format", {}).get("duration", 0.0) or 0.0)
            except Exception:
                total_duration = 0.0

        # Calcular los tramos de contenido a conservar (complemento de segments)
        sorted_cuts = sorted(segments, key=lambda s: float(s["start"]))
        keep_ranges = []
        cursor = 0.0

        for cut in sorted_cuts:
            c_start = max(0.0, float(cut["start"]))
            c_end = max(c_start, float(cut["end"]))
            if c_start - cursor >= 0.5:
                keep_ranges.append((round(cursor, 3), round(c_start, 3)))
            cursor = max(cursor, c_end)

        if total_duration <= 0 or (total_duration - cursor) >= 0.5:
            keep_ranges.append((round(cursor, 3), round(total_duration, 3) if total_duration > 0 else None))

        if not keep_ranges:
            return False, "Los segmentos detectados cubren la totalidad del archivo; recorte abortado por seguridad."

        base_f, ext_f = os.path.splitext(filepath)
        concat_list_path = f"{base_f}.smartsponsor_concat.txt"
        out_tmp_path = f"{base_f}.smartsponsor{ext_f}"

        try:
            # Escapar comillas simples para directiva file de ffconcat
            safe_in = filepath.replace("'", "'\\''")
            lines = ["ffconcat version 1.0"]
            for k_start, k_end in keep_ranges:
                lines.append(f"file '{safe_in}'")
                if k_start > 0:
                    lines.append(f"inpoint {k_start:.3f}")
                if k_end is not None and k_end > k_start:
                    lines.append(f"outpoint {k_end:.3f}")

            with open(concat_list_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")

            cmd = [
                mc.ffmpeg_path, "-hide_banner", "-y",
                "-f", "concat", "-safe", "0",
                "-i", concat_list_path,
                "-c", "copy"
            ]
            if ext_f.lower() in (".mp4", ".m4a", ".mov"):
                cmd.extend(["-movflags", "+faststart"])
            cmd.append(out_tmp_path)

            ok, _out, err = mc.run_ffmpeg_cmd(cmd, cancel_check=cancel_check)
            if ok and os.path.isfile(out_tmp_path) and os.path.getsize(out_tmp_path) > 0:
                os.replace(out_tmp_path, filepath)
                return True, f"Recortados {len(sorted_cuts)} tramo(s) patrocinado(s) con FFmpeg (-c copy)."
            return False, f"Error en FFmpeg concat: {err[-300:] if err else 'Salida vacía'}"
        finally:
            for tmp_p in (concat_list_path, out_tmp_path):
                try:
                    if os.path.isfile(tmp_p):
                        os.remove(tmp_p)
                except Exception:
                    pass

    @classmethod
    def analyze_url_subtitles(
        cls,
        url: str,
        cookies_browser: str = "Ninguno",
        cookies_file: str = "",
        ffmpeg_path: str = None,
        proxy: str = ""
    ) -> dict:
        """
        Descarga únicamente los subtítulos de una URL y ejecuta el análisis completo de intervalos.
        """
        logs = []
        cues, info = cls.fetch_cues_with_ytdlp(
            url,
            cookies_browser=cookies_browser,
            cookies_file=cookies_file,
            ffmpeg_path=ffmpeg_path,
            proxy=proxy,
            log_fn=logs.append
        )
        duration = float(info.get("duration") or 0.0)
        chapters = info.get("chapters") or []
        segments = cls.detect_sponsor_segments(cues, chapters=chapters, duration=duration)
        return {
            "video_id": info.get("id", ""),
            "title": info.get("title", ""),
            "duration": duration,
            "sub_lang": info.get("_selected_sub_lang", ""),
            "sub_auto": info.get("_selected_sub_auto", False),
            "cues_count": len(cues),
            "segments": segments,
            "logs": logs
        }


__all__ = [k for k in list(globals().keys()) if not k.startswith("__")]
