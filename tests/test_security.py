# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
import urllib.request
import zipfile
import pytest

from mpp.core import SecurityGuard, SafeRedirectHandler, EngineHotSwapManager


class TestSecurityGuardURLs:
    @pytest.mark.parametrize(
        "malicious_url",
        [
            "file:///etc/passwd",
            "file://C:/Windows/System32/cmd.exe",
            "ftp://93.184.216.34/pub/file.mp4",
            "gopher://127.0.0.1:6379/_INFO",
            "javascript:alert(1)",
            "http://127.0.0.1/admin",
            "http://127.0.0.53:8080/internal",
            "http://localhost/video.mp4",
            "http://[::1]:8000/stream.m3u8",
            "http://0.0.0.0/test",
            "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
            "http://[fe80::1]/router",
            "http://10.0.0.1/private.mp4",
            "http://172.16.5.4/secret.mkv",
            "http://192.168.1.254/config",
            "http://100.64.10.1/cgnat",
            "http://2130706433/decimal-loopback",
            "http://0x7f000001/hex-loopback",
            "http://0177.0.0.1/octal-loopback",
            "http://[::ffff:127.0.0.1]/mapped-loopback",
            "http://[::ffff:169.254.169.254]/mapped-metadata",
            "https://93.184.216.34/video\r\nX-Injected: true",
        ],
    )
    def test_blocks_malicious_and_internal_urls(self, malicious_url):
        ok, msg = SecurityGuard.validate_url(malicious_url)
        assert ok is False, f"Debió bloquearse la URL maliciosa: {malicious_url} ({msg})"

    def test_allows_public_ip_https_url(self):
        # 93.184.216.34 es la IP pública histórica de example.com (globalmente enrutable)
        ok, clean = SecurityGuard.validate_url("https://93.184.216.34/media/video.mp4")
        assert ok is True
        assert clean == "https://93.184.216.34/media/video.mp4"

    def test_safe_redirect_handler_blocks_local_redirects(self):
        handler = SafeRedirectHandler()
        req = urllib.request.Request("https://93.184.216.34/initial")
        with pytest.raises(urllib.error.URLError):
            handler.redirect_request(
                req, None, 302, "Found", {}, "http://127.0.0.1:8080/internal-admin"
            )
        with pytest.raises(urllib.error.URLError):
            handler.redirect_request(
                req, None, 301, "Moved", {}, "file:///etc/shadow"
            )


class TestZipSlipAndPathTraversal:
    @pytest.mark.parametrize(
        "bad_member",
        [
            "../../evil.py",
            "yt_dlp/../../../outside.py",
            "/etc/passwd",
            "\\Windows\\System32\\evil.dll",
            "C:/Windows/evil.exe",
            "yt_dlp/../../pwn.sh",
            "yt_dlp/archivo\x00.py",
        ],
    )
    def test_validate_zip_member_blocks_traversal(self, tmp_path, bad_member):
        ok, _ = EngineHotSwapManager.validate_zip_member(bad_member, str(tmp_path))
        assert ok is False

    def test_safe_extract_wheel_rejects_zip_slip_archive(self, tmp_path):
        whl_file = tmp_path / "malicious.whl"
        extract_dir = tmp_path / "plugins"
        extract_dir.mkdir()

        with zipfile.ZipFile(whl_file, "w") as zf:
            zf.writestr("yt_dlp/__init__.py", "# ok\n")
            zf.writestr("yt_dlp/../../escaped.py", "raise SystemExit('pwned')\n")

        with pytest.raises(RuntimeError, match="Zip Slip|fuera de PLUGINS_DIR"):
            EngineHotSwapManager.safe_extract_wheel(str(whl_file), str(extract_dir))

        assert not (tmp_path / "escaped.py").exists()

    def test_safe_extract_wheel_extracts_valid_package(self, tmp_path):
        whl_file = tmp_path / "clean.whl"
        extract_dir = tmp_path / "plugins"
        extract_dir.mkdir()

        with zipfile.ZipFile(whl_file, "w") as zf:
            zf.writestr("yt_dlp/__init__.py", "__version__ = '2026.01.01'\n")
            zf.writestr("yt_dlp/version.py", "__version__ = '2026.01.01'\n")

        extracted = EngineHotSwapManager.safe_extract_wheel(str(whl_file), str(extract_dir))
        assert len(extracted) == 2
        assert (extract_dir / "yt_dlp" / "version.py").is_file()


class TestFilenameAndTemplateSanitization:
    def test_sanitize_filename_removes_traversal_and_leading_dashes(self):
        sanitized = SecurityGuard.sanitize_filename("../../../etc/passwd")
        assert ".." not in sanitized and "/" not in sanitized and sanitized == "etcpasswd"
        assert SecurityGuard.sanitize_filename("-exec_flag_video") == "exec_flag_video"
        assert SecurityGuard.sanitize_filename("CON") == "_CON"
        assert SecurityGuard.sanitize_filename("NUL.txt") == "_NUL.txt"
        clean_title = SecurityGuard.sanitize_filename("Vídeo: Prueba * <2026>?|")
        for bad_ch in (":", "*", "<", ">", "?", "|"):
            assert bad_ch not in clean_title

    def test_sanitize_naming_template_blocks_directory_escape(self):
        tpl = "../../outside/%(title)s.%(ext)s"
        safe_tpl = SecurityGuard.sanitize_naming_template(tpl)
        assert ".." not in safe_tpl
        assert "/" not in safe_tpl
        assert "\\" not in safe_tpl

    def test_verify_safe_path_blocks_outside_and_dangerous_extensions(self, tmp_path):
        base_dir = tmp_path / "downloads"
        base_dir.mkdir()

        safe_mp4 = base_dir / "video_limpio.mp4"
        safe_mp4.write_bytes(b"fake_mp4_content")
        ok, _ = SecurityGuard.verify_safe_path(str(safe_mp4), str(base_dir))
        assert ok is True

        outside_mp4 = tmp_path / "outside.mp4"
        outside_mp4.write_bytes(b"outside")
        ok_out, _ = SecurityGuard.verify_safe_path(str(outside_mp4), str(base_dir))
        assert ok_out is False

        bad_exe = base_dir / "payload.exe"
        bad_exe.write_bytes(b"MZ")
        ok_exe, _ = SecurityGuard.verify_safe_path(str(bad_exe), str(base_dir))
        assert ok_exe is False

    def test_validate_proxy_rules(self):
        assert SecurityGuard.validate_proxy("")[0] is True
        assert SecurityGuard.validate_proxy("socks5://127.0.0.1:9050")[0] is True
        assert SecurityGuard.validate_proxy("http://proxy.example.com:8080")[0] is True
        assert SecurityGuard.validate_proxy("file:///etc/passwd")[0] is False
        assert SecurityGuard.validate_proxy("http://127.0.0.1:8080\r\nHeader: 1")[0] is False

    def test_ssl_certifi_bundle_configuration_and_strict_tls(self):
        import os
        import ssl
        import certifi
        from mpp.core import configure_ssl_certificates

        ca_path = configure_ssl_certificates()
        assert ca_path and os.path.isfile(ca_path)
        assert ca_path == certifi.where()
        assert os.environ.get("SSL_CERT_FILE") == ca_path
        assert os.environ.get("REQUESTS_CA_BUNDLE") == ca_path

        ctx = ssl.create_default_context(cafile=ca_path)
        assert ctx.verify_mode == ssl.CERT_REQUIRED
        assert ctx.check_hostname is True
