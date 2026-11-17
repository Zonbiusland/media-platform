# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Media Platform (Studio Master v1.0.0) — Gestor de Internacionalización (GPLv3+)
# Este archivo es software libre distribuido bajo la licencia GNU GPL v3.0 o posterior.
import json
import locale
import os
import sys
from PySide6.QtCore import QLocale


def _resolve_locales_dir() -> str:
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "locales"))
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    candidates.extend([
        os.path.join(root, "locales"),
        os.path.join(here, "locales"),
    ])
    for path in candidates:
        if os.path.isdir(path):
            return path
    return os.path.join(root, "locales")


def detect_system_language(locale_name: str = None) -> str:
    """
    Detecta el idioma del sistema operativo usando QLocale.system().name().
    Devuelve 'es' si empieza por 'es', y 'en' (inglés) por defecto para el resto del mundo.
    """
    raw = str(locale_name or "").strip()
    if not raw:
        try:
            raw = str(QLocale.system().name() or "").strip()
        except Exception:
            raw = ""
    if not raw:
        try:
            loc = locale.getlocale()[0] or ""
            raw = str(loc)
        except Exception:
            raw = ""
    if raw.lower().startswith("es"):
        return "es"
    return "en"


class I18nManager:
    """Sistema ligero de internacionalización basado en archivos JSON externos (locales/en.json y locales/es.json)."""
    SUPPORTED_LANGUAGES = ("en", "es")
    LANGUAGE_LABELS = {
        "en": "English (en)",
        "es": "Español (es)",
    }
    _catalogs: dict[str, dict[str, str]] = {}
    _current_lang: str = ""

    @classmethod
    def _ensure_loaded(cls):
        if cls._catalogs:
            return
        loc_dir = _resolve_locales_dir()
        for code in cls.SUPPORTED_LANGUAGES:
            fpath = os.path.join(loc_dir, f"{code}.json")
            data = {}
            if os.path.isfile(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        loaded = json.load(f)
                    if isinstance(loaded, dict):
                        data = {str(k): str(v) for k, v in loaded.items()}
                except Exception:
                    data = {}
            cls._catalogs[code] = data

    @classmethod
    def reload_catalogs(cls):
        cls._catalogs.clear()
        cls._ensure_loaded()

    @classmethod
    def normalize_lang(cls, lang_code: str) -> str:
        raw = str(lang_code or "").strip().lower()
        if not raw or raw == "auto":
            return detect_system_language()
        if raw.startswith("es") or "español" in raw:
            return "es"
        if raw.startswith("en") or "english" in raw:
            return "en"
        return "en"

    @classmethod
    def set_language(cls, lang_code: str) -> str:
        cls._ensure_loaded()
        cls._current_lang = cls.normalize_lang(lang_code)
        return cls._current_lang

    @classmethod
    def get_language(cls) -> str:
        cls._ensure_loaded()
        if not cls._current_lang:
            cls._current_lang = detect_system_language()
        return cls._current_lang

    @classmethod
    def tr(cls, key: str, lang: str = None, default: str = None, **kwargs) -> str:
        cls._ensure_loaded()
        target_lang = cls.normalize_lang(lang) if lang else cls.get_language()
        catalog = cls._catalogs.get(target_lang) or {}
        text = catalog.get(key)
        if text is None:
            fallback_cat = cls._catalogs.get("en") or cls._catalogs.get("es") or {}
            text = fallback_cat.get(key)
        if text is None:
            text = default if default is not None else key
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text


def set_language(lang_code: str) -> str:
    return I18nManager.set_language(lang_code)


def get_language() -> str:
    return I18nManager.get_language()


def tr(key: str, default: str = None, **kwargs) -> str:
    return I18nManager.tr(key, default=default, **kwargs)


__all__ = [
    "I18nManager",
    "detect_system_language",
    "set_language",
    "get_language",
    "tr",
]
