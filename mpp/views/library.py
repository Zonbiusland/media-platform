# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Media Platform (Studio Master v1.0.0) — Vista de Videoteca Local (GPLv3+)
# Este archivo es software libre distribuido bajo la licencia GNU GPL v3.0 o posterior.
from ..core import *
from ..themes import *


def build_library_view(win) -> QWidget:
    """Construye la vista de Videoteca Local y vincula sus controles a MainWindow."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    win.lib_card = SurfaceCard(
        tr("library.card_title"),
        tr("library.card_sub")
    )

    search_bar = QHBoxLayout()
    search_bar.setSpacing(8)
    win.lib_search_timer = QTimer(win)
    win.lib_search_timer.setSingleShot(True)
    win.lib_search_timer.setInterval(200)
    win.lib_search_timer.timeout.connect(win.refresh_library)

    win.input_lib_search = QLineEdit()
    win.input_lib_search.setMinimumHeight(34)
    win.input_lib_search.setPlaceholderText(tr("library.search_placeholder"))
    win.input_lib_search.textChanged.connect(lambda _t: win.lib_search_timer.start())
    search_bar.addWidget(win.input_lib_search, stretch=1)

    win.btn_play_lib = QPushButton(tr("library.btn_play"))
    win.btn_play_lib.setMinimumHeight(34)
    win.btn_play_lib.setObjectName("AccentButton")
    win.btn_play_lib.setToolTip("Abre el archivo seleccionado con el reproductor multimedia del sistema")
    win.btn_play_lib.clicked.connect(win.play_selected_library)
    search_bar.addWidget(win.btn_play_lib)

    win.btn_locate_lib = QPushButton(tr("library.btn_locate"))
    win.btn_locate_lib.setMinimumHeight(34)
    win.btn_locate_lib.setToolTip("Resalta el archivo seleccionado en el gestor de archivos")
    win.btn_locate_lib.clicked.connect(win.locate_selected_library)
    search_bar.addWidget(win.btn_locate_lib)

    win.btn_del_item_lib = QPushButton(tr("library.btn_delete"))
    win.btn_del_item_lib.setMinimumHeight(34)
    win.btn_del_item_lib.setToolTip("Borra la entrada seleccionada del historial SQLite (sin borrar el archivo en disco)")
    win.btn_del_item_lib.clicked.connect(win.delete_selected_library_row)
    search_bar.addWidget(win.btn_del_item_lib)

    win.btn_clear_lib = QPushButton(tr("library.btn_clear"))
    win.btn_clear_lib.setMinimumHeight(34)
    win.btn_clear_lib.setObjectName("DangerButton")
    win.btn_clear_lib.setToolTip("Limpia todos los registros históricos de la base de datos SQLite")
    win.btn_clear_lib.clicked.connect(win.clear_library)
    search_bar.addWidget(win.btn_clear_lib)

    win.lib_card.main_layout.addLayout(search_bar)

    win.table_lib = QTableWidget(0, 7)
    win.table_lib.setHorizontalHeaderLabels([
        "Título", "Canal", "Plataforma", "Calidad", "SHA-256", "Fecha", "Ruta"
    ])
    win.table_lib.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    win.table_lib.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
    win.table_lib.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
    win.table_lib.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
    win.table_lib.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
    win.table_lib.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
    win.table_lib.horizontalHeader().setSectionResizeMode(6, QHeaderView.Interactive)
    win.table_lib.setColumnWidth(6, 220)
    win.table_lib.setSelectionBehavior(QAbstractItemView.SelectRows)
    win.table_lib.setEditTriggers(QAbstractItemView.NoEditTriggers)
    win.table_lib.setAlternatingRowColors(True)
    win.table_lib.verticalHeader().setVisible(False)
    win.table_lib.verticalHeader().setDefaultSectionSize(38)
    win.table_lib.itemDoubleClicked.connect(lambda _item: win.play_selected_library())
    win.lib_card.main_layout.addWidget(win.table_lib, stretch=1)

    layout.addWidget(win.lib_card, stretch=1)
    return page
