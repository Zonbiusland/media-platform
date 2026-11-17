# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Media Platform (Studio Master v1.0.0) — Vista de Laboratorio FFmpeg (GPLv3+)
# Este archivo es software libre distribuido bajo la licencia GNU GPL v3.0 o posterior.
from ..core import *
from ..themes import *
from . import build_option_subcard, wrap_page_in_scroll


def build_ffmpeg_lab_view(win) -> QScrollArea:
    """Construye la vista de Laboratorio FFmpeg y vincula sus controles a MainWindow."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 6, 0)
    layout.setSpacing(12)

    win.ff_card = SurfaceCard(
        tr("ffmpeg.card_title"),
        tr("ffmpeg.card_sub")
    )

    win.sub_ff_card, sub_ff_lay = build_option_subcard(tr("ffmpeg.sub_params"))
    grid = QGridLayout()
    grid.setHorizontalSpacing(16)
    grid.setVerticalSpacing(12)
    grid.setColumnStretch(1, 1)

    win.lbl_ff_in = QLabel(tr("ffmpeg.lbl_input"))
    win.lbl_ff_in.setObjectName("FieldLabel")
    grid.addWidget(win.lbl_ff_in, 0, 0)
    win.input_ff_in = QLineEdit()
    win.input_ff_in.setMinimumHeight(34)
    win.input_ff_in.setPlaceholderText(tr("ffmpeg.input_placeholder"))
    grid.addWidget(win.input_ff_in, 0, 1)

    win.btn_ff_browse = QPushButton(tr("ffmpeg.btn_browse"))
    win.btn_ff_browse.setMinimumHeight(34)
    win.btn_ff_browse.setToolTip(tr("ffmpeg.btn_browse_tip"))
    win.btn_ff_browse.clicked.connect(win.select_ffmpeg_input)
    grid.addWidget(win.btn_ff_browse, 0, 2)

    win.lbl_ff_op = QLabel(tr("ffmpeg.lbl_op"))
    win.lbl_ff_op.setObjectName("FieldLabel")
    grid.addWidget(win.lbl_ff_op, 1, 0)
    win.combo_ff_op = QComboBox()
    win.combo_ff_op.setMinimumHeight(34)
    win._ff_op_keys = [
        ("remux_mp4", "ffmpeg.op_remux_mp4"),
        ("remux_mkv", "ffmpeg.op_remux_mkv"),
        ("compress_10", "ffmpeg.op_compress_10"),
        ("compress_25", "ffmpeg.op_compress_25"),
        ("compress_50", "ffmpeg.op_compress_50"),
        ("loudnorm_video", "ffmpeg.op_loudnorm_video"),
        ("loudnorm_audio", "ffmpeg.op_loudnorm_audio"),
        ("audio_mp3", "ffmpeg.op_audio_mp3"),
        ("convert_mp4", "ffmpeg.op_convert_mp4"),
        ("gif", "ffmpeg.op_gif"),
    ]
    for op_code, op_tr_key in win._ff_op_keys:
        win.combo_ff_op.addItem(tr(op_tr_key), op_code)
    grid.addWidget(win.combo_ff_op, 1, 1, 1, 2)

    win.lbl_ff_hw = QLabel(tr("ffmpeg.lbl_hw"))
    win.lbl_ff_hw.setObjectName("FieldLabel")
    grid.addWidget(win.lbl_ff_hw, 2, 0)
    win.combo_hw = QComboBox()
    win.combo_hw.setMinimumHeight(34)
    win.combo_hw.addItems([
        "nvenc (GPU NVIDIA NVENC)",
        "cpu (Software libx264)",
        "qsv (Intel Quick Sync)",
        "amf (GPU AMD AMF)"
    ])
    grid.addWidget(win.combo_hw, 2, 1, 1, 2)

    win.btn_run_ff = QPushButton(tr("ffmpeg.btn_run"))
    win.btn_run_ff.setMinimumHeight(38)
    win.btn_run_ff.setObjectName("AccentButton")
    win.btn_run_ff.clicked.connect(win.run_ffmpeg_tool)
    grid.addWidget(win.btn_run_ff, 3, 0, 1, 3)

    sub_ff_lay.addLayout(grid)
    win.ff_card.main_layout.addWidget(win.sub_ff_card)

    win.lbl_probe_hdr = QLabel(tr("ffmpeg.lbl_console"))
    win.lbl_probe_hdr.setObjectName("CardSub")
    win.ff_card.main_layout.addWidget(win.lbl_probe_hdr)

    win.txt_ffprobe = QTextEdit()
    win.txt_ffprobe.setReadOnly(True)
    win.txt_ffprobe.setMinimumHeight(200)
    mono_font = QFont("DejaVu Sans Mono", 9.5)
    mono_font.setStyleHint(QFont.Monospace)
    win.txt_ffprobe.setFont(mono_font)
    win.txt_ffprobe.setPlaceholderText(tr("ffmpeg.console_placeholder"))
    win.ff_card.main_layout.addWidget(win.txt_ffprobe, stretch=1)

    layout.addWidget(win.ff_card, stretch=1)
    return wrap_page_in_scroll(page)
