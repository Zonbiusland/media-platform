# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
import re
import string
import pytest

from mpp.i18n import I18nManager, detect_system_language, set_language, get_language, tr, _resolve_locales_dir
from mpp.core import SubtitleResolver, SettingsManager


class TestI18nCatalogsAndParity:
    def test_en_and_es_json_have_exact_same_keys_non_empty_and_valid_placeholders(self):
        loc_dir = _resolve_locales_dir()
        en_path = os.path.join(loc_dir, "en.json")
        es_path = os.path.join(loc_dir, "es.json")

        assert os.path.isfile(en_path), "Falta locales/en.json"
        assert os.path.isfile(es_path), "Falta locales/es.json"

        with open(en_path, "r", encoding="utf-8") as f_en:
            en_data = json.load(f_en)
        with open(es_path, "r", encoding="utf-8") as f_es:
            es_data = json.load(f_es)

        assert isinstance(en_data, dict) and len(en_data) > 0
        assert isinstance(es_data, dict) and len(es_data) > 0

        en_keys = set(en_data.keys())
        es_keys = set(es_data.keys())
        missing_in_es = en_keys - es_keys
        missing_in_en = es_keys - en_keys
        assert not missing_in_es, f"Claves presentes en en.json pero ausentes en es.json: {missing_in_es}"
        assert not missing_in_en, f"Claves presentes en es.json pero ausentes en en.json: {missing_in_en}"

        formatter = string.Formatter()
        for key in sorted(en_keys):
            val_en = en_data[key]
            val_es = es_data[key]
            assert isinstance(val_en, str) and val_en.strip() != "", f"Cadena vacía en en.json para '{key}'"
            assert isinstance(val_es, str) and val_es.strip() != "", f"Cadena vacía en es.json para '{key}'"

            # Verificar que la sintaxis de formato Python ({var}) sea válida y coincida entre ambos idiomas
            fields_en = {
                field_name.split(".")[0].split("[")[0]
                for _, field_name, _, _ in formatter.parse(val_en)
                if field_name is not None
            }
            fields_es = {
                field_name.split(".")[0].split("[")[0]
                for _, field_name, _, _ in formatter.parse(val_es)
                if field_name is not None
            }
            assert fields_en == fields_es, (
                f"Los marcadores de formato de '{key}' no coinciden: en={fields_en} vs es={fields_es}"
            )

    def test_detect_system_language_defaults_to_en_outside_spanish(self):
        assert detect_system_language("es_ES") == "es"
        assert detect_system_language("es-MX") == "es"
        assert detect_system_language("en_US") == "en"
        assert detect_system_language("fr_FR") == "en"
        assert detect_system_language("de_DE") == "en"
        assert detect_system_language("ja_JP") == "en"

    def test_i18n_external_json_catalogs_and_tr(self):
        I18nManager.reload_catalogs()

        set_language("es")
        assert get_language() == "es"
        assert tr("mode.simple") == "Modo Simple"
        assert tr("mode.advanced") == "Modo Avanzado"
        assert tr("action.download") == "Descargar"
        assert "2026.03.01" in tr("update.available", version="2026.03.01")

        set_language("en")
        assert get_language() == "en"
        assert tr("mode.simple") == "Simple Mode"
        assert tr("mode.advanced") == "Advanced Mode"
        assert tr("action.download") == "Download"
        assert "2026.03.01" in tr("update.available", version="2026.03.01")

        assert tr("clave.inexistente", default="Fallback OK") == "Fallback OK"
        set_language("fr-FR")
        assert get_language() == "en"

    def test_safe_defaults_in_settings_manager(self):
        sm = SettingsManager()
        assert sm.defaults["simple_mode"] is True
        assert sm.defaults["auto_update_engine"] is True
        assert sm.defaults["fragments"] == 4
        assert sm.defaults["max_concurrent"] == 2
        assert sm.defaults["allow_playlist"] is False
        assert sm.defaults["sponsorblock"] is False
        assert sm.defaults["smart_sponsor"] is False
        assert sm.defaults["loudnorm"] is False

    def test_subtitle_resolver_presets_and_track_chains(self):
        info = {
            "subtitles": {
                "es-ES": [{"ext": "vtt"}],
                "en-GB": [{"ext": "vtt"}],
            },
            "automatic_captions": {
                "en-US": [{"ext": "vtt"}],
            },
        }

        chosen_es, need_man_es, need_auto_es = SubtitleResolver.resolve_tracks(
            info, "Español (España) [es-ES]"
        )
        assert chosen_es == ["es-ES"]
        assert need_man_es is True
        assert need_auto_es is False

        chosen_all, need_man_all, need_auto_all = SubtitleResolver.resolve_tracks(
            info, "Los 3 (ES-España + EN-EE.UU. + EN-Inglaterra)"
        )
        assert chosen_all == ["es-ES", "en-US", "en-GB"]
        assert need_man_all is True
        assert need_auto_all is True
