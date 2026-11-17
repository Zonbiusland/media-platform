# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Media Platform (Studio Master v1.0.0) — Vista de Cola de Transferencias (GPLv3+)
# Este archivo es software libre distribuido bajo la licencia GNU GPL v3.0 o posterior.
from ..core import *
from ..themes import *
from PySide6.QtCore import QByteArray, QRectF
from PySide6.QtSvg import QSvgRenderer


class DragonForgeQueueTable(QTableWidget):
    """Tabla de cola con dragon_watermark.png (transparencia + resplandor cálido) cacheado al 22%."""
    _wm_cache = {}

    @classmethod
    def _get_cached_dragon_svg_pixmap(
        cls,
        gold_hex: str = "#C59B5F",
        copper_hex: str = "#7A4B26",
        width: int = 280,
        height: int = 210,
        opacity: float = 0.22
    ) -> QPixmap:
        key = (str(gold_hex).upper(), str(copper_hex).upper(), int(width), int(height), round(opacity, 2))
        cached = cls._wm_cache.get(key)
        if cached is not None:
            return cached

        png_wm = load_transparent_asset("dragon_watermark.png", opacity=opacity, target_size=(width, height))
        if not png_wm.isNull():
            glow_pm = QPixmap(png_wm.size())
            glow_pm.fill(Qt.transparent)
            p_g = QPainter(glow_pm)
            if p_g.isActive():
                gw, gh = float(png_wm.width()), float(png_wm.height())
                halo = QRadialGradient(gw * 0.52, gh * 0.52, max(gw, gh) * 0.50)
                halo.setColorAt(0.0, QColor(245, 158, 11, int(255 * min(0.14, opacity * 0.48))))
                halo.setColorAt(0.55, QColor(197, 155, 95, int(255 * min(0.08, opacity * 0.28))))
                halo.setColorAt(1.0, QColor(122, 75, 38, 0))
                p_g.fillRect(0, 0, png_wm.width(), png_wm.height(), halo)
                p_g.drawPixmap(0, 0, png_wm)
                p_g.end()
            cls._wm_cache[key] = glow_pm
            return glow_pm

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240">
  <defs>
    <linearGradient id="crestBronze" x1="12%" y1="10%" x2="88%" y2="90%">
      <stop offset="0%" stop-color="{gold_hex}"/>
      <stop offset="52%" stop-color="#A6743E"/>
      <stop offset="100%" stop-color="{copper_hex}"/>
    </linearGradient>
    <radialGradient id="crestHalo" cx="50%" cy="50%" r="48%">
      <stop offset="0%" stop-color="{gold_hex}" stop-opacity="0.32"/>
      <stop offset="70%" stop-color="{copper_hex}" stop-opacity="0.14"/>
      <stop offset="100%" stop-color="{copper_hex}" stop-opacity="0.0"/>
    </radialGradient>
  </defs>

  <!-- Medallón circular grabado con muescas heráldicas -->
  <circle cx="120" cy="120" r="102" fill="url(#crestHalo)"/>
  <circle cx="120" cy="120" r="98" fill="none" stroke="url(#crestBronze)" stroke-width="3.2"/>
  <circle cx="120" cy="120" r="89" fill="none" stroke="{gold_hex}" stroke-width="1.2" stroke-dasharray="10 5 3 5"/>
  <circle cx="120" cy="120" r="78" fill="none" stroke="{copper_hex}" stroke-width="1.0" stroke-opacity="0.8"/>

  <!-- Marcas cardinales del escudo circular -->
  <g fill="url(#crestBronze)">
    <polygon points="120,14 124,25 120,30 116,25"/>
    <polygon points="120,226 124,215 120,210 116,215"/>
    <polygon points="14,120 25,116 30,120 25,124"/>
    <polygon points="226,120 215,116 210,120 215,124"/>
  </g>

  <!-- Ala orgánica asimétrica desplegada hacia el cuadrante superior derecho -->
  <path d="M108 112 C112 82 135 55 170 43 C186 38 197 44 203 55
           C188 57 179 65 186 76 C168 74 159 83 166 95 C148 93 139 102 142 114
           C129 109 117 110 108 112 Z"
        fill="url(#crestBronze)" fill-opacity="0.62" stroke="{copper_hex}" stroke-width="2.0" stroke-linejoin="round"/>
  <path d="M112 108 Q148 70 198 54 M117 110 Q149 85 182 75 M122 111 Q143 97 162 94"
        fill="none" stroke="{gold_hex}" stroke-width="1.5" stroke-linecap="round"/>

  <!-- Dragón heráldico orgánico enroscado en perfil sinuoso -->
  <path d="M84 57 C74 49 62 49 52 54 L65 59 L53 67 C63 69 70 68 76 72
           C69 83 68 98 76 112 C84 127 83 145 94 160 C107 177 132 183 153 175
           C174 167 187 146 183 125 C180 110 166 105 159 114 C154 121 163 127 168 122
           C173 135 164 153 147 160 C128 167 109 159 104 143 C99 128 108 114 105 97
           C102 82 95 72 100 63 C106 52 117 47 125 41 L110 42 L117 32 C104 36 93 43 87 51
           L78 40 Z"
        fill="url(#crestBronze)" stroke="{copper_hex}" stroke-width="2.2" stroke-linejoin="round"/>

  <!-- Cresta dorsal, garra anterior y lengüeta orgánica -->
  <path d="M98 75 L90 79 L97 86 L89 92 L98 99 L91 106 L99 113"
        fill="none" stroke="{gold_hex}" stroke-width="1.6" stroke-linejoin="round"/>
  <path d="M82 114 L67 123 M84 119 L72 130 M55 62 Q43 63 39 70"
        fill="none" stroke="{gold_hex}" stroke-width="1.9" stroke-linecap="round"/>
</svg>"""

        raw_pm = QPixmap(width, height)
        raw_pm.fill(Qt.transparent)
        p_raw = QPainter(raw_pm)
        p_raw.setRenderHint(QPainter.Antialiasing, True)
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        renderer.render(p_raw, QRectF(0.0, 0.0, float(width), float(height)))
        p_raw.end()

        pm = QPixmap(width, height)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setOpacity(opacity)
        p.drawPixmap(0, 0, raw_pm)
        p.end()

        cls._wm_cache[key] = pm
        return pm

    def paintEvent(self, event):
        super().paintEvent(event)
        vp = self.viewport()
        if vp is None or vp.width() < 130 or vp.height() < 120:
            return

        y_start = 0
        rc = self.rowCount()
        if rc > 0:
            y_start = max(0, self.rowViewportPosition(rc - 1) + self.rowHeight(rc - 1))
        if y_start >= vp.height() - 28:
            return

        win = self.window()
        t = getattr(win, "_active_ergonomic_theme", None) if win else None
        if not isinstance(t, dict):
            t = ErgonomicThemeEngine.PRESETS[ErgonomicThemeEngine.DEFAULT_PRESET]

        gold_hex = str(t.get("border_gold", "#C59B5F"))
        copper_hex = str(t.get("border", "#7A4B26"))
        wm = self._get_cached_dragon_svg_pixmap(
            gold_hex=gold_hex, copper_hex=copper_hex, width=280, height=210, opacity=0.22
        )

        p = QPainter(vp)
        if not p.isActive():
            return
        p.setClipRect(0, y_start, vp.width(), vp.height() - y_start)
        p.drawPixmap(vp.width() - wm.width() - 16, vp.height() - wm.height() - 12, wm)
        p.end()


def create_queue_progress_bar() -> tuple[QWidget, QProgressBar]:
    """Crea la cápsula QProgressBar de fila con propiedades dinámicas iniciales."""
    holder = QWidget()
    holder.setStyleSheet("background: transparent; border: none;")
    lay = QVBoxLayout(holder)
    lay.setContentsMargins(6, 5, 6, 5)
    pbar = QProgressBar()
    pbar.setRange(0, 100)
    pbar.setFixedHeight(20)
    pbar.setProperty("hasProgress", False)
    pbar.setProperty("completed", False)
    pbar._has_prog_state = False
    pbar._completed_state = False
    pbar.setValue(0)
    lay.addWidget(pbar)
    return holder, pbar


def set_queue_bar_completed(pbar: QProgressBar | None, completed: bool):
    """Activa o desactiva el estado visual 'Forja Incandescente' en una barra de la cola."""
    if pbar is None:
        return
    done = bool(completed)
    if getattr(pbar, "_completed_state", None) != done:
        pbar._completed_state = done
        pbar.setProperty("completed", done)
        pbar.style().unpolish(pbar)
        pbar.style().polish(pbar)


class DragonForgeFrame(SurfaceCard):
    """Marco principal de Cola de Transferencias con ornamentos laterales 'Brasero / Dragón de Fuego'."""
    def paintEvent(self, event):
        super().paintEvent(event)
        if not bool(self.property("headerSummary")):
            return
        w, h = self.width(), self.height()
        if w < 64 or h < 72:
            return
        left_pm, right_pm = ErgonomicThemeEngine.get_side_brazier_pixmaps(14, 56)
        cy = (h - left_pm.height()) // 2
        p = QPainter(self)
        if not p.isActive():
            return
        if event is not None:
            p.setClipRect(event.rect())
        p.drawPixmap(0, cy, left_pm)
        p.drawPixmap(w - right_pm.width(), cy, right_pm)
        p.end()


def build_queue_view(win) -> QWidget:
    """Construye la vista de Cola de Transferencias y vincula sus controles a MainWindow."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)

    win.queue_card = DragonForgeFrame(
        tr("queue.card_title"),
        tr("queue.card_sub")
    )
    win.queue_card.setProperty("headerSummary", True)

    toolbar = QHBoxLayout()
    toolbar.setSpacing(6)

    win.btn_import_txt = QPushButton(tr("queue.btn_import_txt"))
    win.btn_import_txt.setObjectName("CompactActionBtn")
    win.btn_import_txt.setMinimumHeight(32)
    win.btn_import_txt.setToolTip("Importa una lista de enlaces desde un archivo .txt o .csv")
    win.btn_import_txt.clicked.connect(win.import_batch_file)
    toolbar.addWidget(win.btn_import_txt)

    win.btn_import_clip = QPushButton(tr("queue.btn_paste_batch"))
    win.btn_import_clip.setObjectName("CompactActionBtn")
    win.btn_import_clip.setMinimumHeight(32)
    win.btn_import_clip.setToolTip("Encola múltiples enlaces copiados en el portapapeles")
    win.btn_import_clip.clicked.connect(win.import_from_clipboard)
    toolbar.addWidget(win.btn_import_clip)

    toolbar.addStretch()

    win.btn_pause_q = QPushButton(tr("queue.btn_pause"))
    win.btn_pause_q.setObjectName("CompactActionBtn")
    win.btn_pause_q.setMinimumHeight(32)
    win.btn_pause_q.setToolTip("Pausa temporalmente las descargas seleccionadas")
    win.btn_pause_q.clicked.connect(win.pause_selected)
    toolbar.addWidget(win.btn_pause_q)

    win.btn_resume_q = QPushButton(tr("queue.btn_resume"))
    win.btn_resume_q.setObjectName("CompactActionBtn")
    win.btn_resume_q.setMinimumHeight(32)
    win.btn_resume_q.setToolTip("Reanuda las descargas seleccionadas que estén en pausa")
    win.btn_resume_q.clicked.connect(win.resume_selected)
    toolbar.addWidget(win.btn_resume_q)

    win.btn_retry_q = QPushButton(tr("queue.btn_retry"))
    win.btn_retry_q.setObjectName("CompactActionBtn")
    win.btn_retry_q.setMinimumHeight(32)
    win.btn_retry_q.setToolTip("Vuelve a poner en cola las tareas fallidas o canceladas seleccionadas")
    win.btn_retry_q.clicked.connect(win.retry_selected)
    toolbar.addWidget(win.btn_retry_q)

    win.btn_force_redownload_q = QPushButton(tr("queue.btn_force_redownload"))
    win.btn_force_redownload_q.setObjectName("CompactActionBtn")
    win.btn_force_redownload_q.setMinimumHeight(32)
    win.btn_force_redownload_q.setToolTip(tr("queue.btn_force_redownload_tip"))
    win.btn_force_redownload_q.clicked.connect(win.force_redownload_selected)
    toolbar.addWidget(win.btn_force_redownload_q)

    win.btn_cancel_q = QPushButton(tr("queue.btn_cancel"))
    win.btn_cancel_q.setObjectName("CancelQueueBtn")
    win.btn_cancel_q.setMinimumHeight(32)
    win.btn_cancel_q.setToolTip("Detiene la descarga seleccionada")
    win.btn_cancel_q.clicked.connect(win.cancel_selected)
    toolbar.addWidget(win.btn_cancel_q)

    win.btn_remove_q = QPushButton(tr("queue.btn_remove"))
    win.btn_remove_q.setObjectName("DangerButton")
    win.btn_remove_q.setMinimumHeight(32)
    win.btn_remove_q.setToolTip("Elimina las filas seleccionadas y limpia sus archivos temporales .part")
    win.btn_remove_q.clicked.connect(win.remove_selected_from_queue)
    toolbar.addWidget(win.btn_remove_q)

    win.btn_clear_inactive_q = QPushButton(tr("queue.btn_clear_inactive"))
    win.btn_clear_inactive_q.setObjectName("CompactActionBtn")
    win.btn_clear_inactive_q.setMinimumHeight(32)
    win.btn_clear_inactive_q.setToolTip("Retira de la tabla todas las tareas completadas, canceladas o con error")
    win.btn_clear_inactive_q.clicked.connect(win.clear_inactive_queue)
    toolbar.addWidget(win.btn_clear_inactive_q)

    win.queue_card.main_layout.addLayout(toolbar)

    win.table_queue = DragonForgeQueueTable(0, 5)
    win.table_queue.setHorizontalHeaderLabels([
        tr("queue.col_title"),
        tr("queue.col_format"),
        tr("queue.col_progress"),
        tr("queue.col_speed"),
        tr("queue.col_status"),
    ])
    win.table_queue.horizontalHeader().setStretchLastSection(False)
    win.table_queue.horizontalHeader().setMinimumSectionSize(110)
    win.table_queue.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    win.table_queue.setColumnWidth(0, 360)
    win.table_queue.setTextElideMode(Qt.ElideRight)
    win.table_queue.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
    win.table_queue.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
    win.table_queue.setColumnWidth(2, 185)
    win.table_queue.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
    win.table_queue.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive)
    win.table_queue.setColumnWidth(4, 235)
    win.table_queue.setSelectionBehavior(QAbstractItemView.SelectRows)
    win.table_queue.setEditTriggers(QAbstractItemView.NoEditTriggers)
    win.table_queue.setAlternatingRowColors(True)
    win.table_queue.verticalHeader().setVisible(False)
    win.table_queue.verticalHeader().setDefaultSectionSize(44)
    win.table_queue.setContextMenuPolicy(Qt.CustomContextMenu)
    win.table_queue.customContextMenuRequested.connect(win.show_queue_context_menu)

    win.queue_card.main_layout.addWidget(win.table_queue, stretch=1)

    log_header = QHBoxLayout()
    win.lbl_qlog = QLabel(tr("queue.lbl_log"))
    win.lbl_qlog.setObjectName("CardSub")
    log_header.addWidget(win.lbl_qlog)
    log_header.addStretch()
    win.btn_clear_log = QPushButton(tr("queue.btn_clear_log"))
    win.btn_clear_log.setObjectName("CompactActionBtn")
    win.btn_clear_log.setMinimumHeight(28)
    win.btn_clear_log.setToolTip("Borra el historial de mensajes de la consola inferior")
    win.btn_clear_log.clicked.connect(lambda: win.txt_download_log.clear())
    log_header.addWidget(win.btn_clear_log)
    win.queue_card.main_layout.addLayout(log_header)

    win.txt_download_log = QTextEdit()
    win.txt_download_log.setReadOnly(True)
    win.txt_download_log.setMinimumHeight(95)
    win.txt_download_log.setMaximumHeight(130)
    win.txt_download_log.setPlaceholderText(tr("queue.log_placeholder"))
    qlog_font = QFont("DejaVu Sans Mono", 9)
    qlog_font.setStyleHint(QFont.Monospace)
    win.txt_download_log.setFont(qlog_font)
    win.queue_card.main_layout.addWidget(win.txt_download_log)

    post_bar = QHBoxLayout()
    post_bar.setSpacing(10)
    win.lbl_post_action = QLabel(tr("queue.lbl_post_action"))
    win.lbl_post_action.setObjectName("FieldLabel")
    post_bar.addWidget(win.lbl_post_action)
    win.combo_post_action = QComboBox()
    win.combo_post_action.setMinimumHeight(34)
    win._post_action_keys = [
        ("notify", "queue.post_notify"),
        ("open_dir", "queue.post_open_dir"),
        ("quit", "queue.post_quit"),
        ("sleep", "queue.post_sleep"),
        ("shutdown", "queue.post_shutdown"),
    ]
    for action_id, post_tr_key in win._post_action_keys:
        win.combo_post_action.addItem(tr(post_tr_key), action_id)
    post_bar.addWidget(win.combo_post_action)
    post_bar.addStretch()
    win.queue_card.main_layout.addLayout(post_bar)

    layout.addWidget(win.queue_card, stretch=1)
    return page
