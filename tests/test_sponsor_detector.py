# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from mpp.core import SmartSponsorDetector


SAMPLE_SPONSORED_VTT = """WEBVTT
Kind: captions
Language: es

00:00:05.000 --> 00:00:15.000
Bienvenidos a un nuevo análisis técnico de arquitectura de sistemas en Linux.

00:00:15.500 --> 00:00:35.000
Hoy veremos cómo funcionan los descriptores de archivos y las tuberías en el kernel.

00:01:10.000 --> 00:01:18.000
Pero antes de continuar, este vídeo está patrocinado por NordShield VPN.

00:01:18.500 --> 00:01:32.000
Protege tu conexión en redes públicas y accede a servidores de alta velocidad.

00:01:32.500 --> 00:01:48.000
Usa el código de descuento ESTUDIO50 en el enlace en la descripción para obtener un 60% de descuento.

00:01:48.500 --> 00:01:56.000
Muchas gracias a NordShield por patrocinar este episodio. Ahora sí, volvamos al vídeo.

00:02:00.000 --> 00:02:30.000
Como veíamos en la terminal, el comando lsof nos permite listar todos los descriptores abiertos.
"""

SAMPLE_NORMAL_VTT = """WEBVTT
Kind: captions
Language: es

00:00:02.000 --> 00:00:12.000
En esta clase de programación en Python estudiaremos estructuras de datos y árboles binarios.

00:00:12.500 --> 00:00:28.000
Un árbol binario de búsqueda mantiene la propiedad de orden entre sus nodos izquierdo y derecho.

00:00:29.000 --> 00:00:45.000
La complejidad temporal de búsqueda promedio es logarítmica respecto al número de elementos.

00:00:46.000 --> 00:01:05.000
Gracias por ver esta lección académica y nos vemos en el próximo capítulo del curso.
"""


class TestSmartSponsorDetectorOffline:
    def test_detects_sponsored_segment_from_vtt_file(self, tmp_path):
        vtt_path = tmp_path / "video_con_sponsor.es.vtt"
        vtt_path.write_text(SAMPLE_SPONSORED_VTT, encoding="utf-8")

        cues = SmartSponsorDetector.parse_subtitle_file(str(vtt_path))
        assert len(cues) >= 6

        segments = SmartSponsorDetector.detect_sponsor_segments(cues, duration=240.0)
        assert len(segments) == 1

        seg = segments[0]
        # El bloque patrocinado empieza en 01:10 (70s) y cierra en 01:56 (116s) -> 46s de duración
        assert 68.0 <= seg["start"] <= 72.0
        assert 110.0 <= seg["end"] <= 120.0
        assert 30.0 <= seg["duration"] <= 90.0
        assert len(seg["phrases"]) >= 1

    def test_does_not_cut_normal_non_sponsored_content(self, tmp_path):
        vtt_path = tmp_path / "video_educativo_normal.es.vtt"
        vtt_path.write_text(SAMPLE_NORMAL_VTT, encoding="utf-8")

        cues = SmartSponsorDetector.parse_subtitle_file(str(vtt_path))
        assert len(cues) == 4

        segments = SmartSponsorDetector.detect_sponsor_segments(cues, duration=120.0)
        assert segments == []

    def test_detects_english_sponsored_block_from_srt(self, tmp_path):
        srt_content = (
            "1\n00:00:10,000 --> 00:00:25,000\nWelcome back to our hardware benchmark review.\n\n"
            "2\n00:01:00,000 --> 00:01:12,000\nThis video is sponsored by AcmeCloud Hosting.\n\n"
            "3\n00:01:12,500 --> 00:01:28,000\nDeploy your Linux servers in seconds with global NVMe storage.\n\n"
            "4\n00:01:28,500 --> 00:01:42,000\nClick the link in the description and use promo code ACME2026.\n\n"
            "5\n00:01:42,500 --> 00:01:48,000\nThanks to AcmeCloud for sponsoring. Now let's get back to the video.\n\n"
            "6\n00:01:50,000 --> 00:02:20,000\nHere are the GPU temperature charts under full load.\n"
        )
        srt_path = tmp_path / "english_review.en.srt"
        srt_path.write_text(srt_content, encoding="utf-8")

        cues = SmartSponsorDetector.parse_subtitle_file(str(srt_path))
        segments = SmartSponsorDetector.detect_sponsor_segments(cues, duration=180.0)
        assert len(segments) == 1
        assert 58.0 <= segments[0]["start"] <= 62.0
        assert 100.0 <= segments[0]["end"] <= 110.0
