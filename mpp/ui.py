# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Media Platform (Studio Master v1.0.0) — Ventana Principal y Coordinador UI (GPLv3+)
# Este archivo es software libre distribuido bajo la licencia GNU GPL v3.0 o posterior.
from .core import *
from .i18n import *
from .workers import *
from .themes import *
from PySide6.QtWidgets import QSizePolicy
from .views import (
    build_option_subcard,
    wrap_page_in_scroll,
    _build_option_subcard,
    _wrap_page_in_scroll,
    build_capturer_view,
    build_queue_view,
    create_queue_progress_bar,
    set_queue_bar_completed,
    build_library_view,
    build_ffmpeg_lab_view,
    build_settings_view,
    build_security_view,
)


class SelectionDialog(QDialog):
    def __init__(self, parent, title: str, subtitle: str, entries: list[dict]):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(860, 540)
        self.entries = entries or []
        self.selected_urls = []

        if parent and hasattr(parent, "_active_ergonomic_theme"):
            self.setStyleSheet(ErgonomicThemeEngine.build_qss(parent._active_ergonomic_theme))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        hdr_card = QFrame()
        hdr_card.setObjectName("PageHeaderBar")
        hdr_lay = QVBoxLayout(hdr_card)
        hdr_lay.setContentsMargins(16, 12, 16, 12)
        hdr_lay.setSpacing(3)
        lbl_h = QLabel(title)
        lbl_h.setObjectName("PageHeaderTitle")
        lbl_s = QLabel(subtitle)
        lbl_s.setObjectName("PageHeaderDesc")
        hdr_lay.addWidget(lbl_h)
        hdr_lay.addWidget(lbl_s)
        layout.addWidget(hdr_card)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)
        self.input_filter = QLineEdit()
        self.input_filter.setPlaceholderText(tr("selection.filter_placeholder"))
        self.input_filter.setMinimumHeight(34)
        self.input_filter.textChanged.connect(self._filter_rows)
        top_bar.addWidget(self.input_filter, stretch=1)

        btn_all = QPushButton(tr("selection.btn_all"))
        btn_all.setMinimumHeight(34)
        btn_all.clicked.connect(lambda: self._set_all_checked(True))
        top_bar.addWidget(btn_all)

        btn_none = QPushButton(tr("selection.btn_none"))
        btn_none.setMinimumHeight(34)
        btn_none.clicked.connect(lambda: self._set_all_checked(False))
        top_bar.addWidget(btn_none)

        layout.addLayout(top_bar)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            tr("selection.col_choose"),
            tr("selection.col_title"),
            tr("selection.col_duration"),
            tr("selection.col_channel"),
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 68)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table, stretch=1)

        self._populate()

        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)
        bottom_bar.addStretch()

        btn_cancel = QPushButton(tr("action.cancel"))
        btn_cancel.setMinimumHeight(36)
        btn_cancel.clicked.connect(self.reject)
        bottom_bar.addWidget(btn_cancel)

        self.btn_confirm = QPushButton(tr("selection.btn_confirm"))
        self.btn_confirm.setMinimumHeight(36)
        self.btn_confirm.setObjectName("AccentButton")
        self.btn_confirm.clicked.connect(self._confirm)
        bottom_bar.addWidget(self.btn_confirm)

        layout.addLayout(bottom_bar)

    def _populate(self):
        self.table.setRowCount(0)
        for item in self.entries:
            row = self.table.rowCount()
            self.table.insertRow(row)

            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk_item.setCheckState(Qt.Checked)
            chk_item.setData(Qt.UserRole, item.get("url", ""))
            self.table.setItem(row, 0, chk_item)

            self.table.setItem(row, 1, QTableWidgetItem(str(item.get("title", "Sin título"))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get("duration", "—"))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get("channel", "Web"))))

    def _filter_rows(self, text: str):
        q = text.lower().strip()
        for r in range(self.table.rowCount()):
            t = (self.table.item(r, 1).text() if self.table.item(r, 1) else "").lower()
            c = (self.table.item(r, 3).text() if self.table.item(r, 3) else "").lower()
            self.table.setRowHidden(r, bool(q and q not in t and q not in c))

    def _set_all_checked(self, state: bool):
        chk = Qt.Checked if state else Qt.Unchecked
        for r in range(self.table.rowCount()):
            if not self.table.isRowHidden(r):
                item = self.table.item(r, 0)
                if item:
                    item.setCheckState(chk)

    def _confirm(self):
        urls = []
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.checkState() == Qt.Checked:
                u = item.data(Qt.UserRole)
                if u:
                    urls.append(u)
        if not urls:
            QMessageBox.warning(self, tr("dialog.notice_title"), tr("selection.warn_empty"))
            return
        self.selected_urls = urls
        self.accept()


class MainWindow(QMainWindow):
    APP_VERSION = "1.0.0"

    PAGE_META_KEYS = [
        ("capture", "nav.capture", "nav.capture_desc"),
        ("queue", "nav.queue", "nav.queue_desc"),
        ("library", "nav.library", "nav.library_desc"),
        ("ffmpeg", "nav.ffmpeg", "nav.ffmpeg_desc"),
        ("settings", "nav.settings", "nav.settings_desc"),
        ("security", "nav.security", "nav.security_desc"),
        ("theme", "nav.theme", "nav.theme_desc"),
    ]

    def __init__(self, check_updates_on_start: bool = True):
        super().__init__()
        self.settings = SettingsManager()
        self.settings_mgr = self.settings
        self.language = str(self.settings.data.get("language") or get_language())
        set_language(self.language)

        self.setWindowTitle(tr("app.title", version=self.APP_VERSION))
        self.resize(1280, 860)
        self.setMinimumSize(1020, 680)
        self.setAcceptDrops(True)

        theme_dict, _ = ErgonomicThemeEngine.load_state(self.settings)
        self._active_ergonomic_theme = dict(theme_dict)

        self.icon_path = get_resource_path("icono.ico")
        if self.icon_path:
            self.setWindowIcon(QIcon(self.icon_path))
        else:
            self.setWindowIcon(QIcon(ErgonomicThemeEngine.build_vector_app_pixmap(64)))

        self.media_core = MediaCore()
        self.db = DatabaseManager()
        self.workers = {}
        self.task_info = {}
        self.download_dir = self.settings.data["download_dir"]
        self.dark_mode = self.settings.data["dark_mode"]
        self.simple_mode = bool(self.settings.data.get("simple_mode", True))
        self.last_clipboard = ""
        self._force_quit = False
        self._capturer_advanced_widgets = []

        self._build_ui()
        self._load_saved_state()
        self._setup_reactive_ux_rules()
        self._setup_tray_icon()
        self._check_ffmpeg_availability()
        self.apply_theme()
        self.retranslate_ui()
        self.refresh_library()
        self.refresh_diagnostics()

        self.clip_timer = QTimer(self)
        self.clip_timer.timeout.connect(self._check_clipboard)
        self.clip_timer.start(1500)

        if check_updates_on_start:
            QTimer.singleShot(400, self._start_startup_engine_check)

    def _check_ffmpeg_availability(self) -> bool:
        """Verifica al iniciar si FFmpeg está disponible (en portable_data/ o en el PATH del sistema)."""
        has_ff = bool(self.media_core.ffmpeg_path or shutil.which("ffmpeg"))
        if hasattr(self, "ffmpeg_warning_banner") and self.ffmpeg_warning_banner is not None:
            self.lbl_ffmpeg_warning.setText(tr("header.ffmpeg_missing"))
            self.ffmpeg_warning_banner.setVisible(not has_ff)
        return has_ff

    def _setup_tray_icon(self):
        self.tray = QSystemTrayIcon(self)
        if self.icon_path:
            self.tray.setIcon(QIcon(self.icon_path))
        else:
            self.tray.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay))

        tray_menu = QMenu(self)
        self.act_tray_show = QAction(tr("tray.show"), self)
        self.act_tray_pause = QAction(tr("tray.pause_all"), self)
        self.act_tray_resume = QAction(tr("tray.resume_all"), self)
        self.act_tray_quit = QAction(tr("tray.quit"), self)

        self.act_tray_show.triggered.connect(self._restore_from_tray)
        self.act_tray_pause.triggered.connect(self.pause_all_tasks)
        self.act_tray_resume.triggered.connect(self.resume_all_tasks)
        self.act_tray_quit.triggered.connect(self.quit_application)

        tray_menu.addAction(self.act_tray_show)
        tray_menu.addSeparator()
        tray_menu.addAction(self.act_tray_pause)
        tray_menu.addAction(self.act_tray_resume)
        tray_menu.addSeparator()
        tray_menu.addAction(self.act_tray_quit)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(lambda reason: self._restore_from_tray() if reason == QSystemTrayIcon.Trigger else None)
        self.tray.show()

    def _restore_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def _has_active_tasks(self) -> bool:
        """Comprueba si hay descargas, conversiones FFmpeg o subprocesos hijos activos."""
        if any(w and w.isRunning() for w in self.workers.values()):
            return True
        for attr in ("ffmpeg_worker", "update_worker", "rollback_worker", "trans_worker"):
            w_aux = getattr(self, attr, None)
            if w_aux and w_aux.isRunning():
                return True
        if ProcessAndThreadRegistry.active_subprocesses():
            return True
        return False

    def _stop_all_workers_safely(self):
        """Cancela ordenadamente todos los QThreads activos, mata subprocesos hijos FFmpeg y espera su cierre."""
        aux_list = [
            getattr(self, attr, None)
            for attr in ("ffmpeg_worker", "analyzer", "sniffer", "trans_worker", "probe_worker", "update_worker", "rollback_worker", "ver_check_worker")
        ]
        all_threads = list(self.workers.values()) + [w for w in aux_list if w is not None]
        ProcessAndThreadRegistry.shutdown_all(extra_threads=all_threads, wait_ms=1200)
        for w in list(self.workers.values()):
            if w is not None:
                try:
                    w.cleanup_partials()
                except Exception:
                    pass

    def quit_application(self):
        self._force_quit = True
        self.close()

    def closeEvent(self, event: QCloseEvent):
        self.save_current_settings()
        has_active = self._has_active_tasks()

        if not self._force_quit and self.chk_tray.isChecked() and not has_active:
            event.ignore()
            self.hide()
            self.tray.showMessage(
                tr("tray.minimized_title"),
                tr("tray.minimized_msg"),
                QSystemTrayIcon.Information, 3000
            )
            return

        if has_active:
            ans = QMessageBox.question(
                self,
                tr("close.active_title"),
                tr("close.active_msg"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if ans != QMessageBox.Yes:
                self._force_quit = False
                event.ignore()
                return

        self._stop_all_workers_safely()
        self.tray.hide()
        event.accept()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() or event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        text = event.mimeData().text().strip()
        if text:
            self.url_input.setText(text)
            self.analyze_url()

    def _check_clipboard(self):
        if not self.chk_clip_monitor.isChecked():
            return
        text = QApplication.clipboard().text().strip()
        if text != self.last_clipboard and text.startswith(("http://", "https://")) and " " not in text:
            self.last_clipboard = text
            self.url_input.setText(text)

    def _refresh_sidebar_icons(self):
        if not hasattr(self, "nav_list") or self.nav_list is None:
            return
        t = getattr(self, "_active_ergonomic_theme", {})
        accent_hex = t.get("accent_hover", "#E64955")
        muted_hex = t.get("text_muted", "#C4B5A5")
        curr_row = self.nav_list.currentRow()
        for idx, (icon_kind, _, _) in enumerate(self.PAGE_META_KEYS):
            item = self.nav_list.item(idx)
            if item:
                is_active = (idx == curr_row)
                col_hex = accent_hex if is_active else muted_hex
                item.setIcon(ErgonomicThemeEngine.build_nav_icon(icon_kind, col_hex, 20, active=is_active))

    # ==========================================================================
    # INTERNACIONALIZACIÓN (EN / ES), MODO SIMPLE / AVANZADO Y AUTO-ACTUALIZADOR
    # ==========================================================================
    def set_app_language(self, lang_code: str, persist: bool = True):
        """Cambia el idioma activo (en / es), actualiza todos los textos en vivo y guarda en settings.json."""
        norm = set_language(lang_code)
        self.language = norm
        for cmb in (getattr(self, "combo_header_lang", None), getattr(self, "combo_language", None)):
            if cmb is not None:
                cmb.blockSignals(True)
                idx = cmb.findData(norm)
                if idx >= 0:
                    cmb.setCurrentIndex(idx)
                cmb.blockSignals(False)
        self.retranslate_ui()
        if persist:
            self.settings.save({"language": norm})

    def retranslate_ui(self):
        """Actualiza dinámicamente todos los textos de la interfaz según el idioma seleccionado."""
        self.setWindowTitle(tr("app.title", version=self.APP_VERSION))
        if hasattr(self, "lbl_nav_header"):
            self.lbl_nav_header.setText(tr("sidebar.workspace"))
        if hasattr(self, "btn_theme"):
            self.btn_theme.setText(tr("sidebar.toggle_theme"))
            self.btn_theme.setToolTip(tr("sidebar.toggle_theme_tip"))

        for idx, (_, t_key, d_key) in enumerate(self.PAGE_META_KEYS):
            item = self.nav_list.item(idx) if hasattr(self, "nav_list") else None
            if item:
                if idx == 1:
                    self._update_queue_nav_title()
                else:
                    item.setText(tr(t_key))
                item.setToolTip(tr(d_key))

        curr_idx = self.nav_list.currentRow() if hasattr(self, "nav_list") else 0
        if 0 <= curr_idx < len(self.PAGE_META_KEYS):
            _, t_key, d_key = self.PAGE_META_KEYS[curr_idx]
            self.lbl_page_title.setText(tr(t_key))
            self.lbl_page_desc.setText(tr(d_key))

        if hasattr(self, "btn_mode_simple"):
            self.btn_mode_simple.setText(tr("mode.simple"))
            self.btn_mode_simple.setToolTip(tr("mode.simple_tip"))
        if hasattr(self, "btn_mode_studio"):
            self.btn_mode_studio.setText(tr("mode.advanced"))
            self.btn_mode_studio.setToolTip(tr("mode.advanced_tip"))

        if hasattr(self, "lbl_ffmpeg_warning"):
            self.lbl_ffmpeg_warning.setText(tr("header.ffmpeg_missing"))

        if hasattr(self, "url_input"):
            self.url_input.setPlaceholderText(tr("omnibar.placeholder"))
        if hasattr(self, "btn_paste"):
            self.btn_paste.setText(tr("omnibar.paste"))
            self.btn_paste.setToolTip(tr("omnibar.paste_tip"))
        if hasattr(self, "btn_analyze") and self.btn_analyze.isEnabled():
            self.btn_analyze.setText(tr("omnibar.inspect"))
            self.btn_analyze.setToolTip(tr("omnibar.inspect_tip"))
        if hasattr(self, "btn_sniffer") and self.btn_sniffer.isEnabled():
            self.btn_sniffer.setText(tr("omnibar.sniffer"))
            self.btn_sniffer.setToolTip(tr("omnibar.sniffer_tip"))
        if hasattr(self, "btn_transcript") and self.btn_transcript.isEnabled():
            self.btn_transcript.setText(tr("omnibar.transcript"))
            self.btn_transcript.setToolTip(tr("omnibar.transcript_tip"))
        if hasattr(self, "btn_add_queue"):
            self.btn_add_queue.setText(tr("omnibar.download"))
            self.btn_add_queue.setToolTip(tr("omnibar.download_tip"))

        # Vista Capturador
        if hasattr(self, "insp_card"):
            self.insp_card.set_texts(tr("capture.insp_title"), tr("capture.insp_sub"))
            if hasattr(self, "lbl_meta_title") and getattr(self, "_hero_is_idle", True):
                self.lbl_meta_title.setText(tr("capture.hero_idle"))
            if hasattr(self, "lbl_thumbnail"):
                pm_thumb = self.lbl_thumbnail.pixmap()
                if pm_thumb is None or pm_thumb.isNull():
                    self.lbl_thumbnail.setText(tr("capture.no_preview"))
        if hasattr(self, "card_platform"):
            self.card_platform.lbl_title.setText(tr("capture.tile_origin"))
            self.card_duration.lbl_title.setText(tr("capture.tile_duration"))
            self.card_res.lbl_title.setText(tr("capture.tile_res"))
            self.card_hdr.lbl_title.setText(tr("capture.tile_hdr"))
            self.card_codecs.lbl_title.setText(tr("capture.tile_codecs"))
            self.card_subs.lbl_title.setText(tr("capture.tile_subs"))
            self.card_size.lbl_title.setText(tr("capture.tile_size"))
            self.card_rec.lbl_title.setText(tr("capture.tile_rec"))
        if hasattr(self, "sub_fmt_card"):
            self.sub_fmt_card.setTitle(tr("capture.sub_fmt_title"))
            self.lbl_quality.setText(tr("capture.lbl_quality"))
            if hasattr(self, "combo_quality") and hasattr(self, "_quality_option_keys"):
                self.combo_quality.blockSignals(True)
                for idx_q, (_canon_q, q_tr_key) in enumerate(self._quality_option_keys):
                    if idx_q < self.combo_quality.count():
                        self.combo_quality.setItemText(idx_q, tr(q_tr_key))
                self.combo_quality.blockSignals(False)
            self.lbl_container.setText(tr("capture.lbl_container"))
            if hasattr(self, "_refresh_container_state"):
                self._refresh_container_state()
            self.lbl_fragments.setText(tr("capture.lbl_fragments"))
            self.chk_playlist.setText(tr("capture.chk_playlist"))
            self.chk_subs.setText(tr("capture.chk_subs"))
            self.chk_embed_subs.setText(tr("capture.chk_embed_subs"))
        if hasattr(self, "sub_sp_card"):
            self.sub_sp_card.setTitle(tr("capture.sub_sp_title"))
            self.chk_sponsorblock.setText(tr("capture.chk_sponsorblock"))
            self.chk_smart_sponsor.setText(tr("capture.chk_smart_sponsor"))
            self.chk_loudnorm.setText(tr("capture.chk_loudnorm"))
            self.chk_thumbnail.setText(tr("capture.chk_thumbnail"))
        if hasattr(self, "sub_proc_card"):
            self.sub_proc_card.setTitle(tr("capture.sub_proc_title"))
            self.chk_trim.setText(tr("capture.chk_trim"))
            self.lbl_trim_to.setText(tr("capture.lbl_trim_to"))
            self.chk_split_chapters.setText(tr("capture.chk_split_chapters"))
            self.chk_live_start.setText(tr("capture.chk_live_start"))
        if hasattr(self, "lbl_save_in"):
            self.lbl_save_in.setText(tr("capture.lbl_save_in"))
            self.btn_ch_dir.setText(tr("capture.btn_change_dir"))
            self.btn_open_dir.setText(tr("capture.btn_open_dir"))

        # Vista Cola
        if hasattr(self, "queue_card"):
            self.queue_card.set_texts(tr("queue.card_title"), tr("queue.card_sub"))
            self.btn_import_txt.setText(tr("queue.btn_import_txt"))
            self.btn_import_clip.setText(tr("queue.btn_paste_batch"))
            self.btn_pause_q.setText(tr("queue.btn_pause"))
            self.btn_resume_q.setText(tr("queue.btn_resume"))
            self.btn_retry_q.setText(tr("queue.btn_retry"))
            if hasattr(self, "btn_force_redownload_q") and self.btn_force_redownload_q is not None:
                self.btn_force_redownload_q.setText(tr("queue.btn_force_redownload"))
                self.btn_force_redownload_q.setToolTip(tr("queue.btn_force_redownload_tip"))
            self.btn_cancel_q.setText(tr("queue.btn_cancel"))
            self.btn_remove_q.setText(tr("queue.btn_remove"))
            self.btn_clear_inactive_q.setText(tr("queue.btn_clear_inactive"))
            self.table_queue.setHorizontalHeaderLabels([
                tr("queue.col_title"),
                tr("queue.col_format"),
                tr("queue.col_progress"),
                tr("queue.col_speed"),
                tr("queue.col_status"),
            ])
            self.lbl_qlog.setText(tr("queue.lbl_log"))
            if hasattr(self, "txt_download_log") and self.txt_download_log is not None:
                self.txt_download_log.setPlaceholderText(tr("queue.log_placeholder"))
            self.btn_clear_log.setText(tr("queue.btn_clear_log"))
            self.lbl_post_action.setText(tr("queue.lbl_post_action"))
            if hasattr(self, "combo_post_action") and hasattr(self, "_post_action_keys"):
                self.combo_post_action.blockSignals(True)
                for idx_p, (_act_id, post_tr_key) in enumerate(self._post_action_keys):
                    if idx_p < self.combo_post_action.count():
                        self.combo_post_action.setItemText(idx_p, tr(post_tr_key))
                self.combo_post_action.blockSignals(False)

        # Vista Videoteca
        if hasattr(self, "lib_card"):
            self.lib_card.set_texts(tr("library.card_title"), tr("library.card_sub"))
            self.input_lib_search.setPlaceholderText(tr("library.search_placeholder"))
            self.btn_play_lib.setText(tr("library.btn_play"))
            self.btn_locate_lib.setText(tr("library.btn_locate"))
            self.btn_del_item_lib.setText(tr("library.btn_delete"))
            self.btn_clear_lib.setText(tr("library.btn_clear"))

        # Vista Laboratorio FFmpeg
        if hasattr(self, "ff_card"):
            self.ff_card.set_texts(tr("ffmpeg.card_title"), tr("ffmpeg.card_sub"))
            self.sub_ff_card.setTitle(tr("ffmpeg.sub_params"))
            self.lbl_ff_in.setText(tr("ffmpeg.lbl_input"))
            self.input_ff_in.setPlaceholderText(tr("ffmpeg.input_placeholder"))
            self.btn_ff_browse.setText(tr("ffmpeg.btn_browse"))
            self.btn_ff_browse.setToolTip(tr("ffmpeg.btn_browse_tip"))
            self.lbl_ff_op.setText(tr("ffmpeg.lbl_op"))
            if hasattr(self, "combo_ff_op") and hasattr(self, "_ff_op_keys"):
                self.combo_ff_op.blockSignals(True)
                for idx_op, (_op_code, op_tr_key) in enumerate(self._ff_op_keys):
                    if idx_op < self.combo_ff_op.count():
                        self.combo_ff_op.setItemText(idx_op, tr(op_tr_key))
                self.combo_ff_op.blockSignals(False)
            self.lbl_ff_hw.setText(tr("ffmpeg.lbl_hw"))
            if self.btn_run_ff.isEnabled() and not (getattr(self, "ffmpeg_worker", None) and self.ffmpeg_worker.isRunning()):
                self.btn_run_ff.setText(tr("ffmpeg.btn_run"))
            self.lbl_probe_hdr.setText(tr("ffmpeg.lbl_console"))
            self.txt_ffprobe.setPlaceholderText(tr("ffmpeg.console_placeholder"))

        # Vista Ajustes y Red
        if hasattr(self, "org_card"):
            self.org_card.set_texts(tr("settings.org_title"), tr("settings.org_sub"))
            self.lbl_lang_setting.setText(tr("settings.lbl_language"))
            self.lbl_tpl_setting.setText(tr("settings.lbl_template"))
            self.chk_auto_org.setText(tr("settings.chk_auto_org"))
            self.chk_skip_dup.setText(tr("settings.chk_skip_dup"))
            if hasattr(self, "chk_overwrite_existing") and self.chk_overwrite_existing is not None:
                self.chk_overwrite_existing.setText(tr("settings.chk_overwrite_existing"))
                self.chk_overwrite_existing.setToolTip(tr("settings.chk_overwrite_existing_tip"))
            self.chk_clip_monitor.setText(tr("settings.chk_clip_monitor"))
            self.chk_tray.setText(tr("settings.chk_tray"))
            self.net_card.set_texts(tr("settings.net_title"), tr("settings.net_sub"))
            self.lbl_conc_setting.setText(tr("settings.lbl_concurrent"))
            self.lbl_spd_setting.setText(tr("settings.lbl_speed"))
            self.lbl_prx_setting.setText(tr("settings.lbl_proxy"))
            self.lbl_ckb_setting.setText(tr("settings.lbl_cookies_browser"))
            self.lbl_cf_setting.setText(tr("settings.lbl_cookies_file"))
            self.btn_browse_cf.setText(tr("ffmpeg.btn_browse"))
            self.btn_clear_cf.setText(tr("settings.btn_clear"))
            self.priv_card.set_texts(tr("settings.priv_title"))
            self.chk_privacy.setText(tr("settings.chk_privacy"))

        # Vista Seguridad
        if hasattr(self, "sec_card"):
            self.sec_card.set_texts(tr("security.card_title"), tr("security.card_sub"))
            if hasattr(self, "chk_auto_update_engine"):
                self.chk_auto_update_engine.setText(tr("security.chk_auto_update"))
            if self.btn_update_yt.isEnabled():
                self.btn_update_yt.setText(tr("security.btn_update_yt"))
            self.btn_update_yt.setToolTip(tr("security.btn_update_yt_tip"))
            if hasattr(self, "btn_rollback_yt"):
                rb_running = getattr(self, "rollback_worker", None) and self.rollback_worker.isRunning()
                if not rb_running:
                    self.btn_rollback_yt.setText(tr("security.btn_rollback_yt"))
                self.btn_rollback_yt.setToolTip(tr("security.btn_rollback_yt_tip"))
            self.btn_refresh_diag.setText(tr("security.btn_refresh"))
            self.btn_about_gpl.setText(tr("security.btn_about"))
            self.gpl_card.set_texts(tr("security.gpl_title"), tr("security.gpl_sub"))
            if hasattr(self, "lbl_gpl_info") and self.lbl_gpl_info is not None:
                self.lbl_gpl_info.setText(tr("security.gpl_body"))
            if hasattr(self, "txt_diag") and self.txt_diag is not None:
                self.refresh_diagnostics()

        if hasattr(self, "act_tray_show"):
            self.act_tray_show.setText(tr("tray.show"))
            self.act_tray_pause.setText(tr("tray.pause_all"))
            self.act_tray_resume.setText(tr("tray.resume_all"))
            self.act_tray_quit.setText(tr("tray.quit"))

        if hasattr(self, "_retranslate_customizer") and callable(self._retranslate_customizer):
            self._retranslate_customizer()

        self.set_ui_mode(self.simple_mode, persist=False)
        self.update_disk_space()
        self._update_queue_nav_title()

    def set_ui_mode(self, simple: bool, persist: bool = True):
        """Alterna entre 'Modo Simple' (interfaz limpia para principiantes) y 'Modo Avanzado' (completo)."""
        self.simple_mode = bool(simple)
        if hasattr(self, "btn_mode_simple") and self.btn_mode_simple is not None:
            self.btn_mode_simple.blockSignals(True)
            self.btn_mode_studio.blockSignals(True)
            self.btn_mode_simple.setChecked(self.simple_mode)
            self.btn_mode_studio.setChecked(not self.simple_mode)
            self.btn_mode_simple.blockSignals(False)
            self.btn_mode_studio.blockSignals(False)

        for w in getattr(self, "_capturer_advanced_widgets", []):
            if w is not None:
                w.setVisible(not self.simple_mode)

        for aux_btn in (getattr(self, "btn_sniffer", None), getattr(self, "btn_transcript", None)):
            if aux_btn is not None:
                aux_btn.setVisible(not self.simple_mode)

        if hasattr(self, "cfg_card") and self.cfg_card is not None:
            self.cfg_card.set_texts(
                tr("capture.cfg_title_simple") if self.simple_mode else tr("capture.cfg_title_adv"),
                tr("capture.cfg_sub_simple") if self.simple_mode else tr("capture.cfg_sub_adv"),
            )

        if persist:
            self.settings.save({"simple_mode": self.simple_mode})

    def toggle_ui_mode(self):
        self.set_ui_mode(not self.simple_mode, persist=True)

    def _start_startup_engine_check(self):
        """Ejecuta en segundo plano una comprobación silenciosa de versión de yt-dlp en PyPI."""
        if getattr(self, "ver_check_worker", None) and self.ver_check_worker.isRunning():
            return
        self.ver_check_worker = EngineVersionCheckWorker(self)
        self.ver_check_worker.update_available_signal.connect(self.on_engine_update_available)
        self.ver_check_worker.finished.connect(self.ver_check_worker.deleteLater)
        self.ver_check_worker.start()

    def on_engine_update_available(self, curr_ver: str, latest_ver: str):
        auto_upd = bool(
            self.chk_auto_update_engine.isChecked()
            if hasattr(self, "chk_auto_update_engine") and self.chk_auto_update_engine is not None
            else self.settings.data.get("auto_update_engine", True)
        )
        if auto_upd:
            if hasattr(self, "txt_diag") and self.txt_diag is not None:
                self.txt_diag.append(
                    f"\n[Auto-Update] Detectada nueva versión yt-dlp {latest_ver} (actual: {curr_ver}). "
                    "Iniciando actualización segura en segundo plano..."
                )
            self.update_ytdlp_engine(auto_triggered=True)
            return

        if hasattr(self, "update_banner_frame") and self.update_banner_frame is not None:
            self.lbl_update_notice.setText(tr("header.update_available", version=latest_ver))
            self.lbl_update_notice.setToolTip(f"Installed: {curr_ver} → PyPI: {latest_ver}")
            self.btn_quick_update_yt.setEnabled(True)
            self.btn_quick_update_yt.setText(tr("header.update_btn"))
            self.update_banner_frame.setVisible(True)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Barra Lateral de Navegación ──
        sidebar = DragonForgeSidebarFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(248)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 18, 12, 16)
        side_layout.setSpacing(10)

        brand_box = QHBoxLayout()
        brand_box.setSpacing(9)
        self.lbl_brand_icon = QLabel()
        self.lbl_brand_icon.setFixedSize(54, 54)
        self.lbl_brand_icon.setPixmap(
            ErgonomicThemeEngine.build_vector_app_pixmap(
                54,
                str(self._active_ergonomic_theme.get("accent", "#C82333")),
                str(self._active_ergonomic_theme.get("border_gold", self._active_ergonomic_theme.get("gold", "#D4AF37"))),
            )
        )

        brand_text_layout = QVBoxLayout()
        brand_text_layout.setSpacing(1)
        lbl_title = QLabel(tr("brand.title"))
        lbl_title.setObjectName("BrandTitle")
        lbl_sub = QLabel(tr("brand.subtitle", version=self.APP_VERSION))
        lbl_sub.setObjectName("BrandSub")
        brand_text_layout.addWidget(lbl_title)
        brand_text_layout.addWidget(lbl_sub)

        brand_box.addWidget(self.lbl_brand_icon)
        brand_box.addLayout(brand_text_layout, stretch=1)
        side_layout.addLayout(brand_box)

        side_layout.addSpacing(8)

        self.lbl_nav_header = QLabel(tr("sidebar.workspace"))
        self.lbl_nav_header.setObjectName("SidebarSection")
        side_layout.addWidget(self.lbl_nav_header)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("NavList")
        self.nav_list.setIconSize(QSize(20, 20))
        self.nav_list.setSpacing(2)
        for icon_kind, t_key, d_key in self.PAGE_META_KEYS:
            item = QListWidgetItem(tr(t_key))
            item.setSizeHint(QSize(214, 40))
            item.setToolTip(tr(d_key))
            item.setIcon(ErgonomicThemeEngine.build_nav_icon(icon_kind, "#C4B1B4", 20))
            self.nav_list.addItem(item)
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        side_layout.addWidget(self.nav_list, stretch=1)

        disk_frame = DragonForgeFooterFrame()
        disk_frame.setObjectName("SidebarFooterCard")
        d_layout = QVBoxLayout(disk_frame)
        d_layout.setContentsMargins(12, 10, 12, 10)
        d_layout.setSpacing(6)

        self.lbl_disk = QLabel(tr("sidebar.storage"))
        self.lbl_disk.setObjectName("DiskLabel")
        self.bar_disk = QProgressBar()
        self.bar_disk.setFixedHeight(20)
        self.bar_disk.setTextVisible(False)
        self.bar_disk.setProperty("hasProgress", False)
        self.bar_disk._has_prog_state = False
        d_layout.addWidget(self.lbl_disk)
        d_layout.addWidget(self.bar_disk)
        side_layout.addWidget(disk_frame)

        self.btn_theme = QPushButton(tr("sidebar.toggle_theme"))
        self.btn_theme.setMinimumHeight(34)
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.setToolTip(tr("sidebar.toggle_theme_tip"))
        self.btn_theme.clicked.connect(self.toggle_theme)
        side_layout.addWidget(self.btn_theme)

        root_layout.addWidget(sidebar)

        # ── Área Principal de Trabajo ──
        workspace = QWidget()
        work_layout = QVBoxLayout(workspace)
        work_layout.setContentsMargins(20, 14, 20, 14)
        work_layout.setSpacing(10)

        # Cabecera Superior Contextual + Selector Idioma + Selector Modo Simple / Modo Avanzado
        self.page_header_bar = QFrame()
        self.page_header_bar.setObjectName("PageHeaderBar")
        ph_layout = QHBoxLayout(self.page_header_bar)
        ph_layout.setContentsMargins(14, 8, 14, 8)
        ph_layout.setSpacing(10)

        ph_text_col = QVBoxLayout()
        ph_text_col.setSpacing(2)
        self.lbl_page_title = QLabel(tr(self.PAGE_META_KEYS[0][1]))
        self.lbl_page_title.setObjectName("PageHeaderTitle")
        self.lbl_page_desc = QLabel(tr(self.PAGE_META_KEYS[0][2]))
        self.lbl_page_desc.setObjectName("PageHeaderDesc")
        self.lbl_page_desc.setWordWrap(True)
        self.lbl_page_desc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        ph_text_col.addWidget(self.lbl_page_title)
        ph_text_col.addWidget(self.lbl_page_desc)
        ph_layout.addLayout(ph_text_col, stretch=1)

        # Aviso discreto de nueva versión de yt-dlp (oculto por defecto hasta que haya actualización)
        self.update_banner_frame = QFrame()
        self.update_banner_frame.setObjectName("UpdateBanner")
        ub_lay = QHBoxLayout(self.update_banner_frame)
        ub_lay.setContentsMargins(8, 3, 8, 3)
        ub_lay.setSpacing(6)
        self.lbl_update_notice = QLabel(tr("header.update_available", version=""))
        self.lbl_update_notice.setObjectName("UpdateBannerLabel")
        self.btn_quick_update_yt = QPushButton(tr("header.update_btn"))
        self.btn_quick_update_yt.setObjectName("BtnUpdateBanner")
        self.btn_quick_update_yt.setCursor(Qt.PointingHandCursor)
        self.btn_quick_update_yt.setToolTip("Actualiza el motor yt-dlp en caliente verificando su hash SHA-256")
        self.btn_quick_update_yt.clicked.connect(self.update_ytdlp_engine)
        ub_lay.addWidget(self.lbl_update_notice)
        ub_lay.addWidget(self.btn_quick_update_yt)
        self.update_banner_frame.setVisible(False)
        ph_layout.addWidget(self.update_banner_frame)

        # Selector rápido de idioma en la cabecera superior (English / Español)
        self.combo_header_lang = QComboBox()
        self.combo_header_lang.setMinimumHeight(30)
        self.combo_header_lang.setFixedWidth(128)
        self.combo_header_lang.addItem("English", "en")
        self.combo_header_lang.addItem("Español", "es")
        idx_hl = self.combo_header_lang.findData(get_language())
        if idx_hl >= 0:
            self.combo_header_lang.setCurrentIndex(idx_hl)
        self.combo_header_lang.currentIndexChanged.connect(
            lambda _i: self.set_app_language(self.combo_header_lang.currentData(), persist=True)
        )
        ph_layout.addWidget(self.combo_header_lang)

        # Interruptor "Modo Simple" / "Modo Avanzado"
        self.mode_toggle_frame = QFrame()
        self.mode_toggle_frame.setObjectName("ModeToggleFrame")
        mt_lay = QHBoxLayout(self.mode_toggle_frame)
        mt_lay.setContentsMargins(3, 2, 3, 2)
        mt_lay.setSpacing(2)

        self.btn_mode_simple = QPushButton(tr("mode.simple"))
        self.btn_mode_simple.setObjectName("ModeSwitchBtn")
        self.btn_mode_simple.setCheckable(True)
        self.btn_mode_simple.setCursor(Qt.PointingHandCursor)
        self.btn_mode_simple.setToolTip(tr("mode.simple_tip"))
        self.btn_mode_simple.clicked.connect(lambda: self.set_ui_mode(True, persist=True))

        self.btn_mode_studio = QPushButton(tr("mode.advanced"))
        self.btn_mode_studio.setObjectName("ModeSwitchBtn")
        self.btn_mode_studio.setCheckable(True)
        self.btn_mode_studio.setCursor(Qt.PointingHandCursor)
        self.btn_mode_studio.setToolTip(tr("mode.advanced_tip"))
        self.btn_mode_studio.clicked.connect(lambda: self.set_ui_mode(False, persist=True))
        self.btn_mode_advanced = self.btn_mode_studio

        mt_lay.addWidget(self.btn_mode_simple)
        mt_lay.addWidget(self.btn_mode_studio)
        ph_layout.addWidget(self.mode_toggle_frame)

        self.lbl_queue_summary_badge = QLabel(tr("header.queue_idle"))
        self.lbl_queue_summary_badge.setObjectName("StatusBadge")
        self.lbl_queue_summary_badge.setProperty("headerSummary", True)
        self.lbl_queue_summary_badge.setProperty("statusKind", "queued")
        self.lbl_queue_summary_badge.setAlignment(Qt.AlignCenter)
        ph_layout.addWidget(self.lbl_queue_summary_badge)

        work_layout.addWidget(self.page_header_bar)

        # Aviso en cabecera si FFmpeg no está instalado
        self.ffmpeg_warning_banner = QFrame()
        self.ffmpeg_warning_banner.setObjectName("FFmpegWarningBanner")
        ffw_lay = QHBoxLayout(self.ffmpeg_warning_banner)
        ffw_lay.setContentsMargins(12, 6, 12, 6)
        self.lbl_ffmpeg_warning = QLabel(tr("header.ffmpeg_missing"))
        self.lbl_ffmpeg_warning.setObjectName("FFmpegWarningLabel")
        self.lbl_ffmpeg_warning.setWordWrap(True)
        ffw_lay.addWidget(self.lbl_ffmpeg_warning, 1)
        self.ffmpeg_warning_banner.setVisible(False)
        work_layout.addWidget(self.ffmpeg_warning_banner)

        # Barra de Entrada / Búsqueda Global (OmniBar)
        omnibar = QFrame()
        omnibar.setObjectName("OmniBar")
        omni_layout = QHBoxLayout(omnibar)
        omni_layout.setContentsMargins(12, 8, 12, 8)
        omni_layout.setSpacing(8)

        self.url_input = QLineEdit()
        self.url_input.setObjectName("UrlInput")
        self.url_input.setPlaceholderText(tr("omnibar.placeholder"))
        self.url_input.setMinimumHeight(36)
        self.url_input.returnPressed.connect(self.analyze_url)
        omni_layout.addWidget(self.url_input, stretch=1)

        self.btn_paste = QPushButton(tr("omnibar.paste"))
        self.btn_paste.setObjectName("OmniActionBtn")
        self.btn_paste.setMinimumHeight(36)
        self.btn_paste.setCursor(Qt.PointingHandCursor)
        self.btn_paste.setToolTip(tr("omnibar.paste_tip"))
        self.btn_paste.clicked.connect(self.paste_clipboard)
        omni_layout.addWidget(self.btn_paste)

        self.btn_analyze = QPushButton(tr("omnibar.inspect"))
        self.btn_analyze.setObjectName("OmniActionBtn")
        self.btn_analyze.setMinimumHeight(36)
        self.btn_analyze.setCursor(Qt.PointingHandCursor)
        self.btn_analyze.setToolTip(tr("omnibar.inspect_tip"))
        self.btn_analyze.clicked.connect(self.analyze_url)
        omni_layout.addWidget(self.btn_analyze)

        self.btn_sniffer = QPushButton(tr("omnibar.sniffer"))
        self.btn_sniffer.setObjectName("OmniActionBtn")
        self.btn_sniffer.setMinimumHeight(36)
        self.btn_sniffer.setCursor(Qt.PointingHandCursor)
        self.btn_sniffer.setToolTip(tr("omnibar.sniffer_tip"))
        self.btn_sniffer.clicked.connect(self.run_web_sniffer)
        omni_layout.addWidget(self.btn_sniffer)

        self.btn_transcript = QPushButton(tr("omnibar.transcript"))
        self.btn_transcript.setObjectName("OmniActionBtn")
        self.btn_transcript.setMinimumHeight(36)
        self.btn_transcript.setCursor(Qt.PointingHandCursor)
        self.btn_transcript.setToolTip(tr("omnibar.transcript_tip"))
        self.btn_transcript.clicked.connect(self.extract_clean_transcript)
        omni_layout.addWidget(self.btn_transcript)

        self.btn_add_queue = QPushButton(tr("omnibar.download"))
        self.btn_add_queue.setMinimumHeight(36)
        self.btn_add_queue.setMinimumWidth(118)
        self.btn_add_queue.setObjectName("AccentButton")
        self.btn_add_queue.setCursor(Qt.PointingHandCursor)
        self.btn_add_queue.setToolTip(tr("omnibar.download_tip"))
        btn_glow = QGraphicsDropShadowEffect(self.btn_add_queue)
        btn_glow.setBlurRadius(18)
        btn_glow.setOffset(0, 3)
        btn_glow.setColor(QColor(245, 158, 11, 165))
        self.btn_add_queue.setGraphicsEffect(btn_glow)
        self.btn_add_queue.clicked.connect(self.enqueue_current_url)
        omni_layout.addWidget(self.btn_add_queue)

        work_layout.addWidget(omnibar)

        self.pages = QStackedWidget()
        work_layout.addWidget(self.pages, stretch=1)

        self._build_page_capture()
        self._build_page_queue()
        self._build_page_library()
        self._build_page_ffmpeg()
        self._build_page_settings()
        self._build_page_security()
        self.pages.addWidget(ErgonomicThemeEngine.build_customizer_page(self))

        root_layout.addWidget(workspace, stretch=1)
        self._refresh_sidebar_icons()
        self.update_disk_space()

    def on_nav_changed(self, index):
        if 0 <= index < self.pages.count():
            self.pages.setCurrentIndex(index)
        if 0 <= index < len(self.PAGE_META_KEYS):
            _, t_key, d_key = self.PAGE_META_KEYS[index]
            self.lbl_page_title.setText(tr(t_key))
            self.lbl_page_desc.setText(tr(d_key))
        self._refresh_sidebar_icons()

    def _build_page_capture(self):
        self.pages.addWidget(build_capturer_view(self))

    def _build_page_queue(self):
        self.pages.addWidget(build_queue_view(self))

    def _build_page_library(self):
        self.pages.addWidget(build_library_view(self))

    def _build_page_ffmpeg(self):
        self.pages.addWidget(build_ffmpeg_lab_view(self))

    def _build_page_settings(self):
        self.pages.addWidget(build_settings_view(self))

    def _build_page_security(self):
        self.pages.addWidget(build_security_view(self))

    # ==========================================================================
    # PERSISTENCIA Y CONFIGURACIÓN
    # ==========================================================================
    def _load_saved_state(self):
        d = self.settings.data
        self.input_dir.setText(self.download_dir)
        saved_q = str(d.get("quality", "Mejor Calidad Disponible"))
        idx_q = self.combo_quality.findData(saved_q)
        if idx_q < 0:
            idx_q = self.combo_quality.findText(saved_q)
        if idx_q >= 0:
            self.combo_quality.setCurrentIndex(idx_q)
        else:
            self.combo_quality.setCurrentIndex(0)
        self.combo_container.setCurrentText(d.get("container", "MP4"))
        self.spin_fragments.setValue(int(d.get("fragments", 4)))
        self.spin_max_concurrent.setValue(int(d.get("max_concurrent", 2)))
        self.chk_playlist.setChecked(bool(d.get("allow_playlist", False)))
        self.spin_speed.setValue(int(d.get("speed_limit_kb", 0)))
        self.input_proxy.setText(d.get("proxy", ""))
        self.combo_cookies.setCurrentText(d.get("cookies_browser", "Ninguno"))
        if hasattr(self, "ux_cookies_file_edit") and self.ux_cookies_file_edit is not None:
            self.ux_cookies_file_edit.setText(str(d.get("cookies_file", "")))
        self.input_template.setText(d.get("naming_template", "%(title).100s [%(resolution)s] [%(id)s].%(ext)s"))
        self.chk_auto_org.setChecked(bool(d.get("auto_organize", False)))
        self.chk_skip_dup.setChecked(bool(d.get("skip_duplicates", True)))
        if hasattr(self, "chk_overwrite_existing") and self.chk_overwrite_existing is not None:
            self.chk_overwrite_existing.setChecked(bool(d.get("overwrite_existing", False)))
        self.chk_clip_monitor.setChecked(bool(d.get("clip_monitor", False)))
        self.chk_privacy.setChecked(bool(d.get("privacy_mode", False)))
        self.chk_tray.setChecked(bool(d.get("minimize_to_tray", False)))
        self.chk_thumbnail.setChecked(bool(d.get("embed_thumbnail", False)))
        self.chk_sponsorblock.setChecked(bool(d.get("sponsorblock", False)))
        if hasattr(self, "chk_smart_sponsor"):
            self.chk_smart_sponsor.setChecked(bool(d.get("smart_sponsor", False)))
        self.chk_split_chapters.setChecked(bool(d.get("split_chapters", False)))
        self.chk_live_start.setChecked(bool(d.get("live_from_start", False)))
        self.chk_loudnorm.setChecked(bool(d.get("loudnorm", False)))
        self.combo_sub_langs.setCurrentText(d.get("sub_langs", "Español (España) [es-ES]"))
        self.db.privacy_mode = self.chk_privacy.isChecked()
        if hasattr(self, "chk_auto_update_engine") and self.chk_auto_update_engine is not None:
            self.chk_auto_update_engine.setChecked(bool(d.get("auto_update_engine", True)))
        self.set_app_language(str(d.get("language") or get_language()), persist=False)
        self.set_ui_mode(bool(d.get("simple_mode", True)), persist=False)

    def save_current_settings(self):
        cfile = self.ux_cookies_file_edit.text().strip() if hasattr(self, "ux_cookies_file_edit") and self.ux_cookies_file_edit else ""
        self.settings.save({
            "download_dir": self.download_dir,
            "language": self.language,
            "simple_mode": self.simple_mode,
            "auto_update_engine": self.chk_auto_update_engine.isChecked() if hasattr(self, "chk_auto_update_engine") else True,
            "dark_mode": self.dark_mode,
            "quality": self.combo_quality.currentData() or self.combo_quality.currentText(),
            "container": self.combo_container.currentText(),
            "fragments": self.spin_fragments.value(),
            "max_concurrent": self.spin_max_concurrent.value(),
            "allow_playlist": self.chk_playlist.isChecked(),
            "speed_limit_kb": self.spin_speed.value(),
            "proxy": self.input_proxy.text().strip(),
            "cookies_browser": self.combo_cookies.currentText(),
            "cookies_file": cfile,
            "naming_template": self.input_template.text().strip(),
            "auto_organize": self.chk_auto_org.isChecked(),
            "skip_duplicates": self.chk_skip_dup.isChecked(),
            "overwrite_existing": self.chk_overwrite_existing.isChecked() if hasattr(self, "chk_overwrite_existing") else False,
            "clip_monitor": self.chk_clip_monitor.isChecked(),
            "privacy_mode": self.chk_privacy.isChecked(),
            "minimize_to_tray": self.chk_tray.isChecked(),
            "embed_thumbnail": self.chk_thumbnail.isChecked(),
            "sponsorblock": self.chk_sponsorblock.isChecked(),
            "smart_sponsor": self.chk_smart_sponsor.isChecked() if hasattr(self, "chk_smart_sponsor") else False,
            "split_chapters": self.chk_split_chapters.isChecked(),
            "live_from_start": self.chk_live_start.isChecked(),
            "loudnorm": self.chk_loudnorm.isChecked(),
            "sub_langs": self.combo_sub_langs.currentText()
        })

    def _current_config(self):
        self.save_current_settings()
        cfile = self.ux_cookies_file_edit.text().strip() if hasattr(self, "ux_cookies_file_edit") and self.ux_cookies_file_edit else ""
        return {
            "base_dir": self.download_dir,
            "quality": self.combo_quality.currentData() or self.combo_quality.currentText(),
            "container": self.combo_container.currentText(),
            "fragments": self.spin_fragments.value(),
            "allow_playlist": self.chk_playlist.isChecked(),
            "subtitles": self.chk_subs.isChecked(),
            "sub_langs": self.combo_sub_langs.currentText(),
            "embed_subs": self.chk_embed_subs.isChecked(),
            "trim_enabled": self.chk_trim.isChecked(),
            "trim_start": self.input_trim_start.text(),
            "trim_end": self.input_trim_end.text(),
            "embed_thumbnail": self.chk_thumbnail.isChecked(),
            "sponsorblock": self.chk_sponsorblock.isChecked(),
            "smart_sponsor": self.chk_smart_sponsor.isChecked() if hasattr(self, "chk_smart_sponsor") else False,
            "split_chapters": self.chk_split_chapters.isChecked(),
            "live_from_start": self.chk_live_start.isChecked(),
            "loudnorm": self.chk_loudnorm.isChecked(),
            "naming_template": self.input_template.text().strip() or "%(title).100s [%(resolution)s] [%(id)s].%(ext)s",
            "auto_organize": self.chk_auto_org.isChecked(),
            "skip_duplicates": self.chk_skip_dup.isChecked(),
            "overwrite_existing": self.chk_overwrite_existing.isChecked() if hasattr(self, "chk_overwrite_existing") else False,
            "speed_limit_kb": self.spin_speed.value(),
            "proxy": self.input_proxy.text().strip(),
            "cookies_browser": self.combo_cookies.currentText(),
            "cookies_file": cfile,
            "privacy_mode": self.chk_privacy.isChecked(),
            "auto_update_engine": self.chk_auto_update_engine.isChecked() if hasattr(self, "chk_auto_update_engine") else True,
        }

    _gather_config = _current_config

    def paste_clipboard(self):
        text = QApplication.clipboard().text().strip()
        if text:
            self.url_input.setText(text)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, tr("dialog.select_folder_title"), self.download_dir)
        if folder:
            self.download_dir = os.path.realpath(folder)
            self.input_dir.setText(self.download_dir)
            self.save_current_settings()
            self.update_disk_space()

    def update_disk_space(self):
        try:
            usage = shutil.disk_usage(self.download_dir)
            free_gb = usage.free / (1024 ** 3)
            used_pct = int((usage.used / usage.total) * 100)
            self.lbl_disk.setText(tr("sidebar.free_space", gb=free_gb))
            self._set_pbar_value(self.bar_disk, used_pct, allow_completed=False)
        except Exception:
            self.lbl_disk.setText(tr("sidebar.free_space_na"))

    def analyze_url(self):
        raw = self.url_input.text().strip()
        if not raw:
            QMessageBox.warning(self, tr("dialog.notice_title"), tr("dialog.enter_query"))
            return

        if getattr(self, "analyzer", None) and self.analyzer.isRunning():
            return

        query = raw.split()[0] if SecurityGuard.is_url(raw) else raw
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.setText(tr("omnibar.inspect_busy"))
        self._hero_is_idle = False
        self.lbl_meta_title.setText(tr("capture.hero_loading"))
        self.nav_list.setCurrentRow(0)

        cfile = self.ux_cookies_file_edit.text().strip() if hasattr(self, "ux_cookies_file_edit") and self.ux_cookies_file_edit else ""
        self.analyzer = AnalyzerWorker(query, self.combo_cookies.currentText(), cfile)
        self.analyzer.finished_signal.connect(self.on_analysis_done)
        self.analyzer.error_signal.connect(self.on_analysis_error)
        self.analyzer.finished.connect(self.analyzer.deleteLater)
        self.analyzer.start()

    def on_analysis_done(self, res):
        self.btn_analyze.setEnabled(True)
        self.btn_analyze.setText(tr("omnibar.inspect"))

        if res.get("is_playlist"):
            entries = res.get("entries") or []
            self.lbl_meta_title.setText(f"{res['title']} ({len(entries)})")
            self.card_platform.set_value(res["platform"])
            self.card_duration.set_value(f"{len(entries)}")

            if entries:
                dlg_title = tr("dialog.search_title") if res.get("is_search") else tr("dialog.playlist_title")
                dlg_sub = tr("dialog.playlist_sub")
                dlg = SelectionDialog(self, dlg_title, dlg_sub, entries)
                if dlg.exec() == QDialog.Accepted and dlg.selected_urls:
                    cfg = dict(self._current_config())
                    cfg["allow_playlist"] = False
                    for u in dlg.selected_urls:
                        self.add_download_task(u, custom_cfg=cfg)
                    self.url_input.clear()
                    self.nav_list.setCurrentRow(1)
            return

        self.lbl_meta_title.setText(f"{res['title']}  —  {res['channel']}")
        self.card_platform.set_value(res["platform"])
        self.card_duration.set_value(res["duration"])
        self.card_res.set_value(f"{res['max_res']}  •  {res['max_fps']}")
        self.card_hdr.set_value(res["hdr"])
        self.card_codecs.set_value(f"{res['vcodecs']} / {res['acodecs']}")
        self.card_subs.set_value(res["subtitles"])
        sz_txt = f"{res['chapters']} cap. • ~{res['est_size_mb']} MB" if res["est_size_mb"] else f"{res['chapters']} cap."
        self.card_size.set_value(sz_txt)
        self.card_rec.set_value(res["recommended"])

        thumb_bytes = res.get("thumbnail_bytes")
        if thumb_bytes:
            pix = QPixmap()
            if pix.loadFromData(thumb_bytes):
                self.lbl_thumbnail.setPixmap(pix.scaled(210, 118, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            else:
                self.lbl_thumbnail.setText("PREVIEW OK")
        else:
            self.lbl_thumbnail.setPixmap(QPixmap())
            self.lbl_thumbnail.setText(tr("capture.no_preview"))

    def on_analysis_error(self, err):
        self.btn_analyze.setEnabled(True)
        self.btn_analyze.setText(tr("omnibar.inspect"))
        causa, sol = DiagnosticEngine.analyze_error(err)
        self.lbl_meta_title.setText(causa)
        QMessageBox.warning(self, tr("dialog.diag_title"), tr("dialog.diag_msg", causa=causa, sol=sol))

    def run_web_sniffer(self):
        if getattr(self, "sniffer", None) and self.sniffer.isRunning():
            return
        raw = self.url_input.text().strip()
        if not SecurityGuard.is_url(raw):
            QMessageBox.warning(self, tr("omnibar.sniffer"), tr("dialog.sniffer_invalid_url"))
            return

        self.btn_sniffer.setEnabled(False)
        self.btn_sniffer.setText(tr("omnibar.sniffer_busy"))
        self.sniffer = WebSnifferWorker(raw.split()[0])
        self.sniffer.finished_signal.connect(self.on_sniffer_done)
        self.sniffer.error_signal.connect(self.on_sniffer_error)
        self.sniffer.finished.connect(self.sniffer.deleteLater)
        self.sniffer.start()

    def on_sniffer_done(self, found: list):
        self.btn_sniffer.setEnabled(True)
        self.btn_sniffer.setText(tr("omnibar.sniffer"))
        if not found:
            QMessageBox.information(self, tr("omnibar.sniffer"), tr("dialog.sniffer_empty"))
            return

        dlg = SelectionDialog(
            self,
            tr("dialog.sniffer_found_title"),
            tr("dialog.sniffer_found_sub", count=len(found)),
            found
        )
        if dlg.exec() == QDialog.Accepted and dlg.selected_urls:
            for u in dlg.selected_urls:
                self.add_download_task(u)
            self.nav_list.setCurrentRow(1)

    def on_sniffer_error(self, err: str):
        self.btn_sniffer.setEnabled(True)
        self.btn_sniffer.setText(tr("omnibar.sniffer"))
        QMessageBox.warning(self, tr("dialog.sniffer_err_title"), tr("dialog.sniffer_err_msg", err=err))

    def extract_clean_transcript(self):
        if getattr(self, "trans_worker", None) and self.trans_worker.isRunning():
            return
        raw = self.url_input.text().strip()
        if not SecurityGuard.is_url(raw):
            QMessageBox.warning(self, tr("omnibar.transcript"), tr("dialog.transcript_invalid_url"))
            return

        self.btn_transcript.setEnabled(False)
        self.btn_transcript.setText(tr("omnibar.transcript_busy"))
        cfile = self.ux_cookies_file_edit.text().strip() if hasattr(self, "ux_cookies_file_edit") and self.ux_cookies_file_edit else ""
        self.trans_worker = TranscriptWorker(
            raw.split()[0], self.download_dir,
            self.combo_sub_langs.currentText(), self.combo_cookies.currentText(), cfile
        )
        self.trans_worker.finished_signal.connect(self.on_transcript_done)
        self.trans_worker.error_signal.connect(self.on_transcript_error)
        self.trans_worker.finished.connect(self.trans_worker.deleteLater)
        self.trans_worker.start()

    def on_transcript_done(self, txt_path: str):
        self.btn_transcript.setEnabled(True)
        self.btn_transcript.setText(tr("omnibar.transcript"))
        QMessageBox.information(self, tr("dialog.transcript_done_title"), tr("dialog.transcript_done_msg", path=txt_path))
        SecurityGuard.safe_open_file(txt_path)

    def on_transcript_error(self, err: str):
        self.btn_transcript.setEnabled(True)
        self.btn_transcript.setText(tr("omnibar.transcript"))
        QMessageBox.warning(self, tr("dialog.transcript_err_title"), err)

    def _find_row_by_task_id(self, task_id: str) -> int:
        for row in range(self.table_queue.rowCount()):
            item = self.table_queue.item(row, 0)
            if item and item.data(Qt.UserRole) == task_id:
                return row
        return -1

    def _set_queue_status(self, row: int, status_text: str, tooltip: str = "", filepath: str = ""):
        """Actualiza la celda de estado con un badge estilizado por color y botón directo 'Mostrar archivo' al completar."""
        if row < 0 or row >= self.table_queue.rowCount():
            return
        st_low = str(status_text or "").lower()
        if any(k in st_low for k in ("completado", "completed", "omitido", "skipped", "ya descargado", "already downloaded")):
            kind = "completed"
        elif any(k in st_low for k in ("pausa", "paused")):
            kind = "paused"
        elif "error" in st_low:
            kind = "error"
        elif any(k in st_low for k in ("cancelado", "cancelled")):
            kind = "cancelled"
        elif any(k in st_low for k in (
            "descargando", "downloading", "iniciando", "starting",
            "conectando", "connecting", "analizando", "analyzing",
            "recortando", "trimming", "procesando", "processing",
            "uniendo", "empaquetando", "packing", "convirtiendo",
            "converting", "normalizando", "normalizing", "smartsponsor"
        )):
            kind = "running"
        else:
            kind = "queued"

        item = QTableWidgetItem(status_text)
        item.setForeground(QBrush(QColor(0, 0, 0, 0)))
        if tooltip:
            item.setToolTip(tooltip)
        self.table_queue.setItem(row, 4, item)

        holder = QWidget()
        holder.setStyleSheet("background: transparent; border: none;")
        h_lay = QHBoxLayout(holder)
        h_lay.setContentsMargins(6, 4, 6, 4)
        h_lay.setSpacing(6)
        h_lay.setAlignment(Qt.AlignCenter)

        badge = QLabel(status_text)
        badge.setObjectName("StatusBadge")
        badge.setProperty("statusKind", kind)
        badge.setAlignment(Qt.AlignCenter)
        if tooltip:
            badge.setToolTip(tooltip)
        h_lay.addWidget(badge)

        if kind == "completed":
            btn_open_item = QPushButton(tr("queue.btn_open_item_folder"))
            btn_open_item.setObjectName("CompactActionBtn")
            btn_open_item.setCursor(Qt.PointingHandCursor)
            btn_open_item.setToolTip(tr("queue.btn_open_item_folder_tip"))
            target_fp = filepath
            btn_open_item.clicked.connect(
                lambda _c=False, fp=target_fp: SecurityGuard.reveal_in_explorer(fp, self.download_dir)
            )
            h_lay.addWidget(btn_open_item)

        self.table_queue.setCellWidget(row, 4, holder)
        row_pbar = self._get_row_progress_bar(row)
        if row_pbar is not None:
            if kind == "completed":
                set_queue_bar_completed(row_pbar, True)
            elif kind in ("queued", "error", "cancelled"):
                set_queue_bar_completed(row_pbar, False)
        needed_w = max(245, holder.sizeHint().width() + 14)
        if self.table_queue.columnWidth(4) < needed_w:
            self.table_queue.setColumnWidth(4, needed_w)

    def _ask_playlist_preference(self, url: str) -> str:
        """Si la URL contiene parámetro de lista (&list=) y chk_playlist está desmarcado, pregunta qué descargar."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle(tr("queue.playlist_prompt_title"))
        msg_box.setText(tr("queue.playlist_prompt_msg"))
        btn_only = msg_box.addButton(tr("queue.playlist_only_video"), QMessageBox.AcceptRole)
        btn_all = msg_box.addButton(tr("queue.playlist_full_list"), QMessageBox.ActionRole)
        btn_cancel = msg_box.addButton(tr("queue.playlist_cancel"), QMessageBox.RejectRole)
        msg_box.setDefaultButton(btn_only)
        msg_box.exec()
        clicked = msg_box.clickedButton()
        if clicked == btn_all:
            return "full_list"
        if clicked == btn_cancel:
            return "cancel"
        return "only_video"

    def enqueue_current_url(self):
        raw = self.url_input.text().strip()
        if not raw:
            QMessageBox.warning(self, tr("dialog.notice_title"), tr("dialog.enter_query"))
            return

        if not SecurityGuard.is_url(raw):
            self.analyze_url()
            return

        added = 0
        for u in raw.split():
            ok, msg = SecurityGuard.validate_url(u)
            if not ok:
                QMessageBox.warning(self, tr("dialog.blocked_url_title"), tr("dialog.blocked_url_msg", url=u[:40], msg=msg))
                continue

            custom_cfg = None
            if ("list=" in u.lower()) and not self.chk_playlist.isChecked():
                choice = self._ask_playlist_preference(u)
                if choice == "cancel":
                    continue
                custom_cfg = dict(self._current_config())
                custom_cfg["allow_playlist"] = (choice == "full_list")

            if self.add_download_task(u, custom_cfg=custom_cfg):
                added += 1

        if added > 0:
            self.url_input.clear()
            self.nav_list.setCurrentRow(1)

    def is_url_in_active_queue(self, url: str) -> bool:
        """Comprueba si la URL ya está en espera o descargándose en la cola activa."""
        norm_u = str(url or "").strip()
        if not norm_u:
            return False
        for info in self.task_info.values():
            if info.get("url") == norm_u and info.get("state") in ("queued", "running"):
                return True
        return False

    def _format_quality_display(self, cfg: dict, actual_res: str = "") -> str:
        raw_q = str(cfg.get("quality") or "")
        container = str(cfg.get("container") or "MP4")
        is_audio = raw_q.startswith("Solo Audio") or ("audio" in raw_q.lower())
        q_label = raw_q
        idx_q = self.combo_quality.findData(raw_q)
        if idx_q >= 0:
            q_label = self.combo_quality.itemText(idx_q)
        if actual_res:
            if is_audio and actual_res == "Audio / Directo":
                return q_label
            return q_label if is_audio else f"{actual_res} [{container}]"
        return q_label if is_audio else f"{q_label} [{container}]"

    def add_download_task(self, url, custom_cfg=None, notify_duplicate: bool = True) -> bool:
        clean_u = str(url or "").strip()
        if self.is_url_in_active_queue(clean_u):
            if notify_duplicate:
                QMessageBox.information(self, tr("queue.duplicate_title"), tr("queue.duplicate_msg"))
            return False

        task_id = uuid.uuid4().hex
        cfg = custom_cfg or self._current_config()

        row = self.table_queue.rowCount()
        self.table_queue.insertRow(row)

        title_item = QTableWidgetItem(clean_u)
        title_item.setData(Qt.UserRole, task_id)
        title_item.setToolTip(clean_u)
        self.table_queue.setItem(row, 0, title_item)
        self.table_queue.setItem(row, 1, QTableWidgetItem(self._format_quality_display(cfg)))

        pbar_holder, _pbar = create_queue_progress_bar()
        self.table_queue.setCellWidget(row, 2, pbar_holder)

        self.table_queue.setItem(row, 3, QTableWidgetItem(tr("status.waiting")))
        self._set_queue_status(row, tr("status.queued"))

        self.task_info[task_id] = {"url": clean_u, "config": cfg, "state": "queued"}
        self._process_queue_pool()
        return True

    def _get_row_progress_bar(self, row: int) -> QProgressBar | None:
        w = self.table_queue.cellWidget(row, 2)
        if isinstance(w, QProgressBar):
            return w
        if w is not None:
            return w.findChild(QProgressBar)
        return None

    def _process_queue_pool(self):
        max_active = self.spin_max_concurrent.value()
        active_count = sum(1 for w in self.workers.values() if w.isRunning())

        if active_count < max_active:
            for row in range(self.table_queue.rowCount()):
                if active_count >= max_active:
                    break
                item = self.table_queue.item(row, 0)
                if not item:
                    continue
                tid = item.data(Qt.UserRole)
                info = self.task_info.get(tid)
                if info and info["state"] == "queued":
                    self._start_worker_for_task(tid)
                    active_count += 1

        self._update_queue_nav_title()

    def _start_worker_for_task(self, task_id):
        info = self.task_info.get(task_id)
        if not info:
            return
        row = self._find_row_by_task_id(task_id)
        if row >= 0:
            self.table_queue.setItem(row, 3, QTableWidgetItem(tr("status.connecting")))
            self._set_queue_status(row, tr("status.starting"))

        worker = DownloadWorker(task_id, info["url"], info["config"], self.media_core.ffmpeg_path)
        worker.progress_signal.connect(self.on_worker_progress)
        worker.log_signal.connect(self.on_worker_log)
        worker.finished_signal.connect(self.on_worker_finished)
        self.workers[task_id] = worker
        info["state"] = "running"
        worker.start()

    def append_download_log(self, text: str):
        if hasattr(self, "txt_download_log") and self.txt_download_log is not None:
            ts = datetime.now().strftime("%H:%M:%S")
            self.txt_download_log.append(f"[{ts}] {text}")

    def on_worker_log(self, task_id: str, message: str):
        self.append_download_log(message)

    def _set_pbar_value(self, pbar: QProgressBar | None, pct: float | int, allow_completed: bool = True):
        if pbar is None:
            return
        val = max(0, min(100, int(pct)))
        has_prog = val > 0
        if getattr(pbar, "_has_prog_state", None) != has_prog:
            pbar._has_prog_state = has_prog
            pbar.setProperty("hasProgress", has_prog)
            pbar.style().unpolish(pbar)
            pbar.style().polish(pbar)
        if allow_completed:
            set_queue_bar_completed(pbar, val >= 100)
        pbar.setValue(val)

    def on_worker_progress(self, task_id, pct, speed, eta, status):
        row = self._find_row_by_task_id(task_id)
        if row < 0:
            return
        pbar = self._get_row_progress_bar(row)
        self._set_pbar_value(pbar, pct)
        self.table_queue.setItem(row, 3, QTableWidgetItem(f"{speed}  •  ETA: {eta}"))
        self._set_queue_status(row, status)

    def on_worker_finished(self, task_id, ok, msg, meta):
        row = self._find_row_by_task_id(task_id)
        msg_low = str(msg or "").lower()
        is_cancelled_msg = ("cancelado" in msg_low or "cancelled" in msg_low)
        task_cfg = (self.task_info.get(task_id) or {}).get("config") or {}
        if task_id in self.task_info:
            self.task_info[task_id]["state"] = "completed" if ok else ("cancelled" if is_cancelled_msg else "error")

        worker = self.workers.pop(task_id, None)
        if worker is not None:
            if not ok:
                worker.cleanup_partials()
            worker.deleteLater()

        if row >= 0:
            pbar = self._get_row_progress_bar(row)
            if ok:
                self._set_pbar_value(pbar, 100)
                sponsor_cuts = meta.get("sponsor_cuts") or []
                if meta.get("already_downloaded") or "ya descargado" in msg_low or "already downloaded" in msg_low:
                    status_label = tr("status.already_downloaded")
                    if task_id in self.task_info:
                        self.task_info[task_id]["already_downloaded"] = True
                elif "omitido" in msg_low or "skipped" in msg_low:
                    status_label = tr("status.skipped_dup")
                elif sponsor_cuts:
                    cuts_txt = ", ".join(f"{c['start_str']}-{c['end_str']}" for c in sponsor_cuts)
                    status_label = f"{tr('status.completed')} (-{len(sponsor_cuts)} sponsor: {cuts_txt})"
                else:
                    status_label = tr("status.completed")
                actual_res = str(meta.get("resolution") or "").strip()
                if actual_res:
                    self.table_queue.setItem(row, 1, QTableWidgetItem(self._format_quality_display(task_cfg, actual_res)))
                self.table_queue.setItem(row, 3, QTableWidgetItem("SHA-256 OK"))
                tip_txt = "\n".join(meta.get("sponsor_logs") or []) if sponsor_cuts else ""
                self._set_queue_status(row, status_label, tooltip=tip_txt, filepath=meta.get("filepath", ""))
                if meta.get("title"):
                    item = self.table_queue.item(row, 0)
                    if item:
                        item.setText(meta["title"])
                        item.setToolTip(meta["title"])
                self.db.add_record(meta)
                self.refresh_library()
                self.update_disk_space()
            else:
                estado_txt = tr("status.cancelled") if is_cancelled_msg else tr("status.error")
                self.table_queue.setItem(row, 3, QTableWidgetItem("—"))
                self._set_queue_status(row, estado_txt, tooltip=str(msg))
                if not is_cancelled_msg:
                    causa, sol = DiagnosticEngine.analyze_error(msg)
                    QMessageBox.critical(
                        self, tr("dialog.dl_err_title"),
                        tr("dialog.dl_err_msg", causa=causa, sol=sol)
                    )

        self._process_queue_pool()
        self._check_post_queue_action()

    def _check_post_queue_action(self):
        active = sum(1 for w in self.workers.values() if w.isRunning())
        queued = sum(1 for info in self.task_info.values() if info["state"] == "queued")
        completed = sum(1 for info in self.task_info.values() if info["state"] == "completed")

        if active == 0 and queued == 0 and completed > 0:
            action = str(self.combo_post_action.currentData() or self.combo_post_action.currentText())
            act_low = action.lower()
            if action == "notify" or "notificaci" in act_low:
                self.tray.showMessage(
                    tr("tray.queue_done_title"),
                    tr("tray.queue_done_msg", completed=completed),
                    QSystemTrayIcon.Information, 4000
                )
            elif action == "open_dir" or "abrir carpeta" in act_low:
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.download_dir))
            elif action == "quit" or "cerrar media platform" in act_low:
                self.quit_application()
            elif action == "sleep" or "suspender" in act_low:
                if os.name == "nt":
                    subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], shell=False)
                elif shutil.which("systemctl"):
                    subprocess.run(["systemctl", "suspend"], shell=False)
            elif action == "shutdown" or "apagar" in act_low:
                if os.name == "nt":
                    subprocess.run(["shutdown", "/s", "/t", "60"], shell=False)
                elif shutil.which("shutdown"):
                    subprocess.run(["shutdown", "-h", "+1"], shell=False)

    def _update_queue_nav_title(self):
        active = sum(1 for w in self.workers.values() if w.isRunning())
        queued = sum(1 for info in self.task_info.values() if info["state"] == "queued")
        total = active + queued
        item = self.nav_list.item(1) if hasattr(self, "nav_list") else None
        if item:
            item.setText(tr("nav.queue_count", count=total) if total else tr("nav.queue"))
        if hasattr(self, "lbl_queue_summary_badge") and self.lbl_queue_summary_badge is not None:
            if total > 0:
                self.lbl_queue_summary_badge.setText(tr("header.queue_active", active=active, queued=queued))
                self.lbl_queue_summary_badge.setProperty("statusKind", "running")
            else:
                completed = sum(1 for info in self.task_info.values() if info["state"] == "completed")
                if completed > 0:
                    self.lbl_queue_summary_badge.setText(tr("header.queue_completed", completed=completed))
                    self.lbl_queue_summary_badge.setProperty("statusKind", "completed")
                else:
                    self.lbl_queue_summary_badge.setText(tr("header.queue_idle"))
                    self.lbl_queue_summary_badge.setProperty("statusKind", "queued")
            self.lbl_queue_summary_badge.style().unpolish(self.lbl_queue_summary_badge)
            self.lbl_queue_summary_badge.style().polish(self.lbl_queue_summary_badge)

    def _selected_task_ids(self) -> list[str]:
        ids = []
        for idx in self.table_queue.selectionModel().selectedRows():
            item = self.table_queue.item(idx.row(), 0)
            if item and item.data(Qt.UserRole):
                ids.append(item.data(Qt.UserRole))
        return ids

    def pause_selected(self):
        for tid in self._selected_task_ids():
            w = self.workers.get(tid)
            if w and w.isRunning():
                w.is_paused = True
                row = self._find_row_by_task_id(tid)
                if row >= 0:
                    self._set_queue_status(row, tr("status.paused"))

    def resume_selected(self):
        for tid in self._selected_task_ids():
            w = self.workers.get(tid)
            if w and w.isRunning():
                w.is_paused = False
                row = self._find_row_by_task_id(tid)
                if row >= 0:
                    self._set_queue_status(row, tr("status.downloading"))

    def pause_all_tasks(self):
        for tid, w in self.workers.items():
            if w.isRunning():
                w.is_paused = True
                row = self._find_row_by_task_id(tid)
                if row >= 0:
                    self._set_queue_status(row, tr("status.paused"))

    def resume_all_tasks(self):
        for tid, w in self.workers.items():
            if w.isRunning():
                w.is_paused = False
                row = self._find_row_by_task_id(tid)
                if row >= 0:
                    self._set_queue_status(row, tr("status.downloading"))

    def cancel_selected(self):
        for tid in self._selected_task_ids():
            info = self.task_info.get(tid)
            if info and info["state"] == "queued":
                info["state"] = "cancelled"
                row = self._find_row_by_task_id(tid)
                if row >= 0:
                    self.table_queue.setItem(row, 3, QTableWidgetItem("—"))
                    self._set_queue_status(row, tr("status.cancelled"))
                continue
            w = self.workers.get(tid)
            if w and w.isRunning():
                w.is_cancelled = True
                w.is_paused = False
        self._process_queue_pool()

    def _requeue_selected_tasks(self, force_overwrite: bool = False):
        for tid in self._selected_task_ids():
            w = self.workers.get(tid)
            if w and w.isRunning():
                continue
            info = self.task_info.get(tid)
            if info:
                info["state"] = "queued"
                info["already_downloaded"] = False
                if force_overwrite:
                    cfg = dict(info.get("config") or {})
                    cfg["overwrite_existing"] = True
                    cfg["force_overwrite"] = True
                    cfg["skip_duplicates"] = False
                    info["config"] = cfg
                row = self._find_row_by_task_id(tid)
                if row >= 0:
                    pbar = self._get_row_progress_bar(row)
                    self._set_pbar_value(pbar, 0)
                    self.table_queue.setItem(row, 3, QTableWidgetItem(tr("status.waiting")))
                    self._set_queue_status(row, tr("status.queued"))
        self._process_queue_pool()

    def retry_selected(self):
        self._requeue_selected_tasks(force_overwrite=False)

    def force_redownload_selected(self):
        self._requeue_selected_tasks(force_overwrite=True)

    def remove_selected_from_queue(self):
        task_ids = self._selected_task_ids()
        if not task_ids:
            return

        for tid in task_ids:
            w = self.workers.get(tid)
            if w:
                if w.isRunning():
                    w.is_cancelled = True
                    w.is_paused = False
                    w.wait(800)
                w.cleanup_partials()
                self.workers.pop(tid, None)

            self.task_info.pop(tid, None)
            row = self._find_row_by_task_id(tid)
            if row >= 0:
                self.table_queue.removeRow(row)

        self._process_queue_pool()

    def clear_inactive_queue(self):
        to_remove = []
        for tid, info in list(self.task_info.items()):
            w = self.workers.get(tid)
            if info["state"] in ("completed", "cancelled", "error") and (not w or not w.isRunning()):
                to_remove.append(tid)

        for tid in to_remove:
            w = self.workers.pop(tid, None)
            if w and self.task_info.get(tid, {}).get("state") != "completed":
                w.cleanup_partials()
            self.task_info.pop(tid, None)
            row = self._find_row_by_task_id(tid)
            if row >= 0:
                self.table_queue.removeRow(row)

        self._update_queue_nav_title()

    def show_queue_context_menu(self, pos):
        if not self.table_queue.selectionModel().selectedRows():
            return
        menu = QMenu(self)
        act_pause = QAction(tr("queue.btn_pause"), self)
        act_resume = QAction(tr("queue.btn_resume"), self)
        act_retry = QAction(tr("queue.btn_retry"), self)
        act_force_redownload = QAction(tr("queue.btn_force_redownload"), self)
        act_cancel = QAction(tr("queue.btn_cancel"), self)
        act_remove = QAction(tr("queue.btn_remove"), self)

        act_pause.triggered.connect(self.pause_selected)
        act_resume.triggered.connect(self.resume_selected)
        act_retry.triggered.connect(self.retry_selected)
        act_force_redownload.triggered.connect(self.force_redownload_selected)
        act_cancel.triggered.connect(self.cancel_selected)
        act_remove.triggered.connect(self.remove_selected_from_queue)

        menu.addAction(act_pause)
        menu.addAction(act_resume)
        menu.addAction(act_retry)
        menu.addAction(act_force_redownload)
        menu.addSeparator()
        menu.addAction(act_cancel)
        menu.addAction(act_remove)
        menu.exec(self.table_queue.viewport().mapToGlobal(pos))

    def import_batch_file(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("dialog.import_batch_title"), "", "Listas (*.txt *.csv)")
        if not path or not os.path.isfile(path):
            return
        max_batch_urls = 1000
        urls = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            if path.lower().endswith(".csv"):
                for row in csv.reader(f):
                    for cell in row:
                        ok, clean = SecurityGuard.validate_url(cell)
                        if ok:
                            urls.append(clean)
                            if len(urls) >= max_batch_urls:
                                break
                    if len(urls) >= max_batch_urls:
                        break
            else:
                for line in f:
                    ok, clean = SecurityGuard.validate_url(line)
                    if ok:
                        urls.append(clean)
                        if len(urls) >= max_batch_urls:
                            break
        for u in urls[:max_batch_urls]:
            self.add_download_task(u, notify_duplicate=False)
        self.nav_list.setCurrentRow(1)

    def import_from_clipboard(self):
        raw = QApplication.clipboard().text()
        urls = []
        for token in raw.split():
            ok, clean = SecurityGuard.validate_url(token)
            if ok:
                urls.append(clean)
        if not urls:
            QMessageBox.information(self, tr("dialog.clipboard_title"), tr("dialog.clipboard_empty"))
            return
        for u in urls:
            self.add_download_task(u, notify_duplicate=False)
        self.nav_list.setCurrentRow(1)

    def refresh_library(self):
        query = self.input_lib_search.text().strip() if hasattr(self, "input_lib_search") else ""
        records = self.db.search_library(query)
        self.table_lib.setRowCount(0)
        for r in records:
            row = self.table_lib.rowCount()
            self.table_lib.insertRow(row)

            t_item = QTableWidgetItem(r["title"])
            t_item.setData(Qt.UserRole, r["id"])
            t_item.setToolTip(r["title"])
            self.table_lib.setItem(row, 0, t_item)
            self.table_lib.setItem(row, 1, QTableWidgetItem(r["channel"]))
            self.table_lib.setItem(row, 2, QTableWidgetItem(r["platform"]))
            self.table_lib.setItem(row, 3, QTableWidgetItem(f"{r['resolution']} ({r['hdr']})"))
            full_hash = r.get("file_hash") or "N/A"
            h_short = full_hash[:16] + "..." if len(full_hash) > 16 else full_hash
            h_item = QTableWidgetItem(h_short)
            h_item.setToolTip(f"SHA-256: {full_hash}")
            self.table_lib.setItem(row, 4, h_item)
            self.table_lib.setItem(row, 5, QTableWidgetItem(r["downloaded_at"]))
            p_item = QTableWidgetItem(r["filepath"])
            p_item.setToolTip(r["filepath"])
            self.table_lib.setItem(row, 6, p_item)

    def play_selected_library(self):
        rows = self.table_lib.selectionModel().selectedRows()
        if not rows:
            return
        filepath = self.table_lib.item(rows[0].row(), 6).text()
        SecurityGuard.safe_open_file(filepath)

    def locate_selected_library(self):
        rows = self.table_lib.selectionModel().selectedRows()
        filepath = self.table_lib.item(rows[0].row(), 6).text() if rows else ""
        SecurityGuard.reveal_in_explorer(filepath, self.download_dir)

    def delete_selected_library_row(self):
        rows = self.table_lib.selectionModel().selectedRows()
        for idx in rows:
            item = self.table_lib.item(idx.row(), 0)
            if item and item.data(Qt.UserRole):
                self.db.delete_record(item.data(Qt.UserRole))
        self.refresh_library()

    def clear_library(self):
        self.db.clear_history()
        self.refresh_library()

    def select_ffmpeg_input(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("dialog.select_media_title"))
        if not path:
            return
        self.input_ff_in.setText(path)
        self.txt_ffprobe.setPlainText(f"Analizando pistas y calculando hash SHA-256 en segundo plano...\nArchivo: {path}")
        if getattr(self, "probe_worker", None) and self.probe_worker.isRunning():
            self.probe_worker.wait(300)
        self.probe_worker = ProbeWorker(path)
        self.probe_worker.finished_signal.connect(self.on_probe_done)
        self.probe_worker.error_signal.connect(lambda err: self.txt_ffprobe.setPlainText(f"Error al inspeccionar archivo:\n{err}"))
        self.probe_worker.finished.connect(self.probe_worker.deleteLater)
        self.probe_worker.start()

    def on_probe_done(self, path: str, dur: float, sha: str, info: dict):
        header = f"Archivo  : {path}\nDuración : {dur:.1f} seg\nSHA-256  : {sha}\n" + ("-" * 65) + "\n"
        if info:
            self.txt_ffprobe.setPlainText(header + json.dumps(info, indent=2, ensure_ascii=False))
        else:
            self.txt_ffprobe.setPlainText(header + "Listo para procesar.")

    def run_ffmpeg_tool(self):
        if getattr(self, "ffmpeg_worker", None) and self.ffmpeg_worker.isRunning():
            self.ffmpeg_worker.is_cancelled = True
            self.btn_run_ff.setEnabled(False)
            self.btn_run_ff.setText("Cancelando FFmpeg...")
            return

        in_file = self.input_ff_in.text().strip()
        if not in_file or not os.path.isfile(in_file):
            QMessageBox.warning(self, tr("dialog.notice_title"), tr("dialog.ff_invalid_file"))
            return

        op_code = str(self.combo_ff_op.currentData() or "")
        op = self.combo_ff_op.currentText()
        hw = self.combo_hw.currentText().split()[0]
        base, _ = os.path.splitext(in_file)
        target_mb = 0

        if op_code == "remux_mp4" or ".MP4 (Copia" in op or ".MP4 (Instant" in op:
            out_file, mode = f"{base}_remux.mp4", "remux"
        elif op_code == "remux_mkv" or ".MKV (Copia" in op or ".MKV (Instant" in op:
            out_file, mode = f"{base}_remux.mkv", "remux"
        elif op_code == "compress_10" or "< 10 MB" in op:
            out_file, mode, target_mb = f"{base}_10MB.mp4", "compress_size", 10
        elif op_code == "compress_25" or "< 25 MB" in op:
            out_file, mode, target_mb = f"{base}_25MB.mp4", "compress_size", 25
        elif op_code == "compress_50" or "< 50 MB" in op:
            out_file, mode, target_mb = f"{base}_50MB.mp4", "compress_size", 50
        elif op_code == "loudnorm_video" or "Normalizar volumen" in op or "Normalize video loudness" in op:
            out_file, mode = f"{base}_loudnorm.mp4", "loudnorm_video"
        elif op_code == "loudnorm_audio" or "Extraer y normalizar" in op or "Extract & normalize" in op:
            out_file, mode = f"{base}_loudnorm.mp3", "loudnorm_audio"
        elif op_code == "audio_mp3" or "Extraer pista" in op or "Extract direct" in op:
            out_file, mode = f"{base}_audio.mp3", "audio_mp3"
        elif op_code == "gif" or ".GIF" in op:
            out_file, mode = f"{base}_anim.gif", "gif"
        else:
            out_file, mode = f"{base}_h264.mp4", "convert"

        self.btn_run_ff.setText(tr("ffmpeg.btn_cancel"))
        self.txt_ffprobe.append(f"\n[FFmpeg] Iniciando operación '{mode}' -> {out_file} ...")

        self.ffmpeg_worker = FFmpegTaskWorker(in_file, out_file, mode=mode, hw_accel=hw, target_mb=target_mb)
        self.ffmpeg_worker.status_signal.connect(lambda st: self.txt_ffprobe.append(f"[FFmpeg] {st}"))
        self.ffmpeg_worker.finished_signal.connect(self.on_ffmpeg_task_done)
        self.ffmpeg_worker.error_signal.connect(self.on_ffmpeg_task_error)
        self.ffmpeg_worker.finished.connect(self.ffmpeg_worker.deleteLater)
        self.ffmpeg_worker.start()

    def on_ffmpeg_task_done(self, out_file: str):
        self.btn_run_ff.setEnabled(True)
        self.btn_run_ff.setText(tr("ffmpeg.btn_run"))
        self.txt_ffprobe.append(f"[FFmpeg] Completado con éxito: {out_file}")
        QMessageBox.information(self, tr("dialog.completed_title"), tr("dialog.ff_done_msg", out_file=out_file))

    def on_ffmpeg_task_error(self, err_msg: str):
        self.btn_run_ff.setEnabled(True)
        self.btn_run_ff.setText(tr("ffmpeg.btn_run"))
        self.txt_ffprobe.append(f"[FFmpeg] Aviso/Error: {err_msg}")
        if "cancelado" in err_msg.lower():
            QMessageBox.information(self, "FFmpeg", err_msg)
        else:
            QMessageBox.critical(self, tr("dialog.ff_err_title"), err_msg)

    def toggle_privacy_mode(self, checked):
        self.db.privacy_mode = checked
        self.save_current_settings()
        self.refresh_diagnostics()

    def refresh_diagnostics(self):
        has_ext = EngineHotSwapManager.has_external_plugin() or os.path.isfile(
            os.path.join(get_portable_data_dir(), "engine", "yt-dlp")
        )
        has_bak = EngineHotSwapManager.has_backup_plugin()
        if hasattr(self, "btn_rollback_yt") and self.btn_rollback_yt is not None:
            self.btn_rollback_yt.setEnabled(EngineHotSwapManager.can_rollback())
        self._check_ffmpeg_availability()
        auto_upd_flag = (
            self.chk_auto_update_engine.isChecked()
            if hasattr(self, "chk_auto_update_engine") and self.chk_auto_update_engine is not None
            else bool(self.settings.data.get("auto_update_engine", True))
        )
        ext_status = tr("diag.ext_installed") if has_ext else tr("diag.ext_native")
        rb_status = tr("diag.rb_bak") if has_bak else (tr("diag.rb_rev") if has_ext else tr("diag.rb_na"))
        auto_status = tr("diag.auto_on") if auto_upd_flag else tr("diag.auto_off")
        not_found = tr("diag.not_found")
        report = (
            f"{tr('diag.header', version=self.APP_VERSION)}\n"
            "────────────────────────────────────────────────────────────\n"
            f"{tr('diag.yt_ver', version=yt_dlp.version.__version__)}\n"
            f"{tr('diag.ext_pkg', status=ext_status)}\n"
            f"{tr('diag.rollback', status=rb_status)}\n"
            f"{tr('diag.auto_upd', status=auto_status)}\n"
            f"{tr('diag.ffmpeg_bin', path=self.media_core.ffmpeg_path or not_found)}\n"
            f"{tr('diag.ffprobe_bin', path=self.media_core.ffprobe_path or not_found)}\n"
            f"{tr('diag.sqlite_db', path=self.db.db_path)}\n"
            f"{tr('diag.cfg_file', path=self.settings.filepath)}\n\n"
            f"{tr('diag.lic_header')}\n"
            "────────────────────────────────────────────────────────────\n"
            f"{tr('diag.lic_proj')}\n"
            f"{tr('diag.lic_pyside')}\n"
            f"{tr('diag.lic_ytdlp')}\n"
            f"{tr('diag.lic_ffmpeg')}\n"
            f"{tr('diag.lic_whisper')}\n"
            f"{tr('diag.lic_gfx')}\n"
        )
        self.txt_diag.setPlainText(report)

    def show_about_gpl_dialog(self):
        QMessageBox.information(
            self,
            tr("dialog.about_title"),
            tr("dialog.about_body", version=self.APP_VERSION)
        )

    def update_ytdlp_engine(self, auto_triggered: bool = False):
        if getattr(self, "update_worker", None) and self.update_worker.isRunning():
            return
        self._last_update_was_auto = bool(auto_triggered)
        self.btn_update_yt.setEnabled(False)
        self.btn_update_yt.setText(tr("header.updating_btn"))
        if hasattr(self, "btn_rollback_yt") and self.btn_rollback_yt is not None:
            self.btn_rollback_yt.setEnabled(False)
        if hasattr(self, "btn_quick_update_yt") and self.btn_quick_update_yt is not None:
            self.btn_quick_update_yt.setEnabled(False)
            self.btn_quick_update_yt.setText(tr("header.updating_btn"))
        if not auto_triggered:
            self.txt_diag.append("\nConectando con el repositorio oficial de yt-dlp en segundo plano...")

        self.update_worker = UpdateEngineWorker()
        self.update_worker.finished_signal.connect(self.on_update_engine_done)
        self.update_worker.error_signal.connect(self.on_update_engine_error)
        self.update_worker.finished.connect(self.update_worker.deleteLater)
        self.update_worker.start()

    def on_update_engine_done(self, ok: bool, msg: str):
        self.btn_update_yt.setEnabled(True)
        self.btn_update_yt.setText(tr("security.btn_update_yt"))
        if hasattr(self, "update_banner_frame") and self.update_banner_frame is not None:
            if ok:
                self.update_banner_frame.setVisible(False)
            elif not getattr(self, "_last_update_was_auto", False):
                self.btn_quick_update_yt.setEnabled(True)
                self.btn_quick_update_yt.setText(tr("header.retry_btn"))
        self.refresh_diagnostics()
        self.txt_diag.append(f"\n[{'OK' if ok else 'AVISO'}] {msg}")

    def on_update_engine_error(self, err: str):
        self.btn_update_yt.setEnabled(True)
        self.btn_update_yt.setText(tr("security.btn_update_yt"))
        self.refresh_diagnostics()
        if hasattr(self, "btn_quick_update_yt") and self.btn_quick_update_yt is not None:
            self.btn_quick_update_yt.setEnabled(True)
            self.btn_quick_update_yt.setText(tr("header.retry_btn"))
        self.txt_diag.append(f"\n[ERROR] No se pudo actualizar el motor: {err}")

    def rollback_ytdlp_engine(self):
        if getattr(self, "rollback_worker", None) and self.rollback_worker.isRunning():
            return
        self.btn_update_yt.setEnabled(False)
        if hasattr(self, "btn_rollback_yt") and self.btn_rollback_yt is not None:
            self.btn_rollback_yt.setEnabled(False)
            self.btn_rollback_yt.setText(tr("security.btn_rollback_busy"))
        self.txt_diag.append("\nRevirtiendo motor yt-dlp en segundo plano...")

        self.rollback_worker = RollbackEngineWorker()
        self.rollback_worker.finished_signal.connect(self.on_rollback_engine_done)
        self.rollback_worker.error_signal.connect(self.on_rollback_engine_error)
        self.rollback_worker.finished.connect(self.rollback_worker.deleteLater)
        self.rollback_worker.start()

    def on_rollback_engine_done(self, ok: bool, msg: str):
        self.btn_update_yt.setEnabled(True)
        if hasattr(self, "btn_rollback_yt") and self.btn_rollback_yt is not None:
            self.btn_rollback_yt.setText(tr("security.btn_rollback_yt"))
        self.refresh_diagnostics()
        self.txt_diag.append(f"\n[{'ROLLBACK OK' if ok else 'AVISO'}] {msg}")

    def on_rollback_engine_error(self, err: str):
        self.btn_update_yt.setEnabled(True)
        if hasattr(self, "btn_rollback_yt") and self.btn_rollback_yt is not None:
            self.btn_rollback_yt.setText(tr("security.btn_rollback_yt"))
        self.refresh_diagnostics()
        self.txt_diag.append(f"\n[ERROR ROLLBACK] {err}")

    def apply_theme(self):
        ErgonomicThemeEngine.apply_to_window(self, self._active_ergonomic_theme)

    def toggle_theme(self):
        names = list(ErgonomicThemeEngine.PRESETS.keys())
        _, curr_name = ErgonomicThemeEngine.load_state(self.settings)
        next_idx = (names.index(curr_name) + 1) % len(names) if curr_name in names else 0
        next_name = names[next_idx]
        if hasattr(self, "_theme_preset_combo") and self._theme_preset_combo is not None:
            idx_cmb = self._theme_preset_combo.findData(next_name)
            self._theme_preset_combo.setCurrentIndex(idx_cmb if idx_cmb >= 0 else next_idx)
        else:
            new_t = dict(ErgonomicThemeEngine.PRESETS[next_name])
            ErgonomicThemeEngine.save_state(new_t, next_name, self.settings)
            ErgonomicThemeEngine.apply_to_window(self, new_t)

    def _setup_reactive_ux_rules(self):
        self.ux_quality_combo = self.combo_quality
        self.ux_container_combo = self.combo_container
        self.ux_sub_lang_combo = self.combo_sub_langs
        self.ux_sub_chk = self.chk_subs
        self.ux_embed_subs_chk = self.chk_embed_subs
        self.ux_trim_chk = self.chk_trim
        self.ux_split_chapters_chk = self.chk_split_chapters
        self.ux_embed_thumb_chk = self.chk_thumbnail
        self.ux_trim_inputs = [self.input_trim_start, self.input_trim_end]

        def _on_quality_mode_changed(_q_text: str = ""):
            q_val = str(self.combo_quality.currentData() or self.combo_quality.currentText() or "")
            is_audio = "audio" in q_val.lower()
            self.combo_container.setEnabled(not is_audio)
            self.combo_container.setToolTip(
                tr("capture.container_disabled_tip")
                if is_audio else tr("capture.container_enabled_tip")
            )
            if is_audio:
                self.chk_embed_subs.setChecked(False)
            self.chk_embed_subs.setEnabled(not is_audio)

        self._refresh_container_state = _on_quality_mode_changed
        self.combo_quality.currentIndexChanged.connect(lambda _idx: _on_quality_mode_changed())
        _on_quality_mode_changed()

        def _on_trim_toggled(checked: bool):
            for le_t in self.ux_trim_inputs:
                le_t.setEnabled(bool(checked))
            if checked and self.chk_split_chapters.isChecked():
                self.chk_split_chapters.blockSignals(True)
                self.chk_split_chapters.setChecked(False)
                self.chk_split_chapters.blockSignals(False)

        def _on_split_chapters_toggled(checked: bool):
            if checked and self.chk_trim.isChecked():
                self.chk_trim.blockSignals(True)
                self.chk_trim.setChecked(False)
                self.chk_trim.blockSignals(False)
                for le_t in self.ux_trim_inputs:
                    le_t.setEnabled(False)

        self.chk_trim.toggled.connect(_on_trim_toggled)
        _on_trim_toggled(self.chk_trim.isChecked())
        self.chk_split_chapters.toggled.connect(_on_split_chapters_toggled)

        self.combo_sub_langs.setEnabled(True)
        self.chk_subs.toggled.connect(lambda _c: self.combo_sub_langs.setEnabled(True))


def main():
    EngineHotSwapManager.activate_plugins_path()
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


# Exportar absolutamente todos los símbolos (incluidos los que empiezan por _) entre los módulos de mpp
__all__ = [k for k in list(globals().keys()) if not k.startswith("__")]
