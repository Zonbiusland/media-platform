# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Media Platform (Studio Master) — Hilos y Workers Asíncronos (GPLv3+)
# Este archivo es software libre distribuido bajo la licencia GNU GPL v3.0 o posterior.
import importlib
import ssl
from .core import *
from .i18n import tr


class ManagedWorker(QThread):
    """Clase base para todos los QThreads de la aplicación con registro centralizado de ciclo de vida."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_cancelled = False
        self.is_paused = False
        ProcessAndThreadRegistry.register_thread(self)
        self.finished.connect(lambda: ProcessAndThreadRegistry.unregister_thread(self))


class AnalyzerWorker(ManagedWorker):
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, query_or_url: str, cookies_browser="Ninguno", cookies_file=""):
        super().__init__()
        self.query_or_url = str(query_or_url or "").strip()
        self.cookies_browser = cookies_browser
        self.cookies_file = cookies_file

    def _fetch_thumbnail_bytes(self, thumb_url: str) -> bytes:
        ok, clean_thumb = SecurityGuard.validate_url(thumb_url)
        if not ok:
            return b""
        try:
            opener = urllib.request.build_opener(SafeRedirectHandler())
            req = urllib.request.Request(clean_thumb, headers={"User-Agent": "Mozilla/5.0"})
            with opener.open(req, timeout=6) as resp:
                return resp.read(2 * 1024 * 1024)
        except Exception:
            return b""

    def _format_dur(self, dur) -> str:
        if isinstance(dur, (int, float)) and dur > 0:
            m, s = divmod(int(dur), 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        return "Directo / Variable"

    def run(self):
        is_search = not SecurityGuard.is_url(self.query_or_url)
        if not is_search:
            ok, msg = SecurityGuard.validate_url(self.query_or_url)
            if not ok:
                self.error_signal.emit(msg)
                return
            target = self.query_or_url
        else:
            target = f"ytsearch15:{self.query_or_url}"

        opts = {
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": False,
            "logger": _YtdlpSilentLogger(),
            "extract_flat": "in_playlist",
            "socket_timeout": 15,
        }
        if not is_search:
            CookieHelper.apply_cookies(opts, self.cookies_browser, self.cookies_file)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(target, download=False)

            if not isinstance(info, dict):
                self.error_signal.emit("No se recibieron metadatos del servidor.")
                return

            if info.get("_type") == "playlist" or isinstance(info.get("entries"), list):
                raw_entries = [e for e in (info.get("entries") or []) if isinstance(e, dict)]
                parsed_entries = []
                for e in raw_entries:
                    u = e.get("url") or e.get("webpage_url")
                    if not u and e.get("id") and "youtube" in str(info.get("extractor_key") or "").lower():
                        u = f"https://www.youtube.com/watch?v={e['id']}"
                    if u and str(u).startswith(("http://", "https://")):
                        parsed_entries.append({
                            "title": e.get("title") or "Vídeo de la lista",
                            "duration": self._format_dur(e.get("duration")),
                            "channel": e.get("uploader") or e.get("channel") or info.get("uploader") or "Web",
                            "url": u
                        })

                self.finished_signal.emit({
                    "is_playlist": True,
                    "is_search": is_search,
                    "title": f"Resultados para: {self.query_or_url}" if is_search else (info.get("title") or "Lista / Canal"),
                    "channel": info.get("uploader") or info.get("channel") or "Varios",
                    "platform": "Buscador Directo" if is_search else (info.get("extractor_key") or "Web"),
                    "count": len(parsed_entries),
                    "entries": parsed_entries
                })
                return

            formats = info.get("formats") or []
            vcodecs, acodecs, hdr_types = set(), set(), set()
            max_height = 0
            max_fps = 0
            est_size = 0

            for f in formats:
                if not isinstance(f, dict):
                    continue
                h = f.get("height")
                if isinstance(h, (int, float)) and h > max_height:
                    max_height = int(h)
                fps = f.get("fps")
                if isinstance(fps, (int, float)) and fps > max_fps:
                    max_fps = int(fps)
                vc = f.get("vcodec")
                if isinstance(vc, str) and vc.lower() != "none":
                    vcodecs.add(vc.split(".")[0].upper())
                ac = f.get("acodec")
                if isinstance(ac, str) and ac.lower() != "none":
                    acodecs.add(ac.split(".")[0].upper())
                dr = f.get("dynamic_range")
                if isinstance(dr, str) and dr.upper() != "SDR":
                    hdr_types.add(dr)
                sz = f.get("filesize") or f.get("filesize_approx") or 0
                if isinstance(sz, (int, float)) and sz > est_size:
                    est_size = sz

            if not max_height and isinstance(info.get("height"), (int, float)):
                max_height = int(info["height"])

            subs_dict = info.get("subtitles")
            subs = list(subs_dict.keys()) if isinstance(subs_dict, dict) else []
            chapters = info.get("chapters") if isinstance(info.get("chapters"), list) else []
            dur_str = self._format_dur(info.get("duration"))
            hdr_str = ", ".join(hdr_types) if hdr_types else "SDR"
            rec_container = "MKV" if hdr_types else "MP4"
            thumb_bytes = self._fetch_thumbnail_bytes(info.get("thumbnail") or "")

            self.finished_signal.emit({
                "is_playlist": False,
                "title": info.get("title") or "Vídeo detectado",
                "channel": info.get("uploader") or info.get("channel") or "Autor desconocido",
                "platform": info.get("extractor_key") or "Web",
                "duration": dur_str,
                "max_res": f"{max_height}p" if max_height else "Nativa",
                "max_fps": f"{max_fps} FPS" if max_fps else "Estándar",
                "hdr": hdr_str,
                "vcodecs": ", ".join(sorted(vcodecs)) if vcodecs else "H.264",
                "acodecs": ", ".join(sorted(acodecs)) if acodecs else "AAC",
                "subtitles": ", ".join(subs[:6]) if subs else "Auto / No",
                "chapters": len(chapters),
                "est_size_mb": round(est_size / (1024 * 1024), 1) if est_size else 0,
                "recommended": rec_container,
                "thumbnail_bytes": thumb_bytes
            })
        except Exception as e:
            self.error_signal.emit(str(e))


class WebSnifferWorker(ManagedWorker):
    finished_signal = Signal(list)
    error_signal = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = str(url or "").strip()

    @staticmethod
    def _extract_from_text(raw_text: str, base_url: str, source_tag: str, seen: set, results: list):
        slash = chr(92)
        normalized = (
            raw_text.replace(slash + "/", "/")
            .replace(slash + "u002F", "/")
            .replace(slash + "u0026", "&")
            .replace("&amp;", "&")
        )

        media_regex = re.compile(
            r'(https?://[^\s\x22\x27<>\\?#]{1,500}\.(?:m3u8|mpd|mp4|webm|m4v|mov)(?:\?[^\s\x22\x27<>\\#]{0,500})?)',
            re.IGNORECASE
        )
        for match in media_regex.findall(normalized):
            clean_u = match.rstrip("),;")
            if clean_u not in seen:
                seen.add(clean_u)
                path_part = clean_u.split("?")[0]
                ext = path_part.split(".")[-1].upper()
                low_u = clean_u.lower()
                if ".m3u8" in low_u:
                    mtype = f"Stream HLS (.m3u8) [{source_tag}]"
                elif ".mpd" in low_u:
                    mtype = f"Stream DASH (.mpd) [{source_tag}]"
                else:
                    mtype = f"Vídeo Directo .{ext} [{source_tag}]"

                host = urlparse(clean_u).hostname or "Servidor Multimedia"
                fname = os.path.basename(path_part) or f"Flujo {ext}"
                results.append({
                    "title": fname,
                    "duration": mtype,
                    "channel": host,
                    "url": clean_u,
                    "type": mtype
                })

    @staticmethod
    def _fetch_html(target_url: str, headers: dict, timeout: int = 12, max_bytes: int = 2 * 1024 * 1024) -> str:
        safe_headers = dict(headers or {})
        req = urllib.request.Request(target_url, headers=safe_headers)
        ca_bundle = os.environ.get("SSL_CERT_FILE") or ""
        ctx = ssl.create_default_context(cafile=ca_bundle if (ca_bundle and os.path.isfile(ca_bundle)) else None)
        opener = urllib.request.build_opener(SafeRedirectHandler(), urllib.request.HTTPSHandler(context=ctx))
        with opener.open(req, timeout=timeout) as resp:
            return resp.read(max_bytes).decode("utf-8", errors="replace")

    def run(self):
        ok, clean_url = SecurityGuard.validate_url(self.url)
        if not ok:
            self.error_signal.emit(clean_url)
            return

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            raw_html = self._fetch_html(clean_url, headers, timeout=12)

            seen = set()
            results = []

            self._extract_from_text(raw_html, clean_url, "HTML/JSON", seen, results)

            iframe_regex = re.compile(r'<(?:iframe|embed|source)[^>]+src=[\x22\x27]([^\x22\x27]+)[\x22\x27]', re.IGNORECASE)
            iframe_urls = []
            for raw_src in iframe_regex.findall(raw_html):
                full_src = urljoin(clean_url, raw_src.strip())
                if full_src.startswith(("http://", "https://")) and full_src not in seen:
                    low_s = full_src.lower()
                    if any(ext in low_s for ext in (".m3u8", ".mpd", ".mp4", ".webm", ".m4v", ".mov")):
                        self._extract_from_text(full_src, clean_url, "Directo", seen, results)
                    else:
                        seen.add(full_src)
                        host = urlparse(full_src).hostname or "Embed"
                        mtype = "Reproductor Embebido (Iframe)"
                        results.append({
                            "title": f"Reproductor incrustado ({host})",
                            "duration": mtype,
                            "channel": host,
                            "url": full_src,
                            "type": mtype
                        })
                        iframe_urls.append(full_src)

            for if_url in iframe_urls[:3]:
                ok_if, _ = SecurityGuard.validate_url(if_url)
                if not ok_if:
                    continue
                try:
                    if_headers = dict(headers)
                    if_headers["Referer"] = clean_url
                    if_html = self._fetch_html(if_url, if_headers, timeout=6, max_bytes=1024 * 1024)
                    self._extract_from_text(if_html, if_url, "Iframe Interno", seen, results)
                except Exception:
                    pass

            self.finished_signal.emit(results)
        except Exception as e:
            self.error_signal.emit(f"Error al inspeccionar la página web: {e}")


class TranscriptWorker(ManagedWorker):
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, url: str, out_dir: str, preset_langs: str, cookies_browser="Ninguno", cookies_file=""):
        super().__init__()
        self.url = str(url or "").strip()
        self.out_dir = out_dir
        self.preset_langs = preset_langs
        self.cookies_browser = cookies_browser
        self.cookies_file = cookies_file

    def _clean_vtt_to_text(self, raw_vtt: str) -> str:
        lines = []
        last_line = ""
        for line in raw_vtt.splitlines():
            s = line.strip()
            if not s or s.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
                continue
            if "-->" in s or s.isdigit():
                continue
            s = re.sub(r"<[^>]+>", "", s)
            s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"').strip()
            if s and s != last_line:
                lines.append(s)
                last_line = s
        return " ".join(lines)

    def run(self):
        ok, clean_url = SecurityGuard.validate_url(self.url)
        if not ok:
            self.error_signal.emit(clean_url)
            return

        temp_dir = tempfile.mkdtemp(prefix="mpp_sub_")
        try:
            probe_opts = {
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": False,
                "logger": _YtdlpSilentLogger(),
            }
            CookieHelper.apply_cookies(probe_opts, self.cookies_browser, self.cookies_file)

            with yt_dlp.YoutubeDL(probe_opts) as ydl:
                info = ydl.extract_info(clean_url, download=False)

            chosen_langs, need_man, need_auto = SubtitleResolver.resolve_tracks(info, self.preset_langs)
            if not chosen_langs:
                self.error_signal.emit(
                    f"El vídeo no dispone de subtítulos ni transcripción para: {self.preset_langs}."
                )
                return

            dl_opts = dict(probe_opts)
            dl_opts.update({
                "skip_download": True,
                "writesubtitles": need_man,
                "writeautomaticsub": need_auto,
                "subtitleslangs": chosen_langs,
                "sleep_interval_subtitles": 2,
                "subtitlesformat": "vtt/srt/best",
                "outtmpl": os.path.join(temp_dir, "sub_%(id)s.%(ext)s"),
            })
            with yt_dlp.YoutubeDL(dl_opts) as ydl:
                ydl.extract_info(clean_url, download=True)

            sub_files = glob.glob(os.path.join(temp_dir, "*.vtt")) + glob.glob(os.path.join(temp_dir, "*.srt"))
            if not sub_files:
                self.error_signal.emit(
                    "YouTube rechazó temporalmente la petición de subtítulos (Error 429). "
                    "Selecciona tu navegador o un archivo cookies.txt en 'Ajustes y Red -> Cookies'."
                )
                return

            info = info if isinstance(info, dict) else {}
            title = SecurityGuard.sanitize_filename(info.get("title"), default="Transcripcion")[:85]
            saved_files = []
            safe_out_dir = os.path.realpath(self.out_dir)

            for sf in sub_files:
                parts = os.path.basename(sf).rsplit(".", 2)
                raw_lang = parts[-2] if len(parts) >= 3 else "idioma"
                lang_tag = SecurityGuard.sanitize_filename(raw_lang, default="idioma")[:25]
                with open(sf, "r", encoding="utf-8", errors="ignore") as f:
                    clean_text = self._clean_vtt_to_text(f.read(15 * 1024 * 1024))

                final_txt = os.path.join(safe_out_dir, f"{title} - Guion [{lang_tag}].txt")
                safe_ok, safe_msg = SecurityGuard.verify_safe_path(final_txt, safe_out_dir)
                if not safe_ok:
                    raise RuntimeError(safe_msg)
                with open(final_txt, "w", encoding="utf-8") as f:
                    f.write(f"TÍTULO : {info.get('title', 'Desconocido')}\n")
                    f.write(f"CANAL  : {info.get('uploader', 'Desconocido')}\n")
                    f.write(f"IDIOMA : {lang_tag}\n")
                    f.write(f"ORIGEN : {clean_url}\n")
                    f.write("=" * 72 + "\n\n")
                    f.write(clean_text + "\n")
                saved_files.append(final_txt)

            self.finished_signal.emit(saved_files[0])
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class _DownloadYtdlpLogger(_YtdlpSilentLogger):
    """Captura mensajes clave de yt-dlp (ej. 'has already been downloaded') manteniendo el modo silencioso."""
    def __init__(self, on_message=None):
        self._on_message = on_message

    def debug(self, msg):
        if self._on_message:
            self._on_message(str(msg or ""))

    def info(self, msg):
        if self._on_message:
            self._on_message(str(msg or ""))


class DownloadWorker(ManagedWorker):
    progress_signal = Signal(str, float, str, str, str)
    finished_signal = Signal(str, bool, str, dict)
    log_signal = Signal(str, str)

    def __init__(self, task_id, url, config, ffmpeg_path):
        super().__init__()
        self.task_id = task_id
        self.url = str(url or "").strip()
        self.config = config
        self.ffmpeg_path = ffmpeg_path
        self.is_paused = False
        self.is_cancelled = False
        self.final_filepath = ""
        self.temp_files = set()
        self._last_ui_emit = 0.0
        self._skipped_existing_meta = None
        self._already_downloaded_on_disk = False
        self._sponsorblock_segments = []
        self._sponsor_logs = []
        self._db = None

    def _emit_log(self, text: str):
        msg = str(text or "").strip()
        if msg:
            self._sponsor_logs.append(msg)
            self.log_signal.emit(self.task_id, msg)

    def hook(self, d):
        if not isinstance(d, dict):
            return
        for k in ("tmpfilename", "filename"):
            val = d.get(k)
            if val:
                self.temp_files.add(str(val))

        if self.is_paused and not self.is_cancelled:
            self.progress_signal.emit(self.task_id, 0.0, "0 KB/s", "--:--", tr("status.paused"))
            while self.is_paused and not self.is_cancelled:
                time.sleep(0.2)
            self._last_ui_emit = 0.0

        if self.is_cancelled:
            raise RuntimeError("CANCELLED_BY_USER")

        status = d.get("status")
        if status == "downloading":
            now = time.monotonic()
            if (now - self._last_ui_emit) < 0.14:
                return
            self._last_ui_emit = now

            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0
            pct = (downloaded / total) * 100 if total > 0 else 0.0
            speed = str(d.get("_speed_str") or "N/A").strip()
            eta = str(d.get("_eta_str") or "N/A").strip()
            self.progress_signal.emit(self.task_id, pct, speed, eta, tr("status.downloading"))

        elif status == "finished":
            fn = d.get("filename")
            if fn:
                self.final_filepath = str(fn)
            self.progress_signal.emit(self.task_id, 100.0, "--", "00:00", tr("status.packing"))

    def postprocessor_hook(self, d):
        if isinstance(d, dict):
            info_d = d.get("info_dict")
            if isinstance(info_d, dict):
                if info_d.get("filepath") and d.get("status") == "finished":
                    self.final_filepath = str(info_d["filepath"])
                sb_chaps = info_d.get("sponsorblock_chapters")
                if isinstance(sb_chaps, list) and sb_chaps:
                    self._sponsorblock_segments = list(sb_chaps)

    def cleanup_partials(self):
        for fpath in list(self.temp_files):
            for candidate in (
                fpath, fpath + ".part", fpath + ".ytdl",
                fpath + ".h264.mp4", fpath + ".ln2p", fpath + ".exact",
                fpath + ".smartsponsor_concat.txt"
            ):
                try:
                    if candidate and os.path.isfile(candidate):
                        os.remove(candidate)
                except Exception:
                    pass

    def _parse_hms(self, hms):
        parts = [int(p) for p in str(hms).strip().split(":")]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return parts[0]

    def _get_worker_db(self) -> DatabaseManager:
        if self._db is None:
            self._db = DatabaseManager(privacy_mode=bool(self.config.get("privacy_mode", False)))
        return self._db

    def _duplicate_match_filter(self, info_dict, *, incomplete=False):
        if incomplete or not isinstance(info_dict, dict):
            return None
        if not self.config.get("skip_duplicates"):
            return None
        vid = str(info_dict.get("id") or "").strip()
        platform = str(info_dict.get("extractor_key") or "").strip()
        if not vid:
            return None
        existing = self._get_worker_db().find_existing_download(vid, platform)
        if existing:
            existing["_already_in_db"] = True
            self._skipped_existing_meta = existing
            self.final_filepath = str(existing.get("filepath") or "")
            return "Vídeo omitido: ya existe en la videoteca local."
        return None

    @staticmethod
    def _is_ytdlp_extractor_error(err_text: str) -> bool:
        low = str(err_text or "").lower()
        indicators = (
            "http error 403",
            "403: forbidden",
            "nsig",
            "sabr",
            "signature extraction",
            "unable to extract",
            "extractor",
            "please report this issue on",
        )
        return any(tok in low for tok in indicators)

    def _on_ytdlp_log(self, msg: str):
        if "has already been downloaded" in str(msg or "").lower():
            self._already_downloaded_on_disk = True

    @staticmethod
    def build_ytdlp_cli_args(config: dict) -> list[str]:
        """Devuelve los flags CLI equivalentes activos para la descarga (ej. '--force-overwrites')."""
        cfg = config or {}
        if cfg.get("overwrite_existing") or cfg.get("force_overwrite"):
            return ["--force-overwrites"]
        return []

    def run(self):
        ok, clean_url = SecurityGuard.validate_url(self.url)
        if not ok:
            self.finished_signal.emit(self.task_id, False, clean_url, {})
            return

        self._already_downloaded_on_disk = False
        force_overwrite = bool(self.config.get("overwrite_existing", False) or self.config.get("force_overwrite", False))

        base_dir = os.path.realpath(self.config["base_dir"])
        temp_dir = setup_isolated_temp_dir()
        if self.config["auto_organize"]:
            out_dir = os.path.join(base_dir, "%(extractor_key)s", "%(uploader|General)s")
        else:
            out_dir = base_dir

        safe_template = SecurityGuard.sanitize_naming_template(self.config.get("naming_template"))

        ydl_opts = {
            "paths": {"home": out_dir, "temp": temp_dir},
            "outtmpl": {"default": safe_template},
            "windowsfilenames": True,
            "concurrent_fragment_downloads": self.config["fragments"],
            "retries": 10,
            "fragment_retries": 10,
            "continuedl": True,
            "overwrites": force_overwrite,
            "buffersize": 65536,
            "http_chunk_size": 10485760,
            "socket_timeout": 20,
            "noplaylist": not self.config["allow_playlist"],
            "live_from_start": self.config.get("live_from_start", False),
            "progress_hooks": [self.hook],
            "postprocessor_hooks": [self.postprocessor_hook],
            "color": "no_color",
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": False,
            "logger": _DownloadYtdlpLogger(self._on_ytdlp_log),
        }

        if self.config.get("skip_duplicates") and not force_overwrite:
            ydl_opts["match_filter"] = self._duplicate_match_filter

        if self.ffmpeg_path:
            ydl_opts["ffmpeg_location"] = self.ffmpeg_path

        if self.config["speed_limit_kb"] > 0:
            ydl_opts["ratelimit"] = self.config["speed_limit_kb"] * 1024

        if self.config.get("proxy"):
            ok_px, clean_px = SecurityGuard.validate_proxy(self.config["proxy"])
            if not ok_px:
                self.finished_signal.emit(self.task_id, False, clean_px, {})
                return
            if clean_px:
                ydl_opts["proxy"] = clean_px

        CookieHelper.apply_cookies(
            ydl_opts,
            self.config.get("cookies_browser", "Ninguno"),
            self.config.get("cookies_file", "")
        )

        postprocessors = []
        fmt_choice = str(self.config["quality"])
        container = str(self.config["container"]).lower()
        is_audio_only = fmt_choice.startswith("Solo Audio")

        if is_audio_only:
            acodec = fmt_choice.split("(")[1].replace(")", "").lower()
            ydl_opts["format"] = "bestaudio/best"
            postprocessors.append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": acodec,
                "preferredquality": "320"
            })
        else:
            height_map = {
                "4320p (8K Ultra HD)": 4320,
                "2160p (4K UHD)": 2160,
                "1440p (2K QHD)": 1440,
                "1080p (Full HD)": 1080,
                "720p (HD)": 720,
                "480p (Estándar)": 480,
                "360p (Datos reducidos)": 360
            }
            max_h = height_map.get(fmt_choice)

            if container == "mp4":
                ydl_opts["format_sort"] = ["vcodec:h264", "acodec:m4a", "ext:mp4:m4a"]
                if max_h:
                    ydl_opts["format"] = f"bestvideo[height<={max_h}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={max_h}]+bestaudio/best[height<={max_h}]/best"
                else:
                    ydl_opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
            else:
                if max_h:
                    ydl_opts["format"] = f"bestvideo[height<={max_h}]+bestaudio/best[height<={max_h}]/best"
                else:
                    ydl_opts["format"] = "bestvideo+bestaudio/best"

            ydl_opts["merge_output_format"] = container

        if self.config["embed_thumbnail"]:
            ydl_opts["writethumbnail"] = True
            postprocessors.append({"key": "FFmpegThumbnailsConvertor", "format": "jpg"})
            postprocessors.append({"key": "EmbedThumbnail"})

        if self.config["sponsorblock"]:
            postprocessors.append({
                "key": "SponsorBlock",
                "categories": ["sponsor", "intro", "outro", "selfpromo"]
            })
            postprocessors.append({
                "key": "ModifyChapters",
                "remove_sponsor_segments": ["sponsor", "intro", "outro", "selfpromo"]
            })

        if self.config.get("split_chapters"):
            postprocessors.append({"key": "FFmpegSplitChapters", "force_keyframes": False})

        if self.config["subtitles"]:
            ydl_opts["writesubtitles"] = True
            ydl_opts["writeautomaticsub"] = True
            ydl_opts["sleep_interval_subtitles"] = 2
            preset_str = self.config["sub_langs"]
            lang_map = []
            for chain in SubtitleResolver.get_target_groups(preset_str):
                if chain[0] not in lang_map:
                    lang_map.append(chain[0])
                base_c = chain[0].split("-")[0]
                if base_c not in lang_map:
                    lang_map.append(base_c)
            ydl_opts["subtitleslangs"] = lang_map
            if self.config["embed_subs"]:
                postprocessors.append({"key": "FFmpegEmbedSubtitle"})

        if postprocessors:
            ydl_opts["postprocessors"] = postprocessors

        if self.config["trim_enabled"]:
            try:
                t1 = self._parse_hms(self.config["trim_start"])
                t2 = self._parse_hms(self.config["trim_end"])
                if t2 > t1:
                    ydl_opts["download_ranges"] = yt_dlp.utils.download_range_func(None, [(t1, t2)])
                    if not is_audio_only:
                        ydl_opts["force_keyframes_at_cuts"] = True
            except Exception:
                pass

        mc = MediaCore()
        if self.ffmpeg_path:
            mc.ffmpeg_path = self.ffmpeg_path
        cancel_fn = lambda: self.is_cancelled

        try:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(clean_url, download=True)
            except Exception as dl_err:
                err_msg = str(dl_err)
                if (
                    not self.is_cancelled
                    and "CANCELLED_BY_USER" not in err_msg
                    and self.config.get("auto_update_engine", True)
                    and self._is_ytdlp_extractor_error(err_msg)
                ):
                    self.progress_signal.emit(self.task_id, 0.0, "--", "--:--", "Actualizando motor yt-dlp...")
                    self._emit_log(f"[Auto-Update] Error de extractor detectado ({err_msg[:120]}). Actualizando yt-dlp en caliente...")
                    ok_upd, upd_msg = EngineHotSwapManager.update_yt_dlp_plugin()
                    self._emit_log(f"[Auto-Update] {upd_msg}")
                    if ok_upd:
                        if "yt_dlp" in sys.modules:
                            globals()["yt_dlp"] = sys.modules["yt_dlp"]
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(clean_url, download=True)
                    else:
                        raise
                else:
                    raise

            if self._skipped_existing_meta and not self.config.get("allow_playlist"):
                self.progress_signal.emit(self.task_id, 100.0, "--", "00:00", tr("status.skipped_dup"))
                self.finished_signal.emit(self.task_id, True, tr("status.skipped_dup"), self._skipped_existing_meta)
                return

            if not isinstance(info, dict):
                info = {}
            if isinstance(info.get("entries"), list) and info["entries"]:
                first_entry = info["entries"][0]
                if isinstance(first_entry, dict):
                    info = first_entry

            if not self.final_filepath and info.get("filepath"):
                self.final_filepath = str(info["filepath"])

            if self.final_filepath and os.path.isfile(self.final_filepath):
                safe_ok, safe_msg = SecurityGuard.verify_safe_path(self.final_filepath, base_dir)
                if not safe_ok:
                    try:
                        if os.path.isfile(self.final_filepath):
                            os.remove(self.final_filepath)
                    except Exception:
                        pass
                    self.finished_signal.emit(self.task_id, False, safe_msg, {})
                    return

                # Si el usuario pidió MP4 y el servidor solo tenía AV1 o VP9, convertir a H.264 compatible
                vcodec_dl = str(info.get("vcodec") or "").lower()
                if not is_audio_only and container == "mp4" and mc.ffmpeg_path:
                    if vcodec_dl and not vcodec_dl.startswith(("avc", "h264", "none")):
                        self.progress_signal.emit(self.task_id, 99.0, "--", "00:00", tr("status.converting_h264"))
                        tmp_h264 = self.final_filepath + ".h264.mp4"
                        self.temp_files.add(tmp_h264)
                        ok_h264, _, err_h264 = mc.run_ffmpeg_cmd(
                            [
                                mc.ffmpeg_path, "-hide_banner", "-y", "-i", self.final_filepath,
                                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp_h264
                            ],
                            cancel_check=cancel_fn
                        )
                        if ok_h264 and os.path.isfile(tmp_h264) and os.path.getsize(tmp_h264) > 0:
                            os.replace(tmp_h264, self.final_filepath)
                            self.temp_files.discard(tmp_h264)
                            info["vcodec"] = "h264"
                        elif os.path.isfile(tmp_h264):
                            try:
                                os.remove(tmp_h264)
                            except Exception:
                                pass

            if self.config.get("loudnorm") and mc.ffmpeg_path and self.final_filepath and os.path.isfile(self.final_filepath):
                self.progress_signal.emit(self.task_id, 99.0, "--", "00:00", tr("status.normalizing_audio"))
                base_f, ext_f = os.path.splitext(self.final_filepath)
                self.temp_files.add(f"{base_f}.ln2p{ext_f}")
                mc.normalize_loudnorm_two_pass(
                    self.final_filepath,
                    is_audio_only=is_audio_only,
                    cancel_check=cancel_fn
                )

            if self.config["trim_enabled"] and is_audio_only and mc.ffmpeg_path and self.final_filepath and os.path.isfile(self.final_filepath):
                try:
                    t1_s = self._parse_hms(self.config["trim_start"])
                    t2_s = self._parse_hms(self.config["trim_end"])
                    target_dur = float(t2_s - t1_s)
                    if target_dur > 0:
                        base_a, ext_a = os.path.splitext(self.final_filepath)
                        tmp_trim = f"{base_a}.exact{ext_a}"
                        self.temp_files.add(tmp_trim)
                        ok_tr, _, _ = mc.run_ffmpeg_cmd(
                            [
                                mc.ffmpeg_path, "-hide_banner", "-y",
                                "-sseof", f"-{target_dur}", "-t", str(target_dur),
                                "-i", self.final_filepath, "-c", "copy", tmp_trim
                            ],
                            cancel_check=cancel_fn
                        )
                        if ok_tr and os.path.isfile(tmp_trim) and os.path.getsize(tmp_trim) > 0:
                            os.replace(tmp_trim, self.final_filepath)
                            self.temp_files.discard(tmp_trim)
                        elif os.path.isfile(tmp_trim):
                            os.remove(tmp_trim)
                except RuntimeError:
                    raise
                except Exception:
                    pass

            # Respaldo SmartSponsorDetector cuando SponsorBlock devuelve 0 segmentos
            # o cuando está activo el modo de "Detección inteligente por transcripción"
            sponsor_cuts_applied = []
            sb_enabled = bool(self.config.get("sponsorblock", False))
            smart_enabled = bool(self.config.get("smart_sponsor", False))
            sb_found = self._sponsorblock_segments or (info.get("sponsorblock_chapters") if isinstance(info, dict) else None) or []

            if sb_enabled and sb_found:
                sb_summary = ", ".join(
                    f"[{SmartSponsorDetector.format_timestamp(c.get('start_time', 0))} - {SmartSponsorDetector.format_timestamp(c.get('end_time', 0))}]"
                    for c in sb_found if isinstance(c, dict)
                )
                self._emit_log(f"[SponsorBlock] {len(sb_found)} segmento(s) eliminado(s) por API comunitaria: {sb_summary}")
            elif (smart_enabled or sb_enabled) and not sb_found and self.final_filepath and os.path.isfile(self.final_filepath):
                if sb_enabled and not smart_enabled:
                    self._emit_log("[SponsorBlock] 0 segmentos en la base de datos comunitaria (respaldo por transcripción desactivado).")
                else:
                    if sb_enabled:
                        self._emit_log("[SmartSponsor] SponsorBlock devolvió 0 segmentos. Activando detección inteligente por transcripción...")
                    else:
                        self._emit_log("[SmartSponsor] Iniciando detección inteligente de patrocinios por transcripción...")

                    self.progress_signal.emit(self.task_id, 99.0, "--", "00:00", tr("status.smartsponsor_analyzing"))

                    cues, sub_info = SmartSponsorDetector.fetch_cues_with_ytdlp(
                        clean_url,
                        cookies_browser=self.config.get("cookies_browser", "Ninguno"),
                        cookies_file=self.config.get("cookies_file", ""),
                        ffmpeg_path=self.ffmpeg_path,
                        proxy=self.config.get("proxy", ""),
                        log_fn=self._emit_log
                    )

                    if not cues:
                        self.progress_signal.emit(self.task_id, 99.0, "--", "00:00", tr("status.smartsponsor_whisper"))
                        cues = SmartSponsorDetector.transcribe_with_faster_whisper(
                            self.final_filepath,
                            log_fn=self._emit_log
                        )

                    if cues:
                        vid_dur = float(info.get("duration") or sub_info.get("duration") or 0.0)
                        chaps = info.get("chapters") or sub_info.get("chapters") or []
                        detected = SmartSponsorDetector.detect_sponsor_segments(
                            cues,
                            chapters=chaps,
                            duration=vid_dur
                        )
                        if detected:
                            for idx_s, seg in enumerate(detected, 1):
                                phrases_str = ", ".join(seg.get("phrases", []))
                                self._emit_log(
                                    f"[SmartSponsor] Tramo #{idx_s} detectado: [{seg['start_str']} -> {seg['end_str']}] "
                                    f"({seg['duration']:.1f}s) | Indicadores: {phrases_str}"
                                )
                            self.progress_signal.emit(
                                self.task_id, 99.5, "--", "00:00",
                                tr("status.smartsponsor_trimming", count=len(detected))
                            )
                            cut_ok, cut_msg = SmartSponsorDetector.cut_segments_ffmpeg(
                                self.final_filepath,
                                detected,
                                ffmpeg_path=mc.ffmpeg_path,
                                total_duration=vid_dur,
                                cancel_check=cancel_fn
                            )
                            self._emit_log(f"[SmartSponsor] {cut_msg}")
                            if cut_ok:
                                sponsor_cuts_applied = detected
                        else:
                            self._emit_log("[SmartSponsor] Transcripción analizada: 0 bloques patrocinados detectados.")

            sha256_hash = SecurityGuard.compute_sha256(self.final_filepath)

            already_dl = bool(self._already_downloaded_on_disk)
            meta = {
                "video_id": str(info.get("id") or ""),
                "title": str(info.get("title") or "Vídeo descargado"),
                "channel": str(info.get("uploader") or info.get("channel") or "Desconocido"),
                "platform": str(info.get("extractor_key") or "Web"),
                "resolution": f"{info.get('height')}p" if info.get("height") else "Audio / Directo",
                "fps": info.get("fps") or "N/A",
                "hdr": str(info.get("dynamic_range") or "SDR"),
                "vcodec": str(info.get("vcodec") or "N/A"),
                "acodec": str(info.get("acodec") or "N/A"),
                "filepath": self.final_filepath,
                "filesize": os.path.getsize(self.final_filepath) if (self.final_filepath and os.path.isfile(self.final_filepath)) else (info.get("filesize") or info.get("filesize_approx") or 0),
                "file_hash": sha256_hash,
                "already_downloaded": already_dl,
                "sponsor_cuts": sponsor_cuts_applied,
                "sponsor_logs": list(self._sponsor_logs)
            }
            if already_dl:
                done_msg = tr("status.already_downloaded")
                self._emit_log(f"[yt-dlp] {done_msg}: {self.final_filepath}")
                self.progress_signal.emit(self.task_id, 100.0, "--", "00:00", done_msg)
            elif sponsor_cuts_applied:
                done_msg = f"Completado ({len(sponsor_cuts_applied)} patrocinio(s) recortado(s))"
            else:
                done_msg = "Completado"
            self.finished_signal.emit(self.task_id, True, done_msg, meta)
            gc.collect()
        except Exception as e:
            msg = str(e)
            if "CANCELLED_BY_USER" in msg:
                self.cleanup_partials()
                self.finished_signal.emit(self.task_id, False, "Cancelado", {})
            else:
                self.finished_signal.emit(self.task_id, False, msg, {})


class ProbeWorker(ManagedWorker):
    finished_signal = Signal(str, float, str, dict)
    error_signal = Signal(str)

    def __init__(self, filepath: str):
        super().__init__()
        self.filepath = str(filepath or "").strip()

    def run(self):
        if not self.filepath or not os.path.isfile(self.filepath):
            self.error_signal.emit("El archivo seleccionado no existe.")
            return
        try:
            mc = MediaCore()
            sha = SecurityGuard.compute_sha256(self.filepath)
            info = mc.probe_file(self.filepath)
            try:
                dur = float(info.get("format", {}).get("duration", 0.0)) if info else 0.0
            except Exception:
                dur = 0.0
            self.finished_signal.emit(self.filepath, dur, sha, info or {})
        except Exception as e:
            self.error_signal.emit(str(e))


class FFmpegTaskWorker(ManagedWorker):
    status_signal = Signal(str)
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, in_file: str, out_file: str, mode: str = "remux", hw_accel: str = "cpu", target_mb: int = 0):
        super().__init__()
        self.in_file = in_file
        self.out_file = out_file
        self.mode = mode
        self.hw_accel = hw_accel
        self.target_mb = target_mb
        self.is_cancelled = False

    def run(self):
        try:
            self.status_signal.emit(f"Procesando con FFmpeg ({self.mode})...")
            mc = MediaCore()
            mc.process_media(
                self.in_file,
                self.out_file,
                mode=self.mode,
                hw_accel=self.hw_accel,
                target_mb=self.target_mb,
                cancel_check=lambda: self.is_cancelled
            )
            self.finished_signal.emit(self.out_file)
        except Exception as e:
            msg = str(e)
            if "CANCELLED_BY_USER" in msg:
                try:
                    if os.path.isfile(self.out_file):
                        os.remove(self.out_file)
                except Exception:
                    pass
                self.error_signal.emit("Procesamiento cancelado por el usuario.")
            else:
                self.error_signal.emit(msg)


class UpdateEngineWorker(ManagedWorker):
    finished_signal = Signal(bool, str)
    error_signal = Signal(str)

    def run(self):
        try:
            ok, msg = EngineHotSwapManager.update_yt_dlp_plugin()
            if ok:
                mod = EngineHotSwapManager.load_plugin_yt_dlp()
                if mod is not None:
                    globals()["yt_dlp"] = mod
                elif "yt_dlp" in sys.modules:
                    try:
                        importlib.reload(sys.modules["yt_dlp"])
                    except Exception:
                        pass
            self.finished_signal.emit(ok, msg)
        except Exception as e:
            self.error_signal.emit(str(e))


class RollbackEngineWorker(ManagedWorker):
    """Revierte yt-dlp en segundo plano al respaldo anterior o al motor nativo integrado."""
    finished_signal = Signal(bool, str)
    error_signal = Signal(str)

    def run(self):
        try:
            ok, msg = EngineHotSwapManager.rollback_yt_dlp_plugin()
            if ok and "yt_dlp" in sys.modules:
                globals()["yt_dlp"] = sys.modules["yt_dlp"]
            self.finished_signal.emit(ok, msg)
        except Exception as e:
            self.error_signal.emit(str(e))


class EngineVersionCheckWorker(ManagedWorker):
    """Comprobador ligero en segundo plano al arranque para detectar nuevas versiones de yt-dlp en PyPI."""
    update_available_signal = Signal(str, str)

    def run(self):
        try:
            has_newer, curr_ver, latest_ver = EngineHotSwapManager.check_pypi_update(timeout=6.0)
            if has_newer and not self.is_cancelled:
                self.update_available_signal.emit(curr_ver, latest_ver)
        except Exception:
            pass


__all__ = [k for k in list(globals().keys()) if not k.startswith("__")]
