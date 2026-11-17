# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import io
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
import zipfile
import pytest

import mpp.core as core_mod
import mpp.workers as workers_mod
from mpp.core import EngineHotSwapManager, SettingsManager
from mpp.workers import DownloadWorker, WebSnifferWorker


def _make_fake_ytdlp_wheel(version_str: str) -> tuple[bytes, str]:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "yt_dlp/__init__.py",
            f"from . import version\n__version__ = version.__version__\nclass YoutubeDL:\n    def __init__(self, *a, **kw): pass\n",
        )
        zf.writestr("yt_dlp/version.py", f"__version__ = '{version_str}'\n")
    raw = buf.getvalue()
    return raw, hashlib.sha256(raw).hexdigest()


class _FakeHTTPResp:
    def __init__(self, payload: bytes):
        self._buf = io.BytesIO(payload)

    def read(self, n: int = -1) -> bytes:
        return self._buf.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestEngineHotSwapAndRollback:
    @pytest.fixture
    def isolated_plugins_root(self, tmp_path, monkeypatch):
        portable_dir = tmp_path / "portable_data"
        portable_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(core_mod, "get_portable_data_dir", lambda: str(portable_dir))
        orig_sys_path = list(sys.path)
        orig_core_ytdlp = core_mod.yt_dlp
        orig_workers_ytdlp = workers_mod.yt_dlp
        orig_mods = {k: v for k, v in sys.modules.items() if k == "yt_dlp" or k.startswith("yt_dlp.")}

        yield portable_dir

        # Restaurar estado original de sys.modules, sys.path y referencias yt_dlp
        for k in list(sys.modules.keys()):
            if k == "yt_dlp" or k.startswith("yt_dlp."):
                sys.modules.pop(k, None)
        sys.modules.update(orig_mods)
        sys.path[:] = orig_sys_path
        core_mod.yt_dlp = orig_core_ytdlp
        workers_mod.yt_dlp = orig_workers_ytdlp
        EngineHotSwapManager.APP_DIR = core_mod.PORTABLE_DATA_DIR
        EngineHotSwapManager.PLUGINS_DIR = os.path.join(core_mod.PORTABLE_DATA_DIR, "plugins")

    def test_activate_plugins_path_prioritizes_portable_plugins_over_bundled_ytdlp(self, isolated_plugins_root):
        plugins_dir = isolated_plugins_root / "plugins" / "yt_dlp"
        plugins_dir.mkdir(parents=True)
        (plugins_dir / "__init__.py").write_text(
            "from . import version\n__version__ = version.__version__\n",
            encoding="utf-8",
        )
        (plugins_dir / "version.py").write_text("__version__ = '2099.01.01-plugin'\n", encoding="utf-8")

        # También simular archivo os.py malicioso en plugins/ para confirmar que stdlib NO es secuestrada
        (isolated_plugins_root / "plugins" / "os.py").write_text("raise RuntimeError('stdlib hijacked')\n", encoding="utf-8")

        EngineHotSwapManager.activate_plugins_path()

        assert sys.modules["yt_dlp"].version.__version__ == "2099.01.01-plugin"
        assert core_mod.yt_dlp.version.__version__ == "2099.01.01-plugin"
        # sys.path debe mantener plugins al final (no en índice 0)
        assert sys.path[0] != str(isolated_plugins_root / "plugins")

    def test_safe_update_verifies_sha256_creates_backup_and_supports_rollback(self, isolated_plugins_root, monkeypatch):
        whl_v1, sha_v1 = _make_fake_ytdlp_wheel("2099.01.01")
        whl_v2, sha_v2 = _make_fake_ytdlp_wheel("2099.02.02")

        def make_urlopen(version_str, wheel_url, sha_hex, whl_bytes):
            meta_json = json.dumps({
                "info": {"version": version_str},
                "urls": [{
                    "packagetype": "bdist_wheel",
                    "filename": f"yt_dlp-{version_str}-py3-none-any.whl",
                    "url": wheel_url,
                    "digests": {"sha256": sha_hex},
                }],
            }).encode("utf-8")

            def _fake_open(req, timeout=15):
                url = req.full_url if hasattr(req, "full_url") else str(req)
                if "pypi.org" in url:
                    return _FakeHTTPResp(meta_json)
                return _FakeHTTPResp(whl_bytes)

            return _fake_open

        # 1. Rechazar dominio no confiable
        monkeypatch.setattr(
            urllib.request, "urlopen",
            make_urlopen("2099.01.01", "https://evil.example.com/yt_dlp.whl", sha_v1, whl_v1)
        )
        ok_host, msg_host = EngineHotSwapManager.update_yt_dlp_plugin()
        assert ok_host is False
        assert "no autorizado" in msg_host.lower()

        # 2. Rechazar hash SHA-256 manipulado
        monkeypatch.setattr(
            urllib.request, "urlopen",
            make_urlopen("2099.01.01", "https://files.pythonhosted.org/packages/yt_dlp.whl", "0" * 64, whl_v1)
        )
        ok_sha, msg_sha = EngineHotSwapManager.update_yt_dlp_plugin()
        assert ok_sha is False
        assert "sha-256" in msg_sha.lower()

        # 3. Actualizar correctamente a v1 (2099.01.01)
        monkeypatch.setattr(
            urllib.request, "urlopen",
            make_urlopen("2099.01.01", "https://files.pythonhosted.org/packages/yt_dlp-v1.whl", sha_v1, whl_v1)
        )
        ok1, _ = EngineHotSwapManager.update_yt_dlp_plugin()
        assert ok1 is True
        assert sys.modules["yt_dlp"].version.__version__ == "2099.01.01"

        # 4. Actualizar a v2 (2099.02.02) creando respaldo yt_dlp.bak de v1
        monkeypatch.setattr(
            urllib.request, "urlopen",
            make_urlopen("2099.02.02", "https://files.pythonhosted.org/packages/yt_dlp-v2.whl", sha_v2, whl_v2)
        )
        ok2, _ = EngineHotSwapManager.update_yt_dlp_plugin()
        assert ok2 is True
        assert sys.modules["yt_dlp"].version.__version__ == "2099.02.02"
        assert EngineHotSwapManager.has_backup_plugin() is True

        # 5. Rollback debe restaurar v1 (2099.01.01) desde yt_dlp.bak
        ok_rb, msg_rb = EngineHotSwapManager.rollback_yt_dlp_plugin()
        assert ok_rb is True
        assert "2099.01.01" in msg_rb
        assert sys.modules["yt_dlp"].version.__version__ == "2099.01.01"
        assert EngineHotSwapManager.has_backup_plugin() is False

        # 6. Segundo rollback sin backup elimina plugin externo y vuelve al motor nativo integrado
        ok_rb2, _ = EngineHotSwapManager.rollback_yt_dlp_plugin()
        assert ok_rb2 is True
        assert EngineHotSwapManager.has_external_plugin() is False
        assert sys.modules["yt_dlp"].version.__version__ != "2099.01.01"


class TestStrictTLSAndDownloadAutoRetry:
    def test_web_sniffer_does_not_degrade_tls_on_certificate_error(self, monkeypatch):
        class _FailOpener:
            def open(self, req, timeout=12):
                raise urllib.error.URLError(ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED"))

        unverified_called = {"flag": False}

        def _forbid_unverified(*a, **kw):
            unverified_called["flag"] = True
            raise AssertionError("No debe invocarse ssl._create_unverified_context()")

        monkeypatch.setattr(ssl, "_create_unverified_context", _forbid_unverified)
        monkeypatch.setattr(urllib.request, "build_opener", lambda *a, **kw: _FailOpener())

        with pytest.raises(urllib.error.URLError):
            WebSnifferWorker._fetch_html("https://93.184.216.34/", {"User-Agent": "Test"})
        assert unverified_called["flag"] is False

    def test_download_worker_retries_once_after_hotswap_on_extractor_error(self, tmp_path, monkeypatch):
        cfg = {
            "base_dir": str(tmp_path),
            "quality": "Mejor Calidad Disponible",
            "container": "MP4",
            "fragments": 4,
            "allow_playlist": False,
            "subtitles": False,
            "sub_langs": "Español (España) [es-ES]",
            "embed_subs": False,
            "trim_enabled": False,
            "trim_start": "00:00:00",
            "trim_end": "00:05:00",
            "embed_thumbnail": False,
            "sponsorblock": False,
            "smart_sponsor": False,
            "split_chapters": False,
            "live_from_start": False,
            "loudnorm": False,
            "naming_template": "%(title)s.%(ext)s",
            "auto_organize": False,
            "skip_duplicates": True,
            "speed_limit_kb": 0,
            "proxy": "",
            "cookies_browser": "Ninguno",
            "cookies_file": "",
            "privacy_mode": True,
            "auto_update_engine": True,
        }

        out_media = tmp_path / "demo.mp4"
        out_media.write_bytes(b"mp4data")

        attempts = {"extract": 0, "update": 0}

        class _FakeYDL:
            def __init__(self, opts):
                self.opts = opts

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def extract_info(self, url, download=True):
                attempts["extract"] += 1
                if attempts["extract"] == 1:
                    raise RuntimeError("HTTP Error 403: Forbidden (nsig extraction failed)")
                return {
                    "id": "demo123",
                    "title": "Demo OK",
                    "uploader": "Canal",
                    "extractor_key": "Youtube",
                    "height": 1080,
                    "filepath": str(out_media),
                }

        monkeypatch.setattr(workers_mod.yt_dlp, "YoutubeDL", _FakeYDL)
        monkeypatch.setattr(
            EngineHotSwapManager,
            "update_yt_dlp_plugin",
            classmethod(lambda cls: (attempts.__setitem__("update", attempts["update"] + 1) or (True, "OK v2"))),
        )

        results = []
        worker = DownloadWorker("task-1", "https://93.184.216.34/watch?v=demo123", cfg, None)
        worker.finished_signal.connect(lambda tid, ok, msg, meta: results.append((tid, ok, msg, meta)))
        worker.run()

        assert attempts["update"] == 1
        assert attempts["extract"] == 2
        assert len(results) == 1
        assert results[0][1] is True
        assert worker._get_worker_db() is worker._get_worker_db()

    def test_already_downloaded_detection_and_force_overwrite_flag(self, tmp_path, monkeypatch):
        from mpp.i18n import set_language, tr

        out_media = tmp_path / "existing.mp4"
        out_media.write_bytes(b"existing-video")

        base_cfg = {
            "base_dir": str(tmp_path),
            "quality": "Mejor Calidad Disponible",
            "container": "MP4",
            "fragments": 4,
            "allow_playlist": False,
            "subtitles": False,
            "sub_langs": "Español (España) [es-ES]",
            "embed_subs": False,
            "trim_enabled": False,
            "trim_start": "00:00:00",
            "trim_end": "00:05:00",
            "embed_thumbnail": False,
            "sponsorblock": False,
            "smart_sponsor": False,
            "split_chapters": False,
            "live_from_start": False,
            "loudnorm": False,
            "naming_template": "%(title)s.%(ext)s",
            "auto_organize": False,
            "skip_duplicates": True,
            "overwrite_existing": False,
            "speed_limit_kb": 0,
            "proxy": "",
            "cookies_browser": "Ninguno",
            "cookies_file": "",
            "privacy_mode": True,
            "auto_update_engine": False,
        }

        seen_opts = []

        class _FakeAlreadyYDL:
            def __init__(self, opts):
                self.opts = opts
                seen_opts.append(dict(opts))

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def extract_info(self, url, download=True):
                if not self.opts.get("overwrites"):
                    self.opts["logger"].debug(f"[download] {out_media} has already been downloaded")
                return {
                    "id": "exist123",
                    "title": "Existing Video",
                    "uploader": "Channel",
                    "extractor_key": "Youtube",
                    "height": 1080,
                    "filepath": str(out_media),
                }

        monkeypatch.setattr(workers_mod.yt_dlp, "YoutubeDL", _FakeAlreadyYDL)

        prev_lang = set_language("es")
        try:
            assert DownloadWorker.build_ytdlp_cli_args(base_cfg) == []
            res_skip = []
            w_skip = DownloadWorker("task-skip", "https://93.184.216.34/watch?v=exist123", base_cfg, None)
            w_skip.finished_signal.connect(lambda tid, ok, msg, meta: res_skip.append((tid, ok, msg, meta)))
            w_skip.run()

            assert seen_opts[-1]["overwrites"] is False
            assert res_skip[0][1] is True
            assert res_skip[0][2] == tr("status.already_downloaded") == "Ya descargado (omitido)"
            assert res_skip[0][3]["already_downloaded"] is True

            set_language("en")
            res_en = []
            w_skip_en = DownloadWorker("task-skip-en", "https://93.184.216.34/watch?v=exist123", base_cfg, None)
            w_skip_en.finished_signal.connect(lambda tid, ok, msg, meta: res_en.append((tid, ok, msg, meta)))
            w_skip_en.run()
            assert res_en[0][2] == "Already downloaded (skipped)"
            assert res_en[0][3]["already_downloaded"] is True

            force_cfg = dict(base_cfg, overwrite_existing=True)
            assert DownloadWorker.build_ytdlp_cli_args(force_cfg) == ["--force-overwrites"]
            res_force = []
            w_force = DownloadWorker("task-force", "https://93.184.216.34/watch?v=exist123", force_cfg, None)
            w_force.finished_signal.connect(lambda tid, ok, msg, meta: res_force.append((tid, ok, msg, meta)))
            w_force.run()

            assert seen_opts[-1]["overwrites"] is True
            assert "match_filter" not in seen_opts[-1]
            assert res_force[0][3]["already_downloaded"] is False
        finally:
            set_language(prev_lang)
