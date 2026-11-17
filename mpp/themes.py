# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# Media Platform (Studio Master) — Motor de Temas y Gráficos Vectoriales Libres (GPLv3+)
# Este archivo es software libre distribuido bajo la licencia GNU GPL v3.0 o posterior.
from .core import *
from .i18n import tr
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF, QRect, QByteArray
from PySide6.QtGui import (
    QColor, QPixmap, QImage, QPainter, QPen, QBrush, QPolygonF, QPainterPath, QIcon,
    QLinearGradient, QRadialGradient
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QWidget, QFrame, QLabel, QPushButton, QLineEdit, QComboBox,
    QSpinBox, QCheckBox, QRadioButton, QGroupBox, QProgressBar,
    QTableWidget, QListWidget, QStackedWidget, QVBoxLayout,
    QHBoxLayout, QGridLayout, QColorDialog, QTextEdit, QScrollArea,
    QGraphicsDropShadowEffect
)


class ErgonomicThemeEngine:
    APP_DIR = get_portable_data_dir()
    ICON_DIR = os.path.join(APP_DIR, "ui_icons")
    DEFAULT_PRESET = "Dragon Forge (Obsidiana y Oro)"
    # Familias tipográficas 100% libres (SIL OFL / Ubuntu Font Licence / Bitstream Vera)
    UI_FONT_STACK = '"Noto Sans", "Ubuntu", "Cantarell", "DejaVu Sans", "Liberation Sans", sans-serif'
    MONO_FONT_STACK = '"JetBrains Mono", "DejaVu Sans Mono", "Liberation Mono", "Ubuntu Mono", monospace'
    _cached_icon_key = None
    _cached_icon_paths = None
    _cached_scale_brushes = {}
    _cached_sidebar_scale_brushes = {}
    _cached_transparent_assets = {}
    _cached_corner_pixmaps = {}
    _cached_rivet_pixmaps = {}
    _cached_brazier_pixmaps = {}
    _cached_app_emblems = {}
    _cached_nav_icons = {}

    @classmethod
    def load_transparent_asset(
        cls,
        filename: str,
        opacity: float = 1.0,
        target_size: tuple[int, int] | None = None
    ) -> QPixmap:
        """Carga un PNG de mpp/assets/, convierte fondo negro (luminancia < 18) en alfa suave y lo cachea."""
        norm_op = max(0.0, min(1.0, float(opacity)))
        norm_sz = (int(target_size[0]), int(target_size[1])) if target_size else None
        cache_key = (str(filename), round(norm_op, 3), norm_sz)
        cached = cls._cached_transparent_assets.get(cache_key)
        if cached is not None:
            return cached

        if os.path.isabs(str(filename)) and os.path.isfile(str(filename)):
            asset_path = str(filename)
        else:
            asset_path = resource_path(os.path.join("mpp", "assets", os.path.basename(str(filename))))

        if not asset_path or not os.path.isfile(asset_path):
            return QPixmap()

        img = QImage(asset_path)
        if img.isNull():
            return QPixmap()

        if norm_sz is not None:
            img = img.scaled(norm_sz[0], norm_sz[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif max(img.width(), img.height()) > 512:
            img = img.scaled(512, 512, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        img = img.convertToFormat(QImage.Format_RGBA8888)
        buf = bytearray(img.constBits())
        total = len(buf)
        scale_op = norm_op if norm_op < 0.999 else 1.0

        for idx in range(0, total, 4):
            r = buf[idx]
            g = buf[idx + 1]
            b = buf[idx + 2]
            lum = (77 * r + 150 * g + 29 * b) >> 8
            if lum < 18:
                buf[idx + 3] = 0
            elif lum < 42:
                alpha_val = ((lum - 18) * 255) // 24
                buf[idx + 3] = int(alpha_val * scale_op) if scale_op < 1.0 else alpha_val
            else:
                buf[idx + 3] = int(255 * scale_op) if scale_op < 1.0 else 255

        out_img = QImage(bytes(buf), img.width(), img.height(), img.bytesPerLine(), QImage.Format_RGBA8888).copy()
        pm = QPixmap.fromImage(out_img)
        cls._cached_transparent_assets[cache_key] = pm
        return pm

    @classmethod
    def get_sidebar_scales_brush(cls, tile_size: int = 160, dark_overlay_alpha: int = 140) -> QBrush:
        """Pre-renderiza y cachea scales_tile.png escalado a 160x160 con superposición oscura al ~55%."""
        key = (int(tile_size), int(dark_overlay_alpha))
        cached = cls._cached_sidebar_scale_brushes.get(key)
        if cached is not None:
            return cached

        asset_path = resource_path(os.path.join("mpp", "assets", "scales_tile.png"))
        if asset_path and os.path.isfile(asset_path):
            raw = QPixmap(asset_path)
            if not raw.isNull():
                tile = raw.scaled(tile_size, tile_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                p = QPainter(tile)
                if p.isActive():
                    p.fillRect(0, 0, tile_size, tile_size, QColor(12, 7, 9, dark_overlay_alpha))
                    p.end()
                brush = QBrush(tile)
                cls._cached_sidebar_scale_brushes[key] = brush
                return brush

        fallback = cls.get_dragon_scale_brush("#9E6F3E", "#E0B866", alpha=18)
        cls._cached_sidebar_scale_brushes[key] = fallback
        return fallback

    @classmethod
    def build_vector_app_pixmap(
        cls,
        size: int = 54,
        accent_hex: str = "#C82333",
        gold_hex: str = "#D4AF37"
    ) -> QPixmap:
        """Renderiza el emblema dragon_emblem.png con transparencia limpia o respaldo SVG."""
        cache_key = (int(size), str(accent_hex).upper(), str(gold_hex).upper())
        cached = cls._cached_app_emblems.get(cache_key)
        if cached is not None:
            return cached

        png_emblem = cls.load_transparent_asset("dragon_emblem.png", opacity=1.0, target_size=(size, size))
        if not png_emblem.isNull():
            cls._cached_app_emblems[cache_key] = png_emblem
            return png_emblem

        gold_hi = "#FDE68A"
        gold_old = str(gold_hex or "#D4AF37")
        copper_dk = "#6E4420"
        flame_mid = str(accent_hex or "#E64955")

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <defs>
    <radialGradient id="fireBg" cx="50%" cy="44%" r="54%">
      <stop offset="0%" stop-color="#FFF0A8"/>
      <stop offset="22%" stop-color="#F59E0B"/>
      <stop offset="52%" stop-color="{flame_mid}"/>
      <stop offset="82%" stop-color="#6B0E17"/>
      <stop offset="100%" stop-color="#14080B"/>
    </radialGradient>
    <linearGradient id="shieldRim" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{gold_hi}"/>
      <stop offset="35%" stop-color="{gold_old}"/>
      <stop offset="72%" stop-color="#8C6239"/>
      <stop offset="100%" stop-color="#4A2C16"/>
    </linearGradient>
    <linearGradient id="dragonGold" x1="15%" y1="10%" x2="88%" y2="92%">
      <stop offset="0%" stop-color="#FFF4C4"/>
      <stop offset="36%" stop-color="#F59E0B"/>
      <stop offset="74%" stop-color="{gold_old}"/>
      <stop offset="100%" stop-color="{copper_dk}"/>
    </linearGradient>
    <linearGradient id="wingMem" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#F59E0B" stop-opacity="0.92"/>
      <stop offset="55%" stop-color="{gold_old}" stop-opacity="0.88"/>
      <stop offset="100%" stop-color="#7A4B26" stop-opacity="0.95"/>
    </linearGradient>
  </defs>

  <!-- Sombra/bisel exterior hierro oscuro y escudo heráldico -->
  <path d="M64 4 L114 20 L110 69 C106 96 86 114 64 124 C42 114 22 96 18 69 L14 20 Z"
        fill="#2B170E" stroke="#140906" stroke-width="2"/>
  <path d="M64 7 L111 22 L107 68 C103 93 84 110 64 120 C44 110 25 93 21 68 L17 22 Z"
        fill="url(#fireBg)" stroke="url(#shieldRim)" stroke-width="5.5" stroke-linejoin="round"/>
  <path d="M64 14 L103 27 L99 67 C96 88 80 103 64 112 C48 103 32 88 29 67 L25 27 Z"
        fill="none" stroke="#FDE68A" stroke-opacity="0.55" stroke-width="1.3"/>

  <!-- Halo y lenguas de brasa -->
  <path d="M36 92 Q45 72 34 55 Q50 64 56 46 Q64 62 74 44 Q78 65 94 56 Q83 74 92 92 Q78 82 64 98 Q50 82 36 92 Z"
        fill="#F59E0B" fill-opacity="0.28"/>

  <!-- Ala izquierda desplegada con nervaduras -->
  <path d="M60 56 C46 43 32 30 22 28 C27 39 25 46 21 53 C30 53 33 58 30 66 C39 63 45 66 47 73 C53 68 57 63 60 56 Z"
        fill="url(#wingMem)" stroke="#3D1C0B" stroke-width="1.5" stroke-linejoin="round"/>
  <path d="M58 55 L24 30 M56 58 L24 52 M54 61 L33 65"
        fill="none" stroke="#FFF2BD" stroke-width="1.4" stroke-linecap="round" opacity="0.85"/>

  <!-- Ala derecha desplegada con nervaduras -->
  <path d="M68 56 C82 43 96 30 106 28 C101 39 103 46 107 53 C98 53 95 58 98 66 C89 63 83 66 81 73 C75 68 71 63 68 56 Z"
        fill="url(#wingMem)" stroke="#3D1C0B" stroke-width="1.5" stroke-linejoin="round"/>
  <path d="M70 55 L104 30 M72 58 L104 52 M74 61 L95 65"
        fill="none" stroke="#FFF2BD" stroke-width="1.4" stroke-linecap="round" opacity="0.85"/>

  <!-- Cuerpo, cuello erguido, cabeza rugiente con cuernos y cola barbada -->
  <path d="M64 20 L69 14 L67 24 C74 22 83 25 89 31 L78 33 L85 39 C78 40 73 39 70 43 C74 52 74 66 69 78
           C75 84 82 91 74 102 C69 108 56 108 50 100 C45 94 49 87 54 90 C57 96 66 96 67 89 C63 85 56 80 56 71
           C55 60 56 50 58 43 C54 39 51 33 55 27 L52 16 L60 22 Z"
        fill="url(#dragonGold)" stroke="#2F1308" stroke-width="1.7" stroke-linejoin="round"/>

  <!-- Fuego de las fauces y ojo incandescente -->
  <path d="M81 36 Q93 34 99 40 Q91 41 96 46 Q86 43 80 39 Z" fill="#FFF3B0" stroke="#E64955" stroke-width="0.9"/>
  <circle cx="72" cy="29" r="2.1" fill="#FFF8DC"/>
  <circle cx="72" cy="29" r="1.0" fill="#D92B3A"/>

  <!-- Remaches heráldicos en las esquinas y punta del escudo -->
  <g fill="#FFF0C2" stroke="#4A2C16" stroke-width="1">
    <circle cx="23" cy="25" r="2.6"/>
    <circle cx="105" cy="25" r="2.6"/>
    <circle cx="64" cy="115" r="2.6"/>
  </g>
</svg>"""

        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, True)
        renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        renderer.render(p, QRectF(0, 0, float(size), float(size)))
        p.end()

        cls._cached_app_emblems[cache_key] = pm
        return pm

    @classmethod
    def build_nav_icon(
        cls,
        kind: str,
        color_hex: str = "#C4B5A5",
        size: int = 20,
        active: bool = False
    ) -> QIcon:
        """Iconos de navegación con trazo grueso (2px), degradado bronce-oro y relleno cálido."""
        cache_key = (str(kind), str(color_hex).upper(), int(size), bool(active))
        cached = cls._cached_nav_icons.get(cache_key)
        if cached is not None:
            return cached

        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, True)
        s = float(size)

        metal_grad = QLinearGradient(0.0, 0.0, s, s)
        if active:
            metal_grad.setColorAt(0.0, QColor("#FFF0B8"))
            metal_grad.setColorAt(0.45, QColor("#E5C17B"))
            metal_grad.setColorAt(1.0, QColor("#8C6239"))
            warm_fill = QBrush(QColor(229, 193, 123, 62))
        else:
            metal_grad.setColorAt(0.0, QColor("#E5C17B"))
            metal_grad.setColorAt(0.55, QColor("#B88B53"))
            metal_grad.setColorAt(1.0, QColor("#8C6239"))
            warm_fill = QBrush(QColor(140, 98, 57, 34))

        metal_brush = QBrush(metal_grad)
        pen = QPen(metal_brush, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)

        if kind == "capture":
            tray = QPainterPath()
            tray.moveTo(s * 0.16, s * 0.62)
            tray.lineTo(s * 0.16, s * 0.84)
            tray.lineTo(s * 0.84, s * 0.84)
            tray.lineTo(s * 0.84, s * 0.62)
            p.setBrush(warm_fill)
            p.drawPath(tray)
            p.setBrush(Qt.NoBrush)
            p.drawLine(QPointF(s * 0.50, s * 0.15), QPointF(s * 0.50, s * 0.65))
            p.drawLine(QPointF(s * 0.29, s * 0.45), QPointF(s * 0.50, s * 0.66))
            p.drawLine(QPointF(s * 0.71, s * 0.45), QPointF(s * 0.50, s * 0.66))
        elif kind == "queue":
            p.setBrush(warm_fill)
            p.drawRoundedRect(QRectF(s * 0.15, s * 0.18, s * 0.70, s * 0.18), 2.5, 2.5)
            p.drawRoundedRect(QRectF(s * 0.15, s * 0.43, s * 0.70, s * 0.18), 2.5, 2.5)
            p.drawLine(QPointF(s * 0.15, s * 0.78), QPointF(s * 0.56, s * 0.78))
            p.setBrush(metal_brush)
            p.drawEllipse(QPointF(s * 0.76, s * 0.78), s * 0.085, s * 0.085)
        elif kind == "library":
            p.setBrush(warm_fill)
            p.drawRoundedRect(QRectF(s * 0.14, s * 0.19, s * 0.72, s * 0.62), 3.0, 3.0)
            p.setBrush(metal_brush)
            p.setPen(Qt.NoPen)
            tri = QPolygonF([
                QPointF(s * 0.41, s * 0.35),
                QPointF(s * 0.41, s * 0.65),
                QPointF(s * 0.68, s * 0.50),
            ])
            p.drawPolygon(tri)
        elif kind == "ffmpeg":
            p.setBrush(Qt.NoBrush)
            p.drawLine(QPointF(s * 0.18, s * 0.27), QPointF(s * 0.82, s * 0.27))
            p.drawLine(QPointF(s * 0.18, s * 0.50), QPointF(s * 0.82, s * 0.50))
            p.drawLine(QPointF(s * 0.18, s * 0.73), QPointF(s * 0.82, s * 0.73))
            p.setBrush(metal_brush)
            p.drawEllipse(QPointF(s * 0.37, s * 0.27), s * 0.095, s * 0.095)
            p.drawEllipse(QPointF(s * 0.65, s * 0.50), s * 0.095, s * 0.095)
            p.drawEllipse(QPointF(s * 0.43, s * 0.73), s * 0.095, s * 0.095)
        elif kind == "settings":
            p.setBrush(warm_fill)
            p.drawEllipse(QPointF(s * 0.50, s * 0.50), s * 0.32, s * 0.32)
            p.drawLine(QPointF(s * 0.16, s * 0.50), QPointF(s * 0.84, s * 0.50))
            p.drawLine(QPointF(s * 0.50, s * 0.16), QPointF(s * 0.50, s * 0.84))
            p.setBrush(metal_brush)
            p.drawEllipse(QPointF(s * 0.50, s * 0.50), s * 0.10, s * 0.10)
        elif kind == "security":
            shield = QPainterPath()
            shield.moveTo(s * 0.50, s * 0.14)
            shield.lineTo(s * 0.81, s * 0.26)
            shield.lineTo(s * 0.81, s * 0.52)
            shield.quadTo(s * 0.81, s * 0.77, s * 0.50, s * 0.87)
            shield.quadTo(s * 0.19, s * 0.77, s * 0.19, s * 0.52)
            shield.lineTo(s * 0.19, s * 0.26)
            shield.closeSubpath()
            p.setBrush(warm_fill)
            p.drawPath(shield)
            p.setBrush(Qt.NoBrush)
            p.drawLine(QPointF(s * 0.36, s * 0.51), QPointF(s * 0.47, s * 0.62))
            p.drawLine(QPointF(s * 0.47, s * 0.62), QPointF(s * 0.66, s * 0.40))
        else:
            p.setBrush(warm_fill)
            p.drawEllipse(QPointF(s * 0.50, s * 0.50), s * 0.34, s * 0.34)
            p.setBrush(metal_brush)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(s * 0.38, s * 0.39), s * 0.08, s * 0.08)
            p.drawEllipse(QPointF(s * 0.61, s * 0.37), s * 0.08, s * 0.08)
            p.drawEllipse(QPointF(s * 0.54, s * 0.62), s * 0.09, s * 0.09)

        p.end()
        icon = QIcon(pm)
        cls._cached_nav_icons[cache_key] = icon
        return icon

    @classmethod
    def get_dragon_scale_brush(
        cls,
        copper_hex: str = "#8C6239",
        gold_hex: str = "#C59B5F",
        alpha: int = 11
    ) -> QBrush:
        """Pre-renderiza y cachea un patrón mosaico de escamas de dragón (~4% opacidad)."""
        key = (str(copper_hex).upper(), str(gold_hex).upper(), int(alpha))
        cached = cls._cached_scale_brushes.get(key)
        if cached is not None:
            return cached

        w, h = 44, 36
        tile = QPixmap(w, h)
        tile.fill(Qt.transparent)
        p = QPainter(tile)
        p.setRenderHint(QPainter.Antialiasing, True)

        c1 = QColor(gold_hex)
        c1.setAlpha(max(4, min(255, alpha)))
        c2 = QColor(copper_hex)
        c2.setAlpha(max(4, min(255, int(alpha * 0.85))))

        p.setBrush(Qt.NoBrush)
        for row_y, x_off, pen_col in ((0.0, 0.0, c1), (h * 0.5, w * 0.5, c2), (h, 0.0, c1)):
            p.setPen(QPen(pen_col, 1.05))
            for col_x in (-w * 0.5, 0.0, w * 0.5, w):
                cx = col_x + x_off
                scale = QPainterPath()
                scale.moveTo(cx, row_y - h * 0.42)
                scale.quadTo(cx + w * 0.48, row_y + h * 0.05, cx, row_y + h * 0.46)
                scale.quadTo(cx - w * 0.48, row_y + h * 0.05, cx, row_y - h * 0.42)
                p.drawPath(scale)
        p.end()

        brush = QBrush(tile)
        cls._cached_scale_brushes[key] = brush
        return brush

    @classmethod
    def get_rivet_pixmap(cls, size: int = 10) -> QPixmap:
        """Pre-renderiza un remache circular metálico con punto de luz especular."""
        key = int(size)
        cached = cls._cached_rivet_pixmaps.get(key)
        if cached is not None:
            return cached

        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, True)
        c = size / 2.0
        r = max(2.2, c - 1.2)

        body_grad = QRadialGradient(c - r * 0.25, c - r * 0.25, r * 1.35)
        body_grad.setColorAt(0.0, QColor("#FFF2B8"))
        body_grad.setColorAt(0.45, QColor("#D4AF37"))
        body_grad.setColorAt(0.85, QColor("#7A4B26"))
        body_grad.setColorAt(1.0, QColor("#361E0D"))

        p.setPen(QPen(QColor("#2A160A"), 0.9))
        p.setBrush(QBrush(body_grad))
        p.drawEllipse(QPointF(c, c), r, r)

        # Brillo especular
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(255, 250, 232, 220)))
        p.drawEllipse(QPointF(c - r * 0.30, c - r * 0.30), max(0.8, r * 0.28), max(0.8, r * 0.28))
        p.end()

        cls._cached_rivet_pixmaps[key] = pm
        return pm

    @classmethod
    def get_corner_rivet_pixmaps(
        cls,
        copper_hex: str = "#9E6F3E",
        gold_hex: str = "#E0B866",
        size: int = 24
    ) -> tuple:
        """Pre-renderiza 4 filigranas esquineras metálicas biseladas con remache."""
        key = (str(copper_hex).upper(), str(gold_hex).upper(), int(size))
        cached = cls._cached_corner_pixmaps.get(key)
        if cached is not None:
            return cached

        rivet = cls.get_rivet_pixmap(10)

        def _make_corner(flip_x: bool, flip_y: bool) -> QPixmap:
            pm = QPixmap(size, size)
            pm.fill(Qt.transparent)
            p = QPainter(pm)
            p.setRenderHint(QPainter.Antialiasing, True)
            if flip_x or flip_y:
                p.translate(size if flip_x else 0, size if flip_y else 0)
                p.scale(-1.0 if flip_x else 1.0, -1.0 if flip_y else 1.0)

            grad = QLinearGradient(0.0, 0.0, float(size), float(size))
            grad.setColorAt(0.0, QColor(gold_hex))
            grad.setColorAt(0.55, QColor(copper_hex))
            grad.setColorAt(1.0, QColor("#4A2C16"))

            bevel = QPainterPath()
            bevel.moveTo(1.5, float(size - 2))
            bevel.lineTo(1.5, 4.5)
            bevel.lineTo(4.5, 1.5)
            bevel.lineTo(float(size - 2), 1.5)
            bevel.lineTo(float(size - 4), 4.8)
            bevel.lineTo(6.2, 4.8)
            bevel.lineTo(4.8, 6.2)
            bevel.lineTo(4.8, float(size - 4))
            bevel.closeSubpath()

            p.setPen(QPen(QColor("#361E0D"), 0.8))
            p.setBrush(QBrush(grad))
            p.drawPath(bevel)

            # Filigrana en voluta interior
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(gold_hex), 1.1, Qt.SolidLine, Qt.RoundCap))
            scroll_arc = QPainterPath()
            scroll_arc.moveTo(7.0, float(size - 7))
            scroll_arc.quadTo(7.5, 7.5, float(size - 7), 7.0)
            p.drawPath(scroll_arc)

            p.drawPixmap(2, 2, rivet)
            p.end()
            return pm

        corners = (
            _make_corner(False, False),
            _make_corner(True, False),
            _make_corner(False, True),
            _make_corner(True, True),
        )
        cls._cached_corner_pixmaps[key] = corners
        return corners

    @classmethod
    def get_side_brazier_pixmaps(cls, width: int = 14, height: int = 56) -> tuple[QPixmap, QPixmap]:
        """Pre-renderiza ornamentos laterales simétricos 'Brasero / Garra de Fuego' (14x56) en caché."""
        key = (int(width), int(height))
        cached = cls._cached_brazier_pixmaps.get(key)
        if cached is not None:
            return cached

        def _render_side(mirror_x: bool) -> QPixmap:
            pm = QPixmap(width, height)
            pm.fill(Qt.transparent)
            p = QPainter(pm)
            p.setRenderHint(QPainter.Antialiasing, True)
            if mirror_x:
                p.translate(float(width), 0.0)
                p.scale(-1.0, 1.0)

            w, h = float(width), float(height)
            cy = h * 0.50

            # Lenguas de fuego verticales ascendentes y descendentes
            up_grad = QLinearGradient(0.0, cy - 2.0, 0.0, 1.0)
            up_grad.setColorAt(0.0, QColor("#FFFBEB"))
            up_grad.setColorAt(0.28, QColor("#F59E0B"))
            up_grad.setColorAt(0.68, QColor("#B91C1C"))
            up_grad.setColorAt(1.0, QColor(185, 28, 28, 0))

            dn_grad = QLinearGradient(0.0, cy + 2.0, 0.0, h - 1.0)
            dn_grad.setColorAt(0.0, QColor("#FFFBEB"))
            dn_grad.setColorAt(0.28, QColor("#F59E0B"))
            dn_grad.setColorAt(0.68, QColor("#B91C1C"))
            dn_grad.setColorAt(1.0, QColor(185, 28, 28, 0))

            up_flame = QPainterPath()
            up_flame.moveTo(2.0, cy - 3.0)
            up_flame.quadTo(1.5, h * 0.24, 5.2, 2.0)
            up_flame.quadTo(8.5, h * 0.22, 10.5, cy - 6.0)
            up_flame.closeSubpath()
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(up_grad))
            p.drawPath(up_flame)

            dn_flame = QPainterPath()
            dn_flame.moveTo(2.0, cy + 3.0)
            dn_flame.quadTo(1.5, h * 0.76, 5.2, h - 2.0)
            dn_flame.quadTo(8.5, h * 0.78, 10.5, cy + 6.0)
            dn_flame.closeSubpath()
            p.setBrush(QBrush(dn_grad))
            p.drawPath(dn_flame)

            # Chispas doradas sutiles
            p.setBrush(QBrush(QColor(255, 251, 235, 210)))
            p.drawEllipse(QPointF(8.5, 6.0), 0.9, 0.9)
            p.drawEllipse(QPointF(9.2, h - 7.0), 0.9, 0.9)
            p.setBrush(QBrush(QColor(245, 158, 11, 185)))
            p.drawEllipse(QPointF(3.2, 9.5), 0.8, 0.8)
            p.drawEllipse(QPointF(3.4, h - 10.0), 0.8, 0.8)

            # Base metálica oscura en forma de garra/escudo lateral con ribete dorado (#D4AF37)
            claw = QPainterPath()
            claw.moveTo(0.8, cy - 12.0)
            claw.lineTo(6.5, cy - 10.0)
            claw.quadTo(w - 1.5, cy - 6.5, w - 1.0, cy)
            claw.quadTo(w - 1.5, cy + 6.5, 6.5, cy + 10.0)
            claw.lineTo(0.8, cy + 12.0)
            claw.closeSubpath()

            metal_grad = QLinearGradient(0.0, cy - 12.0, w, cy + 12.0)
            metal_grad.setColorAt(0.0, QColor("#2B1A1E"))
            metal_grad.setColorAt(0.5, QColor("#180E11"))
            metal_grad.setColorAt(1.0, QColor("#4A2C16"))
            p.setBrush(QBrush(metal_grad))
            p.setPen(QPen(QColor("#D4AF37"), 1.35, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPath(claw)

            # Núcleo incandescente / remache central del brasero
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor("#F59E0B")))
            p.drawEllipse(QPointF(5.6, cy), 2.3, 2.3)
            p.setBrush(QBrush(QColor("#FFFBEB")))
            p.drawEllipse(QPointF(5.2, cy - 0.5), 1.0, 1.0)
            p.end()
            return pm

        pair = (_render_side(False), _render_side(True))
        cls._cached_brazier_pixmaps[key] = pair
        return pair

    @classmethod
    def paint_forged_overlay(cls, widget, event, is_sidebar: bool = False):
        """Marcos forjados de doble bisel (3px), friso/textura cacheada y remaches especulares."""
        w, h = widget.width(), widget.height()
        if w < 32 or h < 32:
            return
        win = widget.window() if widget else None
        t = getattr(win, "_active_ergonomic_theme", None) if win else None
        if not isinstance(t, dict):
            t = cls.PRESETS[cls.DEFAULT_PRESET]

        is_light = cls.is_light_theme(t)
        copper_hex = str(t.get("border", "#9E6F3E"))
        gold_hex = str(t.get("border_gold", "#E0B866"))

        # Opacidades calibradas (~7% sidebar, ~10% friso superior de tarjetas)
        scale_alpha = 18 if is_sidebar else 26
        if is_light:
            scale_alpha = max(10, scale_alpha - 6)

        scale_brush = (
            cls.get_sidebar_scales_brush(tile_size=160, dark_overlay_alpha=140)
            if (is_sidebar and not is_light)
            else cls.get_dragon_scale_brush("#9E6F3E", "#E0B866", alpha=scale_alpha)
        )
        tl, tr_pm, bl, br = cls.get_corner_rivet_pixmaps("#9E6F3E", "#E0B866", size=24)
        rivet_pm = cls.get_rivet_pixmap(10)

        p = QPainter(widget)
        if not p.isActive():
            return
        if event is not None:
            p.setClipRect(event.rect())

        # 1. Textura cacheada de escamas (Sidebar completo o friso superior de tarjeta)
        if is_sidebar:
            p.fillRect(QRect(3, 3, max(0, w - 6), max(0, h - 6)), scale_brush)
        else:
            band_h = min(64, max(0, h - 6))
            if band_h > 0:
                p.fillRect(QRect(3, 3, max(0, w - 6), band_h), scale_brush)
                # Línea divisoria dorada bajo el friso ornamental superior
                div_y = float(band_h + 2)
                div_grad = QLinearGradient(12.0, div_y, float(w - 12), div_y)
                div_grad.setColorAt(0.0, QColor(74, 44, 22, 40))
                div_grad.setColorAt(0.2, QColor(158, 111, 62, 180))
                div_grad.setColorAt(0.5, QColor(224, 184, 102, 235))
                div_grad.setColorAt(0.8, QColor(158, 111, 62, 180))
                div_grad.setColorAt(1.0, QColor(74, 44, 22, 40))
                p.setPen(QPen(QBrush(div_grad), 1.2))
                p.drawLine(QPointF(12.0, div_y), QPointF(float(w - 12), div_y))

        # 2. Marco metálico forjado de doble capa (3px totales: #4A2C16 / #9E6F3E / #E0B866)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor("#4A2C16"), 1.0))
        p.drawRect(QRectF(0.5, 0.5, max(1.0, w - 1.0), max(1.0, h - 1.0)))

        p.setPen(QPen(QColor("#9E6F3E"), 1.0))
        p.drawRect(QRectF(1.5, 1.5, max(1.0, w - 3.0), max(1.0, h - 3.0)))

        p.setPen(QPen(QColor("#E0B866"), 1.0))
        p.drawRect(QRectF(2.5, 2.5, max(1.0, w - 5.0), max(1.0, h - 5.0)))

        # Borde derecho ornamentado en Sidebar separándolo del área principal
        if is_sidebar:
            p.setPen(QPen(QColor("#9E6F3E"), 1.5))
            p.drawLine(QPointF(w - 4.0, 6.0), QPointF(w - 4.0, h - 6.0))
            p.setPen(QPen(QColor("#E0B866"), 1.0))
            p.drawLine(QPointF(w - 2.0, 6.0), QPointF(w - 2.0, h - 6.0))
            for my in (int(h * 0.28), int(h * 0.52), int(h * 0.76)):
                p.drawPixmap(w - rivet_pm.width() - 1, my - rivet_pm.height() // 2, rivet_pm)

        # 3. Filigranas con remaches en las 4 esquinas y remaches en puntos medios sup/inf
        cs = tl.width()
        p.drawPixmap(1, 1, tl)
        p.drawPixmap(w - cs - 1, 1, tr_pm)
        p.drawPixmap(1, h - cs - 1, bl)
        p.drawPixmap(w - cs - 1, h - cs - 1, br)

        mid_x = (w - rivet_pm.width()) // 2
        p.drawPixmap(mid_x, 1, rivet_pm)
        p.drawPixmap(mid_x, h - rivet_pm.height() - 1, rivet_pm)
        p.end()

    PRESETS = {
        "Dragon Forge (Obsidiana y Oro)": {
            "bg_main": "#120B0E",
            "bg_sidebar": "#0C0709",
            "bg_card": "#1B1115",
            "bg_subcard": "#21151A",
            "bg_input": "#24171D",
            "bg_dropdown_btn": "#3B2219",
            "border": "#8C6239",
            "border_gold": "#C59B5F",
            "accent": "#C82333",
            "accent_hover": "#E64955",
            "gold": "#F59E0B",
            "text_main": "#F5EFE6",
            "text_muted": "#C4B5A5",
            "font_size": 10,
            "radius": 9
        },
        "Targaryen Rubí (Equilibrado - Recomendado)": {
            "bg_main": "#1A1417",
            "bg_sidebar": "#120E10",
            "bg_card": "#251C20",
            "bg_subcard": "#2D2227",
            "bg_input": "#36282E",
            "bg_dropdown_btn": "#4C2930",
            "border": "#523138",
            "accent": "#D13844",
            "accent_hover": "#E64955",
            "text_main": "#F7F2EE",
            "text_muted": "#C4B1B4",
            "font_size": 10,
            "radius": 9
        },
        "Targaryen Ceniza Clara (Más Luminoso)": {
            "bg_main": "#231B1E",
            "bg_sidebar": "#181315",
            "bg_card": "#2F2529",
            "bg_subcard": "#382C31",
            "bg_input": "#44353B",
            "bg_dropdown_btn": "#5B3139",
            "border": "#6B3F47",
            "accent": "#DC424E",
            "accent_hover": "#F05561",
            "text_main": "#FAF6F2",
            "text_muted": "#D5C3C6",
            "font_size": 10,
            "radius": 9
        },
        "Sangre y Obsidiana (Contraste Oscuro)": {
            "bg_main": "#110E10",
            "bg_sidebar": "#0B090A",
            "bg_card": "#1A1518",
            "bg_subcard": "#221B1F",
            "bg_input": "#2B2227",
            "bg_dropdown_btn": "#3F1F25",
            "border": "#48262D",
            "accent": "#C42F3B",
            "accent_hover": "#DE3F4C",
            "text_main": "#F2ECE7",
            "text_muted": "#B5A2A5",
            "font_size": 10,
            "radius": 9
        },
        "Acero Valyrio (Gris Azulado Suave)": {
            "bg_main": "#141920",
            "bg_sidebar": "#0E1217",
            "bg_card": "#1D242E",
            "bg_subcard": "#232C38",
            "bg_input": "#2B3645",
            "bg_dropdown_btn": "#264666",
            "border": "#3A495E",
            "accent": "#3B82F6",
            "accent_hover": "#60A5FA",
            "text_main": "#F3F6FA",
            "text_muted": "#AFC0D4",
            "font_size": 10,
            "radius": 9
        },
        "Pergamino Real (Modo Claro Anti-Reflejos)": {
            "bg_main": "#EFEAE2",
            "bg_sidebar": "#E3DCD2",
            "bg_card": "#FAF7F2",
            "bg_subcard": "#F3EFE8",
            "bg_input": "#E7E0D6",
            "bg_dropdown_btn": "#D6C8BD",
            "border": "#C5B6AA",
            "accent": "#B02A34",
            "accent_hover": "#C93641",
            "text_main": "#221A1C",
            "text_muted": "#635356",
            "font_size": 10,
            "radius": 9
        }
    }

    @classmethod
    def is_light_theme(cls, t: dict) -> bool:
        bg_col = QColor(str(t.get("bg_main", "#1A1417")))
        lum = 0.299 * bg_col.red() + 0.587 * bg_col.green() + 0.114 * bg_col.blue()
        return lum > 140

    @classmethod
    def ensure_ui_icons(cls, t: dict) -> dict:
        cls.APP_DIR = get_portable_data_dir()
        cls.ICON_DIR = os.path.join(cls.APP_DIR, "ui_icons")
        os.makedirs(cls.ICON_DIR, exist_ok=True)
        txt_hex = str(t.get("text_main", "#F7F2EE")).upper()

        paths = {
            "down": os.path.join(cls.ICON_DIR, "arrow_down.png"),
            "up": os.path.join(cls.ICON_DIR, "arrow_up.png"),
            "check": os.path.join(cls.ICON_DIR, "check_mark.png"),
        }

        cache_key = (cls.ICON_DIR, txt_hex)
        if (
            cls._cached_icon_key == cache_key
            and cls._cached_icon_paths is not None
            and all(os.path.isfile(p) for p in paths.values())
        ):
            return cls._cached_icon_paths

        txt_col = QColor(txt_hex)
        chk_col = QColor("#FFFFFF")

        pm_down = QPixmap(16, 16)
        pm_down.fill(Qt.transparent)
        p = QPainter(pm_down)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(txt_col))
        p.drawPolygon(QPolygonF([QPointF(2.5, 5.0), QPointF(13.5, 5.0), QPointF(8.0, 11.5)]))
        p.end()
        pm_down.save(paths["down"], "PNG")

        pm_up = QPixmap(16, 16)
        pm_up.fill(Qt.transparent)
        p = QPainter(pm_up)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(txt_col))
        p.drawPolygon(QPolygonF([QPointF(8.0, 4.5), QPointF(13.5, 11.0), QPointF(2.5, 11.0)]))
        p.end()
        pm_up.save(paths["up"], "PNG")

        pm_chk = QPixmap(16, 16)
        pm_chk.fill(Qt.transparent)
        p = QPainter(pm_chk)
        p.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(chk_col, 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.drawLine(QPointF(3.0, 8.2), QPointF(6.5, 11.5))
        p.drawLine(QPointF(6.5, 11.5), QPointF(13.0, 4.2))
        p.end()
        pm_chk.save(paths["check"], "PNG")

        slash = chr(92)
        cls._cached_icon_paths = {k: v.replace(slash, "/") for k, v in paths.items()}
        cls._cached_icon_key = cache_key
        return cls._cached_icon_paths

    @classmethod
    def load_state(cls, settings_mgr: SettingsManager = None) -> tuple[dict, str]:
        sm = settings_mgr or SettingsManager()
        data = sm.load()
        preset_name = str(data.get("ui_preset_name") or cls.DEFAULT_PRESET)
        base_preset = cls.PRESETS.get(preset_name, cls.PRESETS[cls.DEFAULT_PRESET])
        theme = dict(base_preset)
        saved_theme = data.get("ui_theme")
        if isinstance(saved_theme, dict) and saved_theme:
            theme.update(saved_theme)
        return theme, preset_name

    @classmethod
    def save_state(cls, theme_dict: dict, preset_name: str = "", settings_mgr: SettingsManager = None):
        sm = settings_mgr or SettingsManager()
        sm.save({
            "ui_theme": dict(theme_dict),
            "ui_preset_name": preset_name or "Personalizado"
        })

    @classmethod
    def build_qss(cls, t: dict) -> str:
        icons = cls.ensure_ui_icons(t)
        bg_main = t.get("bg_main", "#1A1417")
        bg_side = t.get("bg_sidebar", "#120E10")
        bg_card = t.get("bg_card", "#251C20")
        bg_subcard = t.get("bg_subcard") or QColor(bg_card).lighter(112).name()
        bg_inp = t.get("bg_input", "#36282E")
        bg_dd = t.get("bg_dropdown_btn", "#4C2930")
        border = t.get("border", "#8C6239")
        border_gold = t.get("border_gold", "#C59B5F")
        gold = t.get("gold", "#F59E0B")
        accent = t.get("accent", "#C82333")
        accent_h = t.get("accent_hover", "#E64955")
        txt = t.get("text_main", "#F5EFE6")
        muted = t.get("text_muted", "#C4B5A5")
        fsize = int(t.get("font_size", 10))
        rad = max(8, int(t.get("radius", 9)))
        rad_ctrl = 6
        is_light = cls.is_light_theme(t)

        if is_light:
            danger_bg = "#FDE8E8"
            danger_fg = "#9B1C1C"
            danger_bd = "#F8B4B4"
            badge_run_bg, badge_run_fg, badge_run_bd = "#DBEAFE", "#1E40AF", "#93C5FD"
            badge_ok_bg, badge_ok_fg, badge_ok_bd = "#DCFCE7", "#166534", "#86EFAC"
            badge_pause_bg, badge_pause_fg, badge_pause_bd = "#FEF3C7", "#92400E", "#FCD34D"
            badge_err_bg, badge_err_fg, badge_err_bd = "#FEE2E2", "#991B1B", "#FCA5A5"
            badge_wait_bg, badge_wait_fg, badge_wait_bd = "#E5E7EB", "#374151", "#D1D5DB"
            console_bg = "#F5F1EA"
            card_top = QColor(bg_card).lighter(103).name()
            card_bot = QColor(bg_card).darker(106).name()
            sunken_bg = bg_subcard
            sunken_top_bd = QColor(border).darker(120).name()
            sunken_bot_bd = QColor(border).lighter(115).name()
            grp_title_bg = bg_card
            grp_title_fg = accent
            btn_top = QColor(bg_inp).lighter(108).name()
            btn_bot = bg_inp
            btn_b_top = QColor(border).lighter(120).name()
            btn_b_left = border
            btn_b_right = QColor(border).darker(125).name()
            btn_b_bot = QColor(border).darker(145).name()
            btn_hover_top = QColor(bg_subcard).lighter(106).name()
            btn_hover_bot = bg_subcard
            btn_hover_bd = accent
            brand_fg = txt
            brand_sub_fg = accent
            pbar_bg = bg_inp
            pbar_bd_dark = QColor(border).darker(130).name()
            pbar_bd_light = border
        else:
            danger_bg = "#3A1D22"
            danger_fg = "#FCA5A5"
            danger_bd = "#7F2D36"
            badge_run_bg, badge_run_fg, badge_run_bd = "#172B4D", "#93C5FD", "#2563EB"
            badge_ok_bg, badge_ok_fg, badge_ok_bd = "#133223", "#86EFAC", "#16A34A"
            badge_pause_bg, badge_pause_fg, badge_pause_bd = "#3B2A14", "#FCD34D", "#D97706"
            badge_err_bg, badge_err_fg, badge_err_bd = "#3F1A20", "#FCA5A5", "#DC2626"
            badge_wait_bg, badge_wait_fg, badge_wait_bd = "#2D2529", "#D1C4C7", "#524146"
            console_bg = bg_side
            is_df = (str(bg_main).upper() == "#120B0E")
            card_top = "#24151B" if is_df else QColor(bg_card).lighter(124).name()
            card_bot = "#11090C" if is_df else QColor(bg_card).darker(135).name()
            sunken_bg = "#130A0E" if is_df else QColor(bg_main).darker(115).name()
            sunken_top_bd = "#090406"
            sunken_bot_bd = "#6E4D30"
            grp_title_bg = "#1A0F14" if is_df else bg_card
            grp_title_fg = "#E5C17B"
            btn_top = "#36272C" if is_df else QColor(bg_inp).lighter(115).name()
            btn_bot = "#181013" if is_df else QColor(bg_inp).darker(115).name()
            btn_b_top = "#B8925A"
            btn_b_left = "#9E6F3E"
            btn_b_right = "#4A321D"
            btn_b_bot = "#24160C"
            btn_hover_top = "#453138"
            btn_hover_bot = "#24171B"
            btn_hover_bd = "#E0B866"
            brand_fg = "#FFF8EE"
            brand_sub_fg = "#E09F5A"
            pbar_bg = "#0D0709" if is_df else bg_inp
            pbar_bd_dark = "#3A2414"
            pbar_bd_light = "#8C6239"

        return f"""
        QMainWindow, QDialog, QMessageBox, QColorDialog, QFileDialog {{
            background-color: {bg_main};
            color: {txt};
            font-family: {cls.UI_FONT_STACK};
            font-size: {fsize}pt;
        }}
        QStackedWidget, QStackedWidget > QWidget, QFrame#MainArea,
        QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget,
        QWidget#ScrollPageContent {{
            background-color: {bg_main};
            border: none;
        }}
        QToolTip {{
            background-color: {bg_side};
            color: {txt};
            border: 1px solid {accent};
            border-radius: 5px;
            padding: 5px 8px;
            font-family: {cls.UI_FONT_STACK};
            font-size: {max(8, fsize - 1)}pt;
        }}

        /* ── Tipografía y Jerarquía Visual ── */
        QLabel {{
            background-color: transparent;
            border: none;
            color: {txt};
            font-family: {cls.UI_FONT_STACK};
            font-size: {fsize}pt;
            padding: 2px 0px;
        }}
        QCheckBox, QRadioButton {{
            background-color: transparent;
            border: none;
            color: {txt};
            font-family: {cls.UI_FONT_STACK};
            font-size: {fsize}pt;
            min-height: 24px;
            spacing: 8px;
            padding: 2px 4px;
        }}
        QLabel:disabled, QCheckBox:disabled, QRadioButton:disabled {{
            color: {muted};
        }}
        QLabel#BrandTitle {{
            color: {brand_fg};
            font-size: {fsize + 1}pt;
            font-weight: 800;
            letter-spacing: 0.6px;
            padding: 0px;
        }}
        QLabel#BrandSub {{
            color: {brand_sub_fg};
            font-size: 8pt;
            font-weight: 700;
            letter-spacing: 0.9px;
            padding: 0px;
        }}
        QLabel#SidebarSection, QLabel#WorkspaceHdr {{
            color: {muted};
            font-size: 8pt;
            font-weight: 700;
            letter-spacing: 0.7px;
            padding: 4px 6px 2px 6px;
        }}
        QLabel#PageHeaderTitle {{
            color: {txt};
            font-size: {fsize + 3}pt;
            font-weight: 800;
            padding: 0px;
        }}
        QLabel#PageHeaderDesc {{
            color: {muted};
            font-size: {max(8, fsize - 1)}pt;
            font-weight: 400;
            padding: 0px;
        }}
        QLabel#SectionHeader, QLabel#SectionTitle {{
            color: {txt};
            font-size: {fsize + 1}pt;
            font-weight: 700;
            border-left: 3px solid {accent};
            padding-left: 9px;
            margin-bottom: 2px;
        }}
        QLabel#SubCardTitle {{
            color: {accent_h};
            font-size: {fsize}pt;
            font-weight: 700;
            padding-bottom: 4px;
        }}
        QLabel#SectionSub, QLabel#CardSub, QLabel#SubHint {{
            color: {muted};
            font-size: {max(8, fsize - 1)}pt;
            padding-left: 2px;
        }}
        QLabel#MediaHeroTitle {{
            color: {txt};
            font-size: {fsize + 1}pt;
            font-weight: 700;
            padding: 2px 0px;
        }}
        QLabel#FieldLabel {{
            color: {txt};
            font-size: {fsize}pt;
            font-weight: 600;
            min-height: 24px;
        }}
        QLabel#DiskLabel {{
            color: {muted};
            font-size: {max(8, fsize - 1)}pt;
            font-weight: 600;
        }}

        /* ── Contenedores, Tarjetas 3D y Bajorrelieve Metálico ── */
        QFrame#SurfaceCard, QFrame#Card, QFrame#InspectorCard {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {card_top}, stop:1 {card_bot}
            );
            border: 1px solid #4A2C16;
            border-radius: 4px;
        }}
        QFrame#OptionSubCard {{
            background-color: {sunken_bg};
            border-top: 1px solid {sunken_top_bd};
            border-left: 1px solid {sunken_top_bd};
            border-right: 1px solid #2A181F;
            border-bottom: 1px solid {sunken_bot_bd};
            border-radius: {max(6, rad - 2)}px;
        }}
        QGroupBox {{
            background-color: {sunken_bg};
            border-top: 1px solid {sunken_top_bd};
            border-left: 1px solid {sunken_top_bd};
            border-right: 1px solid #2A181F;
            border-bottom: 1px solid {sunken_bot_bd};
            border-radius: {max(6, rad - 2)}px;
            margin-top: 14px;
            padding-top: 18px;
            padding-bottom: 12px;
            padding-left: 12px;
            padding-right: 12px;
            color: {txt};
            font-weight: 700;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px;
            padding: 1px 8px;
            background-color: {grp_title_bg};
            color: {grp_title_fg};
            font-weight: 700;
            border: 1px solid {border};
            border-left: 3px solid #D4AF37;
            border-radius: 3px;
        }}
        QFrame#OmniBar {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {card_top}, stop:1 {card_bot}
            );
            border: 1px solid {border};
            border-radius: {rad}px;
        }}
        QFrame#PageHeaderBar {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {card_top}, stop:1 {card_bot}
            );
            border: 1px solid {border};
            border-left: 4px solid #D4AF37;
            border-radius: {rad}px;
        }}
        QFrame#SidebarFooterCard {{
            border-radius: 12px;
            border: 2px solid #8C6239;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #1F1317, stop:1 #10080B
            );
        }}
        QFrame#MetricTile, QFrame#MetaBox {{
            background-color: {sunken_bg};
            border-top: 1px solid {sunken_top_bd};
            border-right: 1px solid #2A181F;
            border-bottom: 1px solid {sunken_bot_bd};
            border-left: 3px solid {accent};
            border-radius: 6px;
            padding: 4px 8px;
        }}
        QLabel#TileLabel, QLabel#MetaTitle {{
            color: {muted};
            font-size: 8pt;
            font-weight: 600;
        }}
        QLabel#TileValue, QLabel#MetaValue {{
            color: {txt};
            font-size: {fsize}pt;
            font-weight: 700;
        }}
        QLabel#ThumbnailBox, QLabel#PreviewBox {{
            background-color: {bg_inp};
            color: {muted};
            border: 1px solid {border};
            border-radius: 8px;
            font-size: {max(8, fsize - 1)}pt;
            font-weight: 700;
        }}

        /* ── Barra Lateral de Navegación ── */
        QFrame#Sidebar {{
            background-color: {bg_side};
            border-right: 1px solid {border};
        }}
        QListWidget, QListWidget#NavList {{
            background-color: transparent;
            border: none;
            outline: none;
            padding: 2px;
        }}
        QListWidget::item, QListWidget#NavList::item {{
            background-color: transparent;
            color: {muted};
            padding: 9px 12px;
            margin: 2px 2px;
            border-radius: 7px;
            border-left: 3px solid transparent;
            font-weight: 600;
        }}
        QListWidget::item:hover, QListWidget#NavList::item:hover {{
            background-color: {bg_card};
            color: {txt};
        }}
        QListWidget::item:selected, QListWidget#NavList::item:selected {{
            background-color: {bg_inp};
            color: {txt};
            border-left: 4px solid {accent};
            padding-left: 10px;
            font-weight: 700;
        }}

        /* ── Campos de Entrada, Selectores y Controles (min-height 32px, border-radius 6px) ── */
        QLineEdit {{
            background-color: {bg_inp};
            color: {txt};
            border: 1px solid {border};
            border-radius: {rad_ctrl}px;
            min-height: 32px;
            padding: 2px 10px;
            selection-background-color: {accent};
            selection-color: #FFFFFF;
        }}
        QLineEdit#UrlInput {{
            font-size: {fsize}pt;
            min-height: 34px;
            padding: 3px 12px;
        }}
        QLineEdit:hover, QComboBox:hover, QSpinBox:hover {{
            border: 1px solid {accent_h};
        }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {{
            border: 1px solid {accent};
            background-color: {bg_subcard};
        }}
        QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{
            background-color: {bg_side};
            color: {muted};
            border: 1px dashed {border};
        }}
        QComboBox {{
            background-color: {bg_inp};
            color: {txt};
            border: 1px solid {border};
            border-radius: {rad_ctrl}px;
            min-height: 32px;
            padding: 2px 34px 2px 10px;
            selection-background-color: {accent};
            selection-color: #FFFFFF;
        }}
        QComboBox::drop-down {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 28px;
            background-color: {bg_dd};
            border-left: 1px solid {border};
            border-top-right-radius: {rad_ctrl}px;
            border-bottom-right-radius: {rad_ctrl}px;
        }}
        QComboBox::drop-down:hover {{
            background-color: {accent};
        }}
        QComboBox::down-arrow {{
            image: url("{icons['down']}");
            width: 12px;
            height: 12px;
        }}
        QComboBox QAbstractItemView, QMenu {{
            background-color: {bg_card};
            color: {txt};
            border: 1px solid {accent};
            border-radius: 6px;
            selection-background-color: {accent};
            selection-color: #FFFFFF;
            outline: none;
            padding: 4px;
        }}
        QComboBox QAbstractItemView::item, QMenu::item {{
            padding: 6px 12px;
            min-height: 22px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {accent};
            color: #FFFFFF;
        }}
        QMenu::separator {{
            height: 1px;
            background: {border};
            margin: 4px 6px;
        }}
        QSpinBox {{
            background-color: {bg_inp};
            color: {txt};
            border: 1px solid {border};
            border-radius: {rad_ctrl}px;
            min-height: 32px;
            padding: 2px 28px 2px 10px;
            selection-background-color: {accent};
            selection-color: #FFFFFF;
        }}
        QSpinBox::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 24px;
            background-color: {bg_dd};
            border-left: 1px solid {border};
            border-bottom: 1px solid {border};
            border-top-right-radius: {rad_ctrl}px;
        }}
        QSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 24px;
            background-color: {bg_dd};
            border-left: 1px solid {border};
            border-bottom-right-radius: {rad_ctrl}px;
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background-color: {accent};
        }}
        QSpinBox::up-arrow {{
            image: url("{icons['up']}");
            width: 10px;
            height: 10px;
        }}
        QSpinBox::down-arrow {{
            image: url("{icons['down']}");
            width: 10px;
            height: 10px;
        }}

        /* ── Casillas de Verificación (Checkboxes) ── */
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            background-color: {bg_inp};
            border: 1px solid {border};
            border-radius: 4px;
        }}
        QCheckBox::indicator:hover {{
            border: 1px solid {accent_h};
        }}
        QCheckBox::indicator:checked {{
            background-color: {accent};
            border: 1px solid {accent_h};
            image: url("{icons['check']}");
        }}
        QCheckBox::indicator:disabled {{
            background-color: {bg_side};
            border: 1px dashed {border};
        }}

        /* ── Botones Secundarios con Relieve 3D y Botón Forjado de Brasa ── */
        QPushButton {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {btn_top}, stop:1 {btn_bot}
            );
            color: {txt};
            border-top: 2px solid {btn_b_top};
            border-left: 2px solid {btn_b_left};
            border-right: 2px solid {btn_b_right};
            border-bottom: 2px solid {btn_b_bot};
            border-radius: 6px;
            min-height: 28px;
            padding: 4px 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {btn_hover_top}, stop:1 {btn_hover_bot}
            );
            border: 2px solid {btn_hover_bd};
            color: {brand_fg};
        }}
        QPushButton:pressed {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {btn_bot}, stop:1 {btn_top}
            );
            border-top: 2px solid {btn_b_bot};
            border-left: 2px solid {btn_b_right};
            border-right: 2px solid {btn_b_left};
            border-bottom: 2px solid {btn_b_top};
            padding: 5px 14px 3px 14px;
            color: {brand_fg};
        }}
        QPushButton:disabled {{
            background: none;
            background-color: {bg_side};
            color: {muted};
            border: 1px dashed {border};
        }}
        QPushButton#OmniActionBtn {{
            border-radius: 7px;
            border: 1.5px solid #B88A44;
            border-top: 2px solid #E5C17B;
            border-bottom: 2px solid #5C4018;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #2B2124, stop:0.15 #1F171A, stop:0.85 #140E10, stop:1 #0C0809
            );
            color: #F3E8D8;
            font-weight: bold;
            min-height: 30px;
            padding: 4px 14px;
        }}
        QPushButton#OmniActionBtn:hover {{
            border: 1.5px solid #F3C669;
            border-top: 2px solid #FFF0B3;
            border-bottom: 2px solid #8C5819;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #3D2B30, stop:0.5 #261A1E, stop:1 #160E10
            );
            color: #FFFBEB;
        }}
        QPushButton#OmniActionBtn:pressed {{
            border-top: 2px solid #5C4018;
            border-bottom: 2px solid #E5C17B;
            padding: 5px 14px 3px 14px;
            background: #140E10;
        }}
        QPushButton#AccentButton, QPushButton#BtnPrimaryAction {{
            border-radius: 8px;
            border: 2px solid #F3C669;
            border-top: 2.5px solid #FFF0B3;
            border-bottom: 2.5px solid #8C5819;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #E63946, stop:0.45 #B91C1C, stop:0.85 #7F1D1D, stop:1 #9A3412
            );
            color: #FFFBEB;
            font-weight: bold;
            min-height: 30px;
            padding: 5px 18px;
        }}
        QPushButton#AccentButton:hover, QPushButton#BtnPrimaryAction:hover {{
            border: 2px solid #FFE8A3;
            border-top: 2.5px solid #FFFBEB;
            border-bottom: 2.5px solid #B45309;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #F43F5E, stop:0.45 #DC2626, stop:0.85 #991B1B, stop:1 #C2410C
            );
            color: #FFFFFF;
        }}
        QPushButton#AccentButton:pressed, QPushButton#BtnPrimaryAction:pressed {{
            border-top: 2.5px solid #8C5819;
            border-bottom: 2.5px solid #FFF0B3;
            padding: 6px 18px 4px 18px;
            background: #7F1D1D;
        }}
        QPushButton#AccentButton:disabled, QPushButton#BtnPrimaryAction:disabled {{
            background: none;
            background-color: {bg_inp};
            color: {muted};
            border: 1px solid {border};
        }}
        QPushButton#DangerButton {{
            background-color: {danger_bg};
            color: {danger_fg};
            border: 1px solid {danger_bd};
            border-radius: {rad_ctrl}px;
            min-height: 28px;
            padding: 4px 13px;
            font-weight: 600;
        }}
        QPushButton#DangerButton:hover {{
            background-color: #DC2626;
            color: #FFFFFF;
            border: 1px solid #EF4444;
        }}
        QPushButton#CompactActionBtn {{
            border-radius: 6px;
            border: 1px solid #6E5844;
            border-top: 1.5px solid #A88E72;
            border-bottom: 2px solid #1C1412;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #362E30, stop:0.12 #262022, stop:0.88 #171314, stop:1 #0F0C0D
            );
            color: #E6DDD0;
            min-height: 26px;
            padding: 4px 11px;
            font-size: {max(8, fsize - 1)}pt;
            font-weight: 600;
        }}
        QPushButton#CompactActionBtn:hover {{
            border: 1px solid #B88A44;
            border-top: 1.5px solid #F3C669;
            border-bottom: 2px solid #3D2814;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #45383B, stop:0.5 #2E2427, stop:1 #181214
            );
            color: #FFFBEB;
        }}
        QPushButton#CompactActionBtn:pressed {{
            border-top: 2px solid #1C1412;
            border-bottom: 1.5px solid #A88E72;
            padding: 5px 11px 3px 11px;
            background: #171314;
        }}
        QPushButton#CancelQueueBtn {{
            border-radius: 6px;
            border: 1.5px solid #D99B4E;
            border-top: 2px solid #F6D076;
            border-bottom: 2px solid #3D1F08;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #B46928, stop:0.5 #854817, stop:1 #592E0C
            );
            color: #FFF8EE;
            min-height: 26px;
            padding: 4px 11px;
            font-size: {max(8, fsize - 1)}pt;
            font-weight: 700;
        }}
        QPushButton#CancelQueueBtn:hover {{
            border: 1.5px solid #F3C669;
            border-top: 2px solid #F3C669;
            border-bottom: 2px solid #592E0C;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #C97A34, stop:0.5 #9A551D, stop:1 #6B3810
            );
            color: #FFFFFF;
        }}
        QPushButton#CancelQueueBtn:pressed {{
            border-top: 2px solid #3D1F08;
            border-bottom: 2px solid #F6D076;
            padding: 5px 11px 3px 11px;
            background: #592E0C;
        }}
        QFrame#ModeToggleFrame {{
            background-color: #140B0E;
            border: 2px solid #8C6239;
            border-radius: 12px;
            padding: 3px;
        }}
        QPushButton#ModeSwitchBtn {{
            background: transparent;
            background-color: transparent;
            color: #C4B5A5;
            border: 1.5px solid transparent;
            border-radius: 9px;
            min-height: 24px;
            padding: 3px 12px;
            font-size: {max(8, fsize - 1)}pt;
            font-weight: 700;
        }}
        QPushButton#ModeSwitchBtn:hover {{
            color: #FFF8EE;
            background: rgba(197, 155, 95, 0.14);
            border: 1.5px solid #8C6239;
        }}
        QPushButton#ModeSwitchBtn:pressed {{
            padding: 4px 12px 2px 12px;
        }}
        QPushButton#ModeSwitchBtn:checked {{
            border-radius: 9px;
            border: 1.5px solid #F3C669;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #D92B3A, stop:0.6 #9E1B24, stop:1 #6E1017
            );
            color: #FFF8EE;
        }}
        QFrame#UpdateBanner {{
            background-color: {badge_run_bg};
            border: 1px solid {badge_run_bd};
            border-radius: 7px;
            padding: 2px 6px;
        }}
        QLabel#UpdateBannerLabel {{
            color: {badge_run_fg};
            font-size: {max(8, fsize - 1)}pt;
            font-weight: 700;
            padding: 0px 4px;
        }}
        QPushButton#BtnUpdateBanner {{
            background-color: {accent};
            color: #FFFFFF;
            border: 1px solid {accent_h};
            border-radius: 5px;
            min-height: 22px;
            padding: 2px 10px;
            font-size: {max(8, fsize - 1)}pt;
            font-weight: 700;
        }}
        QPushButton#BtnUpdateBanner:hover {{
            background-color: {accent_h};
        }}
        QFrame#FFmpegWarningBanner {{
            background-color: {badge_pause_bg};
            border: 1px solid {badge_pause_bd};
            border-radius: 7px;
            padding: 4px 10px;
        }}
        QLabel#FFmpegWarningLabel {{
            color: {badge_pause_fg};
            font-size: {max(8, fsize - 1)}pt;
            font-weight: 700;
        }}

        /* ── Badges de Estado (Cola de Descargas y Cabecera) ── */
        QLabel#StatusBadge {{
            border-radius: 9px;
            padding: 2px 10px;
            font-size: {max(8, fsize - 1)}pt;
            font-weight: 700;
            background-color: {badge_wait_bg};
            color: {badge_wait_fg};
            border: 1px solid {badge_wait_bd};
        }}
        QLabel#StatusBadge[statusKind="running"] {{
            background-color: {badge_run_bg};
            color: {badge_run_fg};
            border: 1px solid {badge_run_bd};
        }}
        QLabel#StatusBadge[statusKind="completed"] {{
            background-color: {badge_ok_bg};
            color: {badge_ok_fg};
            border: 1px solid {badge_ok_bd};
        }}
        QLabel#StatusBadge[statusKind="paused"] {{
            background-color: {badge_pause_bg};
            color: {badge_pause_fg};
            border: 1px solid {badge_pause_bd};
        }}
        QLabel#StatusBadge[statusKind="error"] {{
            background-color: {badge_err_bg};
            color: {badge_err_fg};
            border: 1px solid {badge_err_bd};
        }}
        QLabel#StatusBadge[statusKind="queued"], QLabel#StatusBadge[statusKind="cancelled"] {{
            background-color: {badge_wait_bg};
            color: {badge_wait_fg};
            border: 1px solid {badge_wait_bd};
        }}
        QLabel#StatusBadge[headerSummary="true"] {{
            border-radius: 12px;
            border: 2px solid #5A7D9A;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #1D2C3A, stop:0.5 #15212C, stop:1 #0E161E
            );
            color: #D8EAFA;
            padding: 4px 12px;
        }}
        QLabel#StatusBadge[headerSummary="true"][statusKind="running"] {{
            border: 2px solid #5A7D9A;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #1D344A, stop:0.5 #162637, stop:1 #0F1A26
            );
            color: #BAE6FD;
        }}
        QLabel#StatusBadge[headerSummary="true"][statusKind="completed"] {{
            border: 2px solid #C59B5F;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #1B3B2B, stop:1 #0E2218
            );
            color: #A7F3D0;
        }}

        /* ── Barras de Progreso estilo "Cápsula de Fuego Líquido" ── */
        QProgressBar {{
            min-height: 20px;
            max-height: 20px;
            border-radius: 10px;
            border: 2px solid #B88A44;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #080406, stop:0.5 #160B0F, stop:1 #0A0507
            );
            text-align: center;
            color: #FFF8EE;
            font-size: {max(8, fsize - 1)}pt;
            font-weight: bold;
        }}
        QProgressBar::chunk {{
            border-radius: 8px;
            margin: 1px;
            border-top: 1px solid #FFE299;
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #6E0D17, stop:0.35 #C82333, stop:0.75 #F59E0B, stop:0.95 #FFE082, stop:1 #FFFBEB
            );
        }}
        QProgressBar[hasProgress="true"]::chunk {{
            min-width: 14px;
        }}
        QProgressBar[completed="true"] {{
            border: 2px solid #F6D076;
            border-radius: 10px;
            background: #1A0D08;
        }}
        QProgressBar[completed="true"]::chunk {{
            border-radius: 8px;
            border: 1px solid #FFE8A3;
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0.00 #5A0B12,
                stop:0.45 #9E1B24,
                stop:0.70 #D97706,
                stop:0.86 #FBBF24,
                stop:0.95 #FFFBEB,
                stop:1.00 #F59E0B
            );
        }}

        /* ── Tablas (Cola y Videoteca) ── */
        QTableWidget {{
            background-color: {bg_card};
            alternate-background-color: {bg_main};
            color: {txt};
            border: 1px solid {border};
            border-radius: 8px;
            gridline-color: {border};
            selection-background-color: {accent};
            selection-color: #FFFFFF;
            outline: none;
        }}
        QTableWidget::item {{
            padding: 6px 8px;
        }}
        QHeaderView::section {{
            background-color: {bg_side};
            color: {muted};
            padding: 8px 10px;
            border: none;
            border-right: 1px solid {border};
            border-bottom: 2px solid {accent};
            font-weight: 700;
        }}

        /* ── Consolas de Registro Monoespaciadas ── */
        QTextEdit {{
            background-color: {console_bg};
            color: {txt};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 8px 10px;
            font-family: {cls.MONO_FONT_STACK};
            selection-background-color: {accent};
            selection-color: #FFFFFF;
        }}

        /* ── Barras de Desplazamiento (QScrollBar) ── */
        QScrollBar:vertical {{
            background: {bg_side};
            width: 10px;
            margin: 2px 0px 2px 0px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical {{
            background: {border};
            min-height: 28px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {accent_h};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
            background: none;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        QScrollBar:horizontal {{
            background: {bg_side};
            height: 10px;
            margin: 0px 2px 0px 2px;
            border-radius: 5px;
        }}
        QScrollBar::handle:horizontal {{
            background: {border};
            min-width: 28px;
            border-radius: 5px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {accent_h};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
            background: none;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}
        """

    @classmethod
    def tag_widgets_once(cls, window):
        if getattr(window, "_mpp_widgets_tagged", False):
            return
        for lw in window.findChildren(QListWidget):
            lw.setFrameShape(QFrame.NoFrame)
            lw.setStyleSheet("")

        for cmb in window.findChildren(QComboBox):
            cmb.setCursor(Qt.PointingHandCursor)
            cmb.setStyleSheet("")

        for spn in window.findChildren(QSpinBox):
            spn.setCursor(Qt.PointingHandCursor)
            spn.setStyleSheet("")

        for chk in window.findChildren(QCheckBox):
            chk.setCursor(Qt.PointingHandCursor)
            chk.setStyleSheet("")

        preserved_frames = {
            "Sidebar", "MetaBox", "MetricTile", "MainArea", "Card", "SurfaceCard",
            "OptionSubCard", "OmniBar", "PageHeaderBar", "SidebarFooterCard", "InspectorCard",
            "ModeToggleFrame", "UpdateBanner", "FFmpegWarningBanner"
        }
        all_frames = [f for f in window.findChildren(QFrame) if f.__class__.__name__ == "QFrame"]
        for fr in all_frames:
            fr.setStyleSheet("")
            oname = fr.objectName() or ""
            if oname in preserved_frames:
                continue
            if 160 <= fr.maximumWidth() <= 290:
                fr.setObjectName("Sidebar")
                continue

            child_lbls = fr.findChildren(QLabel)
            child_inputs = (
                fr.findChildren(QPushButton) + fr.findChildren(QLineEdit) +
                fr.findChildren(QComboBox) + fr.findChildren(QSpinBox) +
                fr.findChildren(QCheckBox) + fr.findChildren(QProgressBar)
            )
            nested_frames = [nf for nf in fr.findChildren(QFrame) if nf is not fr and nf.__class__.__name__ == "QFrame"]

            if len(child_lbls) == 2 and len(child_inputs) == 0 and len(nested_frames) == 0:
                fr.setObjectName("MetaBox")
                child_lbls[0].setObjectName("MetaTitle")
                child_lbls[1].setObjectName("MetaValue")
            elif len(nested_frames) > 8:
                fr.setObjectName("MainArea")
            else:
                fr.setObjectName("Card")

        preserved_labels = {
            "MetaTitle", "MetaValue", "TileLabel", "TileValue", "BrandTitle", "BrandSub",
            "WorkspaceHdr", "SidebarSection", "SectionTitle", "SectionHeader", "SectionSub",
            "CardSub", "SubHint", "PreviewBox", "ThumbnailBox", "MediaHeroTitle",
            "PageHeaderTitle", "PageHeaderDesc", "SubCardTitle", "FieldLabel",
            "DiskLabel", "StatusBadge", "UpdateBannerLabel", "FFmpegWarningLabel"
        }
        for lbl in window.findChildren(QLabel):
            lbl.setStyleSheet("")
            if (lbl.objectName() or "") in preserved_labels:
                continue

        for btn in window.findChildren(QPushButton):
            btn.setCursor(Qt.PointingHandCursor)
            if getattr(btn, "_is_color_swatch", False):
                continue
            btn.setStyleSheet("")
            oname = btn.objectName() or ""
            if oname in (
                "AccentButton", "BtnPrimaryAction", "DangerButton", "CompactActionBtn",
                "NavBtn", "ModeSwitchBtn", "BtnUpdateBanner", "OmniActionBtn", "CancelQueueBtn"
            ):
                continue
            btxt = (btn.text() or "").strip()
            if btxt in ("Descargar", "Ejecutar Procesamiento") or "Iniciar" in btxt:
                btn.setObjectName("BtnPrimaryAction")

        for w_cls in (QProgressBar, QLineEdit, QTableWidget, QTextEdit):
            for w_inst in window.findChildren(w_cls):
                w_inst.setStyleSheet("")
        window._mpp_widgets_tagged = True

    @classmethod
    def apply_to_window(cls, window, theme_dict: dict = None):
        sm = getattr(window, "settings_mgr", None)
        if theme_dict is None:
            theme_dict, _ = cls.load_state(sm)
        window._active_ergonomic_theme = dict(theme_dict)
        cls.tag_widgets_once(window)
        qss = cls.build_qss(theme_dict)
        app_inst = QApplication.instance()
        if app_inst:
            app_inst.setStyleSheet("")
        window.setStyleSheet(qss)
        if hasattr(window, "lbl_brand_icon") and window.lbl_brand_icon is not None:
            accent = str(theme_dict.get("accent", "#C82333"))
            gold = str(theme_dict.get("border_gold", theme_dict.get("gold", "#D4AF37")))
            window.lbl_brand_icon.setPixmap(cls.build_vector_app_pixmap(54, accent, gold))
        if hasattr(window, "btn_add_queue") and window.btn_add_queue is not None:
            if window.btn_add_queue.graphicsEffect() is None:
                glow = QGraphicsDropShadowEffect(window.btn_add_queue)
                glow.setBlurRadius(18)
                glow.setOffset(0, 3)
                glow.setColor(QColor(245, 158, 11, 165))
                window.btn_add_queue.setGraphicsEffect(glow)
        if hasattr(window, "_refresh_sidebar_icons"):
            window._refresh_sidebar_icons()
        if hasattr(window, "_update_swatch_buttons"):
            window._update_swatch_buttons()
        window.update()

    @classmethod
    def build_customizer_page(cls, window) -> QWidget:
        sm = getattr(window, "settings_mgr", None)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        page = QWidget()
        page.setObjectName("ScrollPageContent")
        outer_lay = QVBoxLayout(page)
        outer_lay.setContentsMargins(0, 0, 6, 0)
        outer_lay.setSpacing(14)

        _, saved_preset = cls.load_state(sm)

        hdr_box = QGroupBox(tr("theme.hdr_title"))
        hdr_lay = QVBoxLayout(hdr_box)
        hdr_lay.setContentsMargins(14, 14, 14, 12)
        hdr_lay.setSpacing(10)
        desc = QLabel(tr("theme.hdr_desc"))
        desc.setWordWrap(True)
        desc.setObjectName("SectionSub")
        hdr_lay.addWidget(desc)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(10)
        lbl_preset = QLabel(tr("theme.lbl_preset"))
        lbl_preset.setObjectName("FieldLabel")
        lbl_preset.setMinimumWidth(140)
        cmb_preset = QComboBox()
        cmb_preset.setMinimumHeight(34)
        for k in cls.PRESETS.keys():
            disp_k = tr("theme.preset_dragon_forge") if k == cls.DEFAULT_PRESET else k
            cmb_preset.addItem(disp_k, k)

        idx_p = cmb_preset.findData(saved_preset)
        if idx_p < 0:
            idx_p = cmb_preset.findText(saved_preset)
        if idx_p >= 0:
            cmb_preset.setCurrentIndex(idx_p)

        btn_reset = QPushButton(tr("theme.btn_reset"))
        btn_reset.setMinimumHeight(34)
        btn_reset.setToolTip(tr("theme.btn_reset_tip"))
        preset_row.addWidget(lbl_preset)
        preset_row.addWidget(cmb_preset, 1)
        preset_row.addWidget(btn_reset)
        hdr_lay.addLayout(preset_row)
        outer_lay.addWidget(hdr_box)

        color_box = QGroupBox(tr("theme.color_title"))
        color_grid = QGridLayout(color_box)
        color_grid.setContentsMargins(14, 14, 14, 12)
        color_grid.setHorizontalSpacing(18)
        color_grid.setVerticalSpacing(10)

        color_fields = [
            ("accent", "theme.col_accent"),
            ("accent_hover", "theme.col_accent_hover"),
            ("bg_main", "theme.col_bg_main"),
            ("bg_card", "theme.col_bg_card"),
            ("bg_input", "theme.col_bg_input"),
            ("border", "theme.col_border"),
            ("text_main", "theme.col_text_main"),
            ("text_muted", "theme.col_text_muted")
        ]

        swatch_buttons = {}
        color_labels = []

        def make_pick_handler(key_name, tr_key):
            def _pick():
                curr_hex = window._active_ergonomic_theme.get(key_name, "#D13844")
                col = QColorDialog.getColor(
                    QColor(curr_hex), window,
                    tr("theme.pick_color_title", label=tr(tr_key))
                )
                if col.isValid():
                    new_hex = col.name().upper()
                    window._active_ergonomic_theme[key_name] = new_hex
                    if key_name == "bg_main":
                        window._active_ergonomic_theme["bg_sidebar"] = QColor(new_hex).darker(125).name().upper()
                    elif key_name == "bg_card":
                        window._active_ergonomic_theme["bg_subcard"] = QColor(new_hex).lighter(112).name().upper()
                    cls.save_state(window._active_ergonomic_theme, "Personalizado", sm)
                    cls.apply_to_window(window, window._active_ergonomic_theme)
            return _pick

        for row_idx, (k_col, tr_key) in enumerate(color_fields):
            lbl_c = QLabel(tr(tr_key))
            btn_c = QPushButton()
            btn_c._is_color_swatch = True
            btn_c.setFixedWidth(145)
            btn_c.setMinimumHeight(32)
            btn_c.setCursor(Qt.PointingHandCursor)
            btn_c.setToolTip(tr("theme.pick_color_tip"))
            btn_c.clicked.connect(make_pick_handler(k_col, tr_key))
            swatch_buttons[k_col] = btn_c
            color_labels.append((lbl_c, tr_key, btn_c))
            color_grid.addWidget(lbl_c, row_idx, 0)
            color_grid.addWidget(btn_c, row_idx, 1)

        outer_lay.addWidget(color_box)

        geo_box = QGroupBox(tr("theme.geo_title"))
        geo_grid = QGridLayout(geo_box)
        geo_grid.setContentsMargins(14, 14, 14, 12)
        geo_grid.setHorizontalSpacing(18)
        geo_grid.setVerticalSpacing(10)

        lbl_font = QLabel(tr("theme.lbl_font"))
        spn_font = QSpinBox()
        spn_font.setMinimumHeight(34)
        spn_font.setRange(9, 14)
        spn_font.setValue(int(window._active_ergonomic_theme.get("font_size", 10)))

        lbl_rad = QLabel(tr("theme.lbl_radius"))
        spn_rad = QSpinBox()
        spn_rad.setMinimumHeight(34)
        spn_rad.setRange(6, 14)
        spn_rad.setValue(int(window._active_ergonomic_theme.get("radius", 9)))

        def _on_geo_change():
            window._active_ergonomic_theme["font_size"] = spn_font.value()
            window._active_ergonomic_theme["radius"] = spn_rad.value()
            p_key = str(cmb_preset.currentData() or cmb_preset.currentText())
            cls.save_state(window._active_ergonomic_theme, p_key, sm)
            cls.apply_to_window(window, window._active_ergonomic_theme)

        spn_font.valueChanged.connect(_on_geo_change)
        spn_rad.valueChanged.connect(_on_geo_change)

        geo_grid.addWidget(lbl_font, 0, 0)
        geo_grid.addWidget(spn_font, 0, 1)
        geo_grid.addWidget(lbl_rad, 1, 0)
        geo_grid.addWidget(spn_rad, 1, 1)
        outer_lay.addWidget(geo_box)
        outer_lay.addStretch(1)

        def _update_swatches():
            t_curr = getattr(window, "_active_ergonomic_theme", {})
            for k_s, b_s in swatch_buttons.items():
                hx = t_curr.get(k_s, "#D13844").upper()
                qcol = QColor(hx)
                lum = (0.299 * qcol.red() + 0.587 * qcol.green() + 0.114 * qcol.blue())
                fg = "#111111" if lum > 145 else "#FFFFFF"
                b_s.setText(hx)
                b_s.setStyleSheet(
                    f"background-color: {hx}; color: {fg}; border: 1px solid #666666; "
                    f"border-radius: 6px; padding: 5px 10px; font-family: {cls.MONO_FONT_STACK}; font-weight: 700;"
                )

        def _retranslate_customizer():
            hdr_box.setTitle(tr("theme.hdr_title"))
            desc.setText(tr("theme.hdr_desc"))
            lbl_preset.setText(tr("theme.lbl_preset"))
            if cmb_preset.count() > 0 and cmb_preset.itemData(0) == cls.DEFAULT_PRESET:
                cmb_preset.blockSignals(True)
                cmb_preset.setItemText(0, tr("theme.preset_dragon_forge"))
                cmb_preset.blockSignals(False)
            btn_reset.setText(tr("theme.btn_reset"))
            btn_reset.setToolTip(tr("theme.btn_reset_tip"))
            color_box.setTitle(tr("theme.color_title"))
            for lbl_c, tr_key, btn_c in color_labels:
                lbl_c.setText(tr(tr_key))
                btn_c.setToolTip(tr("theme.pick_color_tip"))
            geo_box.setTitle(tr("theme.geo_title"))
            lbl_font.setText(tr("theme.lbl_font"))
            lbl_rad.setText(tr("theme.lbl_radius"))

        window._update_swatch_buttons = _update_swatches
        window._retranslate_customizer = _retranslate_customizer

        def _on_preset_selected(_idx_or_text=None):
            preset_name = str(cmb_preset.currentData() or cmb_preset.currentText() or "")
            if preset_name in cls.PRESETS:
                new_t = dict(cls.PRESETS[preset_name])
                spn_font.blockSignals(True)
                spn_rad.blockSignals(True)
                spn_font.setValue(int(new_t.get("font_size", 10)))
                spn_rad.setValue(int(new_t.get("radius", 9)))
                spn_font.blockSignals(False)
                spn_rad.blockSignals(False)
                cls.save_state(new_t, preset_name, sm)
                cls.apply_to_window(window, new_t)

        def _on_reset():
            idx_def = cmb_preset.findData(cls.DEFAULT_PRESET)
            if idx_def >= 0:
                cmb_preset.setCurrentIndex(idx_def)
            _on_preset_selected()

        cmb_preset.currentIndexChanged.connect(_on_preset_selected)
        btn_reset.clicked.connect(_on_reset)
        window._theme_preset_combo = cmb_preset
        _update_swatches()
        scroll.setWidget(page)
        return scroll


def _resolve_widget_arrow_color(widget) -> QColor:
    win = widget.window() if widget else None
    t = getattr(win, "_active_ergonomic_theme", None) if win else None
    if isinstance(t, dict):
        hex_c = t.get("text_main", "#F7F2EE") if widget.isEnabled() else t.get("text_muted", "#7A6A6D")
        return QColor(hex_c)
    return QColor("#F7F2EE" if widget.isEnabled() else "#7A6A6D")


# Renderizado vectorial directo en QComboBox y QSpinBox (imposible que Qt oculte las flechas)
if not getattr(QComboBox, "_mpp_arrow_patched", False):
    _orig_cmb_paint = QComboBox.paintEvent
    def _mpp_cmb_paint(self, event):
        _orig_cmb_paint(self, event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        col = _resolve_widget_arrow_color(self)
        p.setPen(QPen(col, 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        cx = self.width() - 14
        cy = self.height() // 2
        p.drawLine(cx - 5, cy - 2, cx, cy + 3)
        p.drawLine(cx, cy + 3, cx + 5, cy - 2)
        p.end()
    QComboBox.paintEvent = _mpp_cmb_paint
    QComboBox._mpp_arrow_patched = True

if not getattr(QSpinBox, "_mpp_arrow_patched", False):
    _orig_spn_paint = QSpinBox.paintEvent
    def _mpp_spn_paint(self, event):
        _orig_spn_paint(self, event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        col = _resolve_widget_arrow_color(self)
        p.setPen(QPen(col, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        cx = self.width() - 12
        cy_up = self.height() // 4 + 1
        cy_dn = (self.height() * 3) // 4 - 1
        # Flecha arriba (∧)
        p.drawLine(cx - 4, cy_up + 2, cx, cy_up - 2)
        p.drawLine(cx, cy_up - 2, cx + 4, cy_up + 2)
        # Flecha abajo (∨)
        p.drawLine(cx - 4, cy_dn - 2, cx, cy_dn + 2)
        p.drawLine(cx, cy_dn + 2, cx + 4, cy_dn - 2)
        p.end()
    QSpinBox.paintEvent = _mpp_spn_paint
    QSpinBox._mpp_arrow_patched = True


class DragonForgeSidebarFrame(QFrame):
    """Barra lateral con textura cacheada de escamas (~7%), borde derecho ornamentado y remaches."""
    def paintEvent(self, event):
        super().paintEvent(event)
        ErgonomicThemeEngine.paint_forged_overlay(self, event, is_sidebar=True)


class DragonForgeFooterFrame(QFrame):
    """Contenedor de almacenamiento lateral con filete interior dorado sutil."""
    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        if not p.isActive():
            return
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(QPen(QColor(224, 184, 102, 75), 1.0))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(3.5, 3.5, max(1.0, self.width() - 7.0), max(1.0, self.height() - 7.0)), 9.0, 9.0)
        p.end()


SurfaceCard._forge_overlay_painter = staticmethod(
    lambda card, ev: ErgonomicThemeEngine.paint_forged_overlay(card, ev, is_sidebar=False)
)


def load_transparent_asset(
    filename: str,
    opacity: float = 1.0,
    target_size: tuple[int, int] | None = None
) -> QPixmap:
    """Atajo modular a ErgonomicThemeEngine.load_transparent_asset."""
    return ErgonomicThemeEngine.load_transparent_asset(filename, opacity=opacity, target_size=target_size)


ErgonomicThemeEngine.APP_DIR = get_portable_data_dir()
ErgonomicThemeEngine.ICON_DIR = os.path.join(ErgonomicThemeEngine.APP_DIR, "ui_icons")

__all__ = [k for k in list(globals().keys()) if not k.startswith("__")]
