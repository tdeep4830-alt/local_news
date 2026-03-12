"""
Unit tests for script/news_db.py
Uses an in-memory SQLite DB (via monkeypatching) so the real news_system.db is never touched.
"""
import pytest
import sqlite3
from unittest.mock import patch
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import script.news_db as db

# ---------------------------------------------------------------------------
# In-memory DB fixture
# ---------------------------------------------------------------------------

CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_title TEXT,
        original_content TEXT,
        translated_title TEXT,
        shortened_title TEXT,
        translated_content TEXT,
        image_path TEXT,
        area TEXT,
        source TEXT,
        source_url TEXT,
        status TEXT DEFAULT 'PENDING',
        created_at DATETIME,
        last_updated DATETIME,
        breaking INTEGER DEFAULT 0
    )
"""

class _NoCloseConn:
    """Wraps a sqlite3.Connection but makes close() a no-op."""
    def __init__(self, conn):
        self._conn = conn

    def close(self):
        pass  # intentional no-op

    def __getattr__(self, name):
        return getattr(self._conn, name)


@pytest.fixture(autouse=True)
def in_memory_db(monkeypatch):
    """
    Replace sqlite3.connect with a function that always returns the same
    in-memory connection. We wrap it to suppress close() so the DB survives
    the multiple open/close calls inside each db function.
    """
    real_conn = sqlite3.connect(":memory:")
    real_conn.execute(CREATE_TABLE)
    real_conn.commit()

    wrapped = _NoCloseConn(real_conn)
    monkeypatch.setattr(sqlite3, "connect", lambda *a, **kw: wrapped)
    yield wrapped

    real_conn.close()


# ---------------------------------------------------------------------------
# save_news
# ---------------------------------------------------------------------------

class TestSaveNews:
    def test_saves_and_returns_id(self):
        news_id = db.save_news({
            "o_title": "Title",
            "o_content": "Content",
            "t_title": "T-Title",
            "t_content": "T-Content",
            "area": "Liverpool",
            "source_url": "http://example.com",
            "source": "echo",
        })
        assert news_id == 1

    def test_saves_multiple_rows(self):
        for i in range(3):
            db.save_news({"o_title": f"Title {i}", "source_url": f"http://example.com/{i}"})
        row = db.get_all_news()
        assert len(row) == 3

    def test_breaking_defaults_to_zero(self):
        db.save_news({"o_title": "T", "source_url": "http://x.com"})
        row = db.get_all_news()[0]
        assert row[13] == 0  # breaking column

    def test_breaking_can_be_set(self):
        db.save_news({"o_title": "T", "source_url": "http://x.com", "breaking": 1})
        row = db.get_all_news()[0]
        assert row[13] == 1


# ---------------------------------------------------------------------------
# get_all_news
# ---------------------------------------------------------------------------

class TestGetAllNews:
    def test_empty_db_returns_empty_list(self):
        assert db.get_all_news() == []

    def test_returns_all_rows(self):
        db.save_news({"o_title": "A", "source_url": "http://a.com"})
        db.save_news({"o_title": "B", "source_url": "http://b.com"})
        rows = db.get_all_news()
        assert len(rows) == 2


# ---------------------------------------------------------------------------
# get_pending_news
# ---------------------------------------------------------------------------

class TestGetPendingNews:
    def test_only_returns_pending(self, in_memory_db):
        db.save_news({"o_title": "Pending", "source_url": "http://a.com"})
        # Manually insert an APPROVED row
        in_memory_db.execute(
            "INSERT INTO news (original_title, source_url, status, created_at, last_updated) "
            "VALUES (?, ?, 'APPROVED', ?, ?)",
            ("Approved", "http://b.com", datetime.now(), datetime.now())
        )
        in_memory_db.commit()
        pending = db.get_pending_news()
        assert len(pending) == 1
        assert pending[0][1] == "Pending"


# ---------------------------------------------------------------------------
# get_news_by_id
# ---------------------------------------------------------------------------

class TestGetNewsById:
    def test_returns_correct_row(self):
        news_id = db.save_news({"o_title": "Find Me", "source_url": "http://x.com"})
        row = db.get_news_by_id(news_id)
        assert row is not None
        assert row[1] == "Find Me"

    def test_returns_none_for_missing_id(self):
        assert db.get_news_by_id(9999) is None


# ---------------------------------------------------------------------------
# update_news_content
# ---------------------------------------------------------------------------

class TestUpdateNewsContent:
    def test_updates_fields(self):
        news_id = db.save_news({"o_title": "Old", "source_url": "http://x.com"})
        # Signature: (news_id, o_title, o_content, t_title, t_content, img_path, area, source_url, breaking, status)
        db.update_news_content(
            news_id, "New Title", "New content",
            "New T-Title", "New T-Content",
            "photo.jpg", "Wirral", "http://x.com",
            1, "APPROVED"
        )
        row = db.get_news_by_id(news_id)
        assert row[1] == "New Title"
        assert row[10] == "APPROVED"
        assert row[13] == 1  # breaking


class TestUpdateStatus:
    def test_updates_status(self):
        news_id = db.save_news({"o_title": "T", "source_url": "http://x.com"})
        db.update_status(news_id, "POSTED")
        row = db.get_news_by_id(news_id)
        assert row[10] == "POSTED"

    def test_update_status_nonexistent_id_does_not_raise(self):
        db.update_status(9999, "POSTED")  # should not raise


# ---------------------------------------------------------------------------
# get_id_by_link
# ---------------------------------------------------------------------------

class TestGetIdByLink:
    def test_finds_existing_url(self):
        db.save_news({"o_title": "T", "source_url": "http://unique.com"})
        found_id = db.get_id_by_link("http://unique.com")
        assert found_id == 1

    def test_returns_none_for_unknown_url(self):
        assert db.get_id_by_link("http://nothere.com") is None
