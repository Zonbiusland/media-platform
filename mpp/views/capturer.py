# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Media Platform (Studio Master v1.0.0) — Vista de Capturador y Calidad (GPLv3+)
# Este archivo es software libre distribuido bajo la licencia GNU GPL v3.0 o posterior.
from ..core import *
from ..themes import *
from . import build_option_subcard, wrap_page_in_scroll


def build_capturer_view(win) -> QScrollArea:
    """Construye la vista de Capturador y Calidad y vincula sus controles a MainWindow."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 6, 0)
    layout.setSpacing(12)

    # ── Tarjeta 1: Inspector Multimedia y Vista Previa ──
    win.insp_card = SurfaceCard(
        tr("capture.insp_title"),
        tr("capture.insp_sub")
    )

    hero_row = QHBoxLayout()
    hero_row.setSpacing(16)

    win.lbl_thumbnail = QLabel(tr("capture.no_preview"))
    win.lbl_thumbnail.setObjectName("ThumbnailBox")
    win.lbl_thumbnail.setFixedSize(210, 118)
    win.lbl_thumbnail.setAlignment(Qt.AlignCenter)
    hero_row.addWidget(win.lbl_thumbnail)

    right_meta = QVBoxLayout()
    right_meta.setSpacing(8)

    win.lbl_meta_title = QLabel(tr("capture.hero_idle"))
    win.lbl_meta_title.setObjectName("MediaHeroTitle")
    win.lbl_meta_title.setWordWrap(True)
    win._hero_is_idle = True
    right_meta.addWidget(win.lbl_meta_title)

    tiles_grid = QGridLayout()
    tiles_grid.setSpacing(8)

    win.card_platform = MetricTile(tr("capture.tile_origin"), "—")
    win.card_duration = MetricTile(tr("capture.tile_duration"), "—")
    win.card_res = MetricTile(tr("capture.tile_res"), "—")
    win.card_hdr = MetricTile(tr("capture.tile_hdr"), "—")
    win.card_codecs = MetricTile(tr("capture.tile_codecs"), "—")
    win.card_subs = MetricTile(tr("capture.tile_subs"), "—")
    win.card_size = MetricTile(tr("capture.tile_size"), "—")
    win.card_rec = MetricTile(tr("capture.tile_rec"), "MP4")

    tiles_grid.addWidget(win.card_platform, 0, 0)
    tiles_grid.addWidget(win.card_duration, 0, 1)
    tiles_grid.addWidget(win.card_res, 0, 2)
    tiles_grid.addWidget(win.card_hdr, 0, 3)
    tiles_grid.addWidget(win.card_codecs, 1, 0)
    tiles_grid.addWidget(win.card_subs, 1, 1)
    tiles_grid.addWidget(win.card_size, 1, 2)
    tiles_grid.addWidget(win.card_rec, 1, 3)

    right_meta.addLayout(tiles_grid)
    hero_row.addLayout(right_meta, stretch=1)
    win.insp_card.main_layout.addLayout(hero_row)
    layout.addWidget(win.insp_card)

    # ── Tarjeta 2: Opciones Agrupadas en QGroupBox sin solapamiento ──
    win.cfg_card = SurfaceCard(
        tr("capture.cfg_title_adv"),
        tr("capture.cfg_sub_adv")
    )

    # Bloque A: Formato, Resolución y Subtítulos
    win.sub_fmt_card, sub_fmt_lay = build_option_subcard(tr("capture.sub_fmt_title"))
    fmt_grid = QGridLayout()
    fmt_grid.setHorizontalSpacing(18)
    fmt_grid.setVerticalSpacing(12)
    fmt_grid.setColumnStretch(1, 1)
    fmt_grid.setColumnStretch(3, 1)

    win.lbl_quality = QLabel(tr("capture.lbl_quality"))
    win.lbl_quality.setObjectName("FieldLabel")
    fmt_grid.addWidget(win.lbl_quality, 0, 0)
    win.combo_quality = QComboBox()
    win.combo_quality.setMinimumHeight(34)
    win._quality_option_keys = [
        ("Mejor Calidad Disponible", "quality.best"),
        ("4320p (8K Ultra HD)", "quality.4320p"),
        ("2160p (4K UHD)", "quality.2160p"),
        ("1440p (2K QHD)", "quality.1440p"),
        ("1080p (Full HD)", "quality.1080p"),
        ("720p (HD)", "quality.720p"),
        ("480p (Estándar)", "quality.480p"),
        ("360p (Datos reducidos)", "quality.360p"),
        ("Solo Audio (MP3)", "quality.audio_mp3"),
        ("Solo Audio (FLAC)", "quality.audio_flac"),
        ("Solo Audio (M4A)", "quality.audio_m4a"),
        ("Solo Audio (OPUS)", "quality.audio_opus"),
        ("Solo Audio (WAV)", "quality.audio_wav"),
    ]
    for canonical_q, q_tr_key in win._quality_option_keys:
        win.combo_quality.addItem(tr(q_tr_key), canonical_q)
    fmt_grid.addWidget(win.combo_quality, 0, 1)

    win.lbl_container = QLabel(tr("capture.lbl_container"))
    win.lbl_container.setObjectName("FieldLabel")
    fmt_grid.addWidget(win.lbl_container, 0, 2)
    win.combo_container = QComboBox()
    win.combo_container.setMinimumHeight(34)
    win.combo_container.addItems(["MP4", "MKV", "WebM", "MOV"])
    fmt_grid.addWidget(win.combo_container, 0, 3)

    win.lbl_fragments = QLabel(tr("capture.lbl_fragments"))
    win.lbl_fragments.setObjectName("FieldLabel")
    fmt_grid.addWidget(win.lbl_fragments, 1, 0)
    win.spin_fragments = QSpinBox()
    win.spin_fragments.setMinimumHeight(34)
    win.spin_fragments.setRange(1, 32)
    win.spin_fragments.setValue(4)
    fmt_grid.addWidget(win.spin_fragments, 1, 1)

    win.chk_playlist = QCheckBox(tr("capture.chk_playlist"))
    win.chk_playlist.setMinimumHeight(26)
    win.chk_playlist.setChecked(False)
    fmt_grid.addWidget(win.chk_playlist, 1, 2, 1, 2)

    win.chk_subs = QCheckBox(tr("capture.chk_subs"))
    win.chk_subs.setMinimumHeight(26)
    fmt_grid.addWidget(win.chk_subs, 2, 0)

    win.combo_sub_langs = QComboBox()
    win.combo_sub_langs.setMinimumHeight(34)
    win.combo_sub_langs.addItems(SubtitleResolver.PRESETS)
    fmt_grid.addWidget(win.combo_sub_langs, 2, 1)

    win.chk_embed_subs = QCheckBox(tr("capture.chk_embed_subs"))
    win.chk_embed_subs.setMinimumHeight(26)
    fmt_grid.addWidget(win.chk_embed_subs, 2, 2, 1, 2)

    sub_fmt_lay.addLayout(fmt_grid)
    win.cfg_card.main_layout.addWidget(win.sub_fmt_card)

    # Fila inferior con 2 bloques técnicos en paralelo (ocultos en Modo Simple, visibles en Modo Avanzado)
    win.advanced_blocks_container = QWidget()
    bottom_cards_row = QHBoxLayout(win.advanced_blocks_container)
    bottom_cards_row.setContentsMargins(0, 0, 0, 0)
    bottom_cards_row.setSpacing(14)

    # Bloque B: Filtro de Patrocinios y Promociones (desactivados por defecto para no alterar contenido sin permiso)
    win.sub_sp_card, sub_sp_lay = build_option_subcard(tr("capture.sub_sp_title"))
    sub_sp_lay.setSpacing(9)
    win.chk_sponsorblock = QCheckBox(tr("capture.chk_sponsorblock"))
    win.chk_sponsorblock.setMinimumHeight(26)
    win.chk_sponsorblock.setChecked(False)
    win.chk_sponsorblock.setToolTip("Consulta la base de datos de SponsorBlock para eliminar segmentos promocionales")
    sub_sp_lay.addWidget(win.chk_sponsorblock)

    win.chk_smart_sponsor = QCheckBox(tr("capture.chk_smart_sponsor"))
    win.chk_smart_sponsor.setMinimumHeight(26)
    win.chk_smart_sponsor.setChecked(False)
    win.chk_smart_sponsor.setToolTip(
        "Respaldo automático si SponsorBlock devuelve 0 tramos: analiza subtítulos VTT/SRT "
        "(o faster-whisper 'base') buscando bloques patrocinados en español e inglés y los recorta "
        "sin pérdida de calidad con FFmpeg (-c copy)."
    )
    sub_sp_lay.addWidget(win.chk_smart_sponsor)

    win.chk_loudnorm = QCheckBox(tr("capture.chk_loudnorm"))
    win.chk_loudnorm.setMinimumHeight(26)
    win.chk_loudnorm.setChecked(False)
    win.chk_loudnorm.setToolTip("Ajusta la sonoridad percibida al estándar de streaming (-14 LUFS)")
    sub_sp_lay.addWidget(win.chk_loudnorm)

    win.chk_thumbnail = QCheckBox(tr("capture.chk_thumbnail"))
    win.chk_thumbnail.setMinimumHeight(26)
    win.chk_thumbnail.setChecked(False)
    sub_sp_lay.addWidget(win.chk_thumbnail)
    sub_sp_lay.addStretch(1)

    # Bloque C: Recorte Temporal, Capítulos y Directos
    win.sub_proc_card, sub_proc_lay = build_option_subcard(tr("capture.sub_proc_title"))
    sub_proc_lay.setSpacing(9)

    trim_row = QHBoxLayout()
    trim_row.setSpacing(8)
    win.chk_trim = QCheckBox(tr("capture.chk_trim"))
    win.chk_trim.setMinimumHeight(26)
    trim_row.addWidget(win.chk_trim)
    win.input_trim_start = QLineEdit("00:00:00")
    win.input_trim_start.setMinimumHeight(32)
    win.input_trim_start.setMinimumWidth(90)
    win.input_trim_start.setMaximumWidth(110)
    win.input_trim_start.setAlignment(Qt.AlignCenter)
    win.input_trim_end = QLineEdit("00:05:00")
    win.input_trim_end.setMinimumHeight(32)
    win.input_trim_end.setMinimumWidth(90)
    win.input_trim_end.setMaximumWidth(110)
    win.input_trim_end.setAlignment(Qt.AlignCenter)
    win.lbl_trim_to = QLabel(tr("capture.lbl_trim_to"))
    trim_row.addWidget(win.input_trim_start)
    trim_row.addWidget(win.lbl_trim_to)
    trim_row.addWidget(win.input_trim_end)
    trim_row.addStretch(1)
    sub_proc_lay.addLayout(trim_row)

    win.chk_split_chapters = QCheckBox(tr("capture.chk_split_chapters"))
    win.chk_split_chapters.setMinimumHeight(26)
    sub_proc_lay.addWidget(win.chk_split_chapters)

    win.chk_live_start = QCheckBox(tr("capture.chk_live_start"))
    win.chk_live_start.setMinimumHeight(26)
    sub_proc_lay.addWidget(win.chk_live_start)
    sub_proc_lay.addStretch(1)

    bottom_cards_row.addWidget(win.sub_sp_card, stretch=1)
    bottom_cards_row.addWidget(win.sub_proc_card, stretch=1)
    win.cfg_card.main_layout.addWidget(win.advanced_blocks_container)

    # Lista de controles técnicos que se ocultan en Modo Simple y se muestran en Modo Avanzado
    win._capturer_advanced_widgets = [
        win.lbl_fragments,
        win.spin_fragments,
        win.chk_playlist,
        win.chk_subs,
        win.combo_sub_langs,
        win.chk_embed_subs,
        win.advanced_blocks_container,
    ]

    layout.addWidget(win.cfg_card)

    # ── Tarjeta 3: Directorio de Salida ──
    win.dest_card = SurfaceCard()
    dest_box = QHBoxLayout()
    dest_box.setContentsMargins(0, 0, 0, 0)
    dest_box.setSpacing(10)

    win.lbl_save_in = QLabel(tr("capture.lbl_save_in"))
    win.lbl_save_in.setObjectName("FieldLabel")
    dest_box.addWidget(win.lbl_save_in)
    win.input_dir = QLineEdit(win.download_dir)
    win.input_dir.setReadOnly(True)
    win.input_dir.setMinimumHeight(34)
    dest_box.addWidget(win.input_dir, stretch=1)

    win.btn_ch_dir = QPushButton(tr("capture.btn_change_dir"))
    win.btn_ch_dir.setMinimumHeight(34)
    win.btn_ch_dir.setToolTip("Selecciona la carpeta donde se guardarán las descargas")
    win.btn_ch_dir.clicked.connect(win.select_folder)
    dest_box.addWidget(win.btn_ch_dir)

    win.btn_open_dir = QPushButton(tr("capture.btn_open_dir"))
    win.btn_open_dir.setMinimumHeight(34)
    win.btn_open_dir.setToolTip("Abre la carpeta de descargas en el explorador de archivos del sistema")
    win.btn_open_dir.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(win.download_dir)))
    dest_box.addWidget(win.btn_open_dir)

    win.dest_card.main_layout.addLayout(dest_box)
    layout.addWidget(win.dest_card)
    layout.addStretch(1)
    return wrap_page_in_scroll(page)
