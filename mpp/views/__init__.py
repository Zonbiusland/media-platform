# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Media Platform (Studio Master v1.0.0) — Paquete de Vistas Modulares (GPLv3+)
# Este archivo es software libre distribuido bajo la licencia GNU GPL v3.0 o posterior.
from ..core import *
from ..themes import *


def build_option_subcard(title_text: str) -> tuple[QGroupBox, QVBoxLayout]:
    """Crea un QGroupBox estilizado con márgenes holgados para evitar solapamiento del título."""
    box = QGroupBox(title_text)
    lay = QVBoxLayout(box)
    lay.setContentsMargins(14, 16, 14, 12)
    lay.setSpacing(10)
    return box, lay


def wrap_page_in_scroll(content_widget: QWidget) -> QScrollArea:
    """Envuelve una página en un QScrollArea elástico para impedir aplastamiento vertical."""
    content_widget.setObjectName("ScrollPageContent")
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setWidget(content_widget)
    return scroll


from .capturer import build_capturer_view
from .queue import build_queue_view, create_queue_progress_bar, set_queue_bar_completed
from .library import build_library_view
from .ffmpeg_lab import build_ffmpeg_lab_view
from .settings import build_settings_view, build_security_view

_build_option_subcard = build_option_subcard
_wrap_page_in_scroll = wrap_page_in_scroll

__all__ = [
    "build_option_subcard",
    "wrap_page_in_scroll",
    "_build_option_subcard",
    "_wrap_page_in_scroll",
    "build_capturer_view",
    "build_queue_view",
    "create_queue_progress_bar",
    "set_queue_bar_completed",
    "build_library_view",
    "build_ffmpeg_lab_view",
    "build_settings_view",
    "build_security_view",
]
