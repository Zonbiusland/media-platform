# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import pytest

from mpp.core import DatabaseManager


class TestDatabaseManagerIsolated:
    def test_insert_search_and_delete_in_temp_sqlite(self, tmp_path):
        db_file = tmp_path / "isolated_library.db"
        db = DatabaseManager(privacy_mode=False, db_path=str(db_file))

        sample_file = tmp_path / "video_demo.mp4"
        sample_file.write_bytes(b"contenido_multimedia_prueba")

        meta = {
            "video_id": "abc123xyz",
            "title": "Documental de Software Libre 100% Auditable",
            "channel": "Canal GNU",
            "platform": "YouTube",
            "resolution": "1080p",
            "fps": "60",
            "hdr": "SDR",
            "vcodec": "H264",
            "acodec": "AAC",
            "filepath": str(sample_file),
            "filesize": sample_file.stat().st_size,
            "file_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        }
        db.add_record(meta)

        rows = db.search_library("Software Libre")
        assert len(rows) == 1
        assert rows[0]["video_id"] == "abc123xyz"
        assert rows[0]["channel"] == "Canal GNU"

        # Verificar que una búsqueda con comodines SQL ('%' o '_') se escapa literalmente
        assert db.search_library("100%") == rows
        assert db.search_library("%_inexistente_%") == []

        # Verificar detección de duplicados cuando el archivo existe en disco
        dup = db.find_existing_download("abc123xyz", "YouTube")
        assert dup is not None
        assert dup["filepath"] == str(sample_file)

        # Eliminar registro individual
        db.delete_record(rows[0]["id"])
        assert db.search_library() == []

    def test_in_memory_database_and_clear_history(self):
        db = DatabaseManager(privacy_mode=False, db_path=":memory:")
        for idx in range(3):
            db.add_record({
                "video_id": f"vid_{idx}",
                "title": f"Vídeo de prueba #{idx}",
                "channel": "Autor",
                "platform": "Web",
            })

        all_rows = db.search_library()
        assert len(all_rows) == 3

        db.clear_history()
        assert db.search_library() == []

    def test_privacy_mode_prevents_persistence(self, tmp_path):
        db_file = tmp_path / "privacy_test.db"
        db = DatabaseManager(privacy_mode=True, db_path=str(db_file))
        db.add_record({
            "video_id": "secret_01",
            "title": "No debe guardarse en modo privacidad",
            "channel": "Privado",
            "platform": "YouTube",
        })
        assert db.search_library() == []
