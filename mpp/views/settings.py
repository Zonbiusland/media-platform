# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Media Platform (Studio Master v1.0.0) — Vistas de Ajustes, Red y Seguridad (GPLv3+)
# Este archivo es software libre distribuido bajo la licencia GNU GPL v3.0 o posterior.
from ..core import *
from ..themes import *
from . import wrap_page_in_scroll


def build_settings_view(win) -> QScrollArea:
    """Construye la vista de Ajustes y Red (con selector de idioma EN/ES) y vincula sus controles a MainWindow."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 6, 0)
    layout.setSpacing(12)

    win.org_card = SurfaceCard(
        tr("settings.org_title"),
        tr("settings.org_sub")
    )
    ogrid = QGridLayout()
    ogrid.setHorizontalSpacing(18)
    ogrid.setVerticalSpacing(10)
    ogrid.setColumnStretch(1, 1)

    win.lbl_lang_setting = QLabel(tr("settings.lbl_language"))
    win.lbl_lang_setting.setObjectName("FieldLabel")
    ogrid.addWidget(win.lbl_lang_setting, 0, 0)

    win.combo_language = QComboBox()
    win.combo_language.setMinimumHeight(34)
    win.combo_language.addItem("English (en)", "en")
    win.combo_language.addItem("Español (es)", "es")
    curr_lang = get_language()
    idx_l = win.combo_language.findData(curr_lang)
    if idx_l >= 0:
        win.combo_language.setCurrentIndex(idx_l)
    win.combo_language.currentIndexChanged.connect(
        lambda _i: win.set_app_language(win.combo_language.currentData(), persist=True)
    )
    ogrid.addWidget(win.combo_language, 0, 1)

    win.lbl_tpl_setting = QLabel(tr("settings.lbl_template"))
    win.lbl_tpl_setting.setObjectName("FieldLabel")
    ogrid.addWidget(win.lbl_tpl_setting, 1, 0)
    win.input_template = QLineEdit("%(title).100s [%(resolution)s] [%(id)s].%(ext)s")
    win.input_template.setMinimumHeight(34)
    ogrid.addWidget(win.input_template, 1, 1)

    win.chk_auto_org = QCheckBox(tr("settings.chk_auto_org"))
    win.chk_auto_org.setMinimumHeight(26)
    ogrid.addWidget(win.chk_auto_org, 2, 0, 1, 2)

    win.chk_skip_dup = QCheckBox(tr("settings.chk_skip_dup"))
    win.chk_skip_dup.setMinimumHeight(26)
    win.chk_skip_dup.setChecked(True)
    ogrid.addWidget(win.chk_skip_dup, 3, 0)

    win.chk_overwrite_existing = QCheckBox(tr("settings.chk_overwrite_existing"))
    win.chk_overwrite_existing.setMinimumHeight(26)
    win.chk_overwrite_existing.setChecked(False)
    win.chk_overwrite_existing.setToolTip(tr("settings.chk_overwrite_existing_tip"))
    ogrid.addWidget(win.chk_overwrite_existing, 3, 1)

    win.chk_clip_monitor = QCheckBox(tr("settings.chk_clip_monitor"))
    win.chk_clip_monitor.setMinimumHeight(26)
    ogrid.addWidget(win.chk_clip_monitor, 4, 0)

    win.chk_tray = QCheckBox(tr("settings.chk_tray"))
    win.chk_tray.setMinimumHeight(26)
    win.chk_tray.setChecked(False)
    ogrid.addWidget(win.chk_tray, 4, 1)

    win.org_card.main_layout.addLayout(ogrid)
    layout.addWidget(win.org_card)

    win.net_card = SurfaceCard(
        tr("settings.net_title"),
        tr("settings.net_sub")
    )
    ngrid = QGridLayout()
    ngrid.setHorizontalSpacing(18)
    ngrid.setVerticalSpacing(12)
    ngrid.setColumnStretch(1, 1)

    win.lbl_conc_setting = QLabel(tr("settings.lbl_concurrent"))
    win.lbl_conc_setting.setObjectName("FieldLabel")
    ngrid.addWidget(win.lbl_conc_setting, 0, 0)
    win.spin_max_concurrent = QSpinBox()
    win.spin_max_concurrent.setMinimumHeight(34)
    win.spin_max_concurrent.setRange(1, 8)
    win.spin_max_concurrent.setValue(2)
    win.spin_max_concurrent.valueChanged.connect(win._process_queue_pool)
    ngrid.addWidget(win.spin_max_concurrent, 0, 1)

    win.lbl_spd_setting = QLabel(tr("settings.lbl_speed"))
    win.lbl_spd_setting.setObjectName("FieldLabel")
    ngrid.addWidget(win.lbl_spd_setting, 1, 0)
    win.spin_speed = QSpinBox()
    win.spin_speed.setMinimumHeight(34)
    win.spin_speed.setRange(0, 1000000)
    win.spin_speed.setValue(0)
    ngrid.addWidget(win.spin_speed, 1, 1)

    win.lbl_prx_setting = QLabel(tr("settings.lbl_proxy"))
    win.lbl_prx_setting.setObjectName("FieldLabel")
    ngrid.addWidget(win.lbl_prx_setting, 2, 0)
    win.input_proxy = QLineEdit()
    win.input_proxy.setMinimumHeight(34)
    win.input_proxy.setPlaceholderText("Opcional: socks5://127.0.0.1:9050")
    ngrid.addWidget(win.input_proxy, 2, 1)

    win.lbl_ckb_setting = QLabel(tr("settings.lbl_cookies_browser"))
    win.lbl_ckb_setting.setObjectName("FieldLabel")
    ngrid.addWidget(win.lbl_ckb_setting, 3, 0)
    win.combo_cookies = QComboBox()
    win.combo_cookies.setMinimumHeight(34)
    win.combo_cookies.addItems(["Ninguno", "Firefox", "Edge", "Chrome", "Brave", "Opera"])
    ngrid.addWidget(win.combo_cookies, 3, 1)

    cf_row_widget = QWidget(win.net_card)
    cf_row_lay = QHBoxLayout(cf_row_widget)
    cf_row_lay.setContentsMargins(0, 4, 0, 2)
    cf_row_lay.setSpacing(8)

    win.lbl_cf_setting = QLabel(tr("settings.lbl_cookies_file"))
    win.lbl_cf_setting.setObjectName("FieldLabel")
    win.ux_cookies_file_edit = QLineEdit()
    win.ux_cookies_file_edit.setMinimumHeight(34)
    win.ux_cookies_file_edit.setPlaceholderText("Opcional: ruta a cookies.txt exportado (prioridad sobre navegador)...")
    win.btn_browse_cf = QPushButton(tr("ffmpeg.btn_browse"))
    win.btn_browse_cf.setMinimumHeight(34)
    win.btn_clear_cf = QPushButton(tr("settings.btn_clear"))
    win.btn_clear_cf.setMinimumHeight(34)

    def _save_cf(path_str: str):
        clean_p = path_str.strip()
        win.ux_cookies_file_edit.setText(clean_p)
        win.settings.save({"cookies_file": clean_p})

    def _browse_cf():
        fpath, _ = QFileDialog.getOpenFileName(
            win, "Seleccionar archivo cookies.txt (Netscape)", "", "Archivos de texto (*.txt);;Todos (*.*)"
        )
        if fpath:
            _save_cf(fpath)

    win.btn_browse_cf.clicked.connect(_browse_cf)
    win.btn_clear_cf.clicked.connect(lambda: _save_cf(""))
    win.ux_cookies_file_edit.editingFinished.connect(lambda: _save_cf(win.ux_cookies_file_edit.text()))

    cf_row_lay.addWidget(win.lbl_cf_setting)
    cf_row_lay.addWidget(win.ux_cookies_file_edit, 1)
    cf_row_lay.addWidget(win.btn_browse_cf)
    cf_row_lay.addWidget(win.btn_clear_cf)
    ngrid.addWidget(cf_row_widget, 4, 0, 1, 2)

    win.net_card.main_layout.addLayout(ngrid)
    layout.addWidget(win.net_card)

    win.priv_card = SurfaceCard(tr("settings.priv_title"))
    win.chk_privacy = QCheckBox(tr("settings.chk_privacy"))
    win.chk_privacy.setMinimumHeight(26)
    win.chk_privacy.toggled.connect(win.toggle_privacy_mode)
    win.priv_card.main_layout.addWidget(win.chk_privacy)

    layout.addWidget(win.priv_card)
    layout.addStretch(1)
    return wrap_page_in_scroll(page)


def build_security_view(win) -> QScrollArea:
    """Construye la vista de Sistema y Seguridad y vincula sus controles a MainWindow."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 6, 0)
    layout.setSpacing(12)

    win.sec_card = SurfaceCard(
        tr("security.card_title"),
        tr("security.card_sub")
    )
    win.chk_auto_update_engine = QCheckBox(tr("security.chk_auto_update"))
    win.chk_auto_update_engine.setMinimumHeight(26)
    win.chk_auto_update_engine.setChecked(True)
    win.chk_auto_update_engine.toggled.connect(
        lambda checked: win.settings.save({"auto_update_engine": bool(checked)})
    )
    win.sec_card.main_layout.addWidget(win.chk_auto_update_engine)

    win.txt_diag = QTextEdit()
    win.txt_diag.setReadOnly(True)
    win.txt_diag.setMinimumHeight(220)
    diag_font = QFont("DejaVu Sans Mono", 9.5)
    diag_font.setStyleHint(QFont.Monospace)
    win.txt_diag.setFont(diag_font)
    win.sec_card.main_layout.addWidget(win.txt_diag, stretch=1)

    btn_bar = QHBoxLayout()
    btn_bar.setSpacing(10)
    win.btn_update_yt = QPushButton(tr("security.btn_update_yt"))
    win.btn_update_yt.setMinimumHeight(36)
    win.btn_update_yt.setObjectName("AccentButton")
    win.btn_update_yt.setToolTip(tr("security.btn_update_yt_tip"))
    win.btn_update_yt.clicked.connect(win.update_ytdlp_engine)
    btn_bar.addWidget(win.btn_update_yt)

    win.btn_rollback_yt = QPushButton(tr("security.btn_rollback_yt"))
    win.btn_rollback_yt.setMinimumHeight(36)
    win.btn_rollback_yt.setToolTip(tr("security.btn_rollback_yt_tip"))
    win.btn_rollback_yt.clicked.connect(win.rollback_ytdlp_engine)
    btn_bar.addWidget(win.btn_rollback_yt)

    win.btn_refresh_diag = QPushButton(tr("security.btn_refresh"))
    win.btn_refresh_diag.setMinimumHeight(36)
    win.btn_refresh_diag.clicked.connect(win.refresh_diagnostics)
    btn_bar.addWidget(win.btn_refresh_diag)

    win.btn_about_gpl = QPushButton(tr("security.btn_about"))
    win.btn_about_gpl.setMinimumHeight(36)
    win.btn_about_gpl.clicked.connect(win.show_about_gpl_dialog)
    btn_bar.addWidget(win.btn_about_gpl)

    win.sec_card.main_layout.addLayout(btn_bar)
    layout.addWidget(win.sec_card, stretch=1)

    win.gpl_card = SurfaceCard(
        tr("security.gpl_title"),
        tr("security.gpl_sub")
    )
    win.lbl_gpl_info = QLabel(tr("security.gpl_body"))
    win.lbl_gpl_info.setWordWrap(True)
    win.gpl_card.main_layout.addWidget(win.lbl_gpl_info)
    layout.addWidget(win.gpl_card)

    return wrap_page_in_scroll(page)
