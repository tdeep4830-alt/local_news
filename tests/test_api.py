"""
Backend unit tests for api/api.py
Tests cover: auth endpoint, protected route enforcement, and news CRUD endpoints.
DB calls are mocked so no real SQLite file is touched.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Patch the DB module before api.py imports it
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Create a TestClient with the FastAPI app."""
    with patch.dict(os.environ, {
        "ADMIN_USERNAME": "admin",
        "ADMIN_PASSWORD": "testpass123",
        "JWT_SECRET_KEY": "a" * 64,
        "JWT_ALGORITHM": "HS256",
        "JWT_EXPIRE_MINUTES": "480",
    }):
        # Import app after env vars are set so HASHED_PASSWORD is correct
        import importlib
        import api.api as api_module
        importlib.reload(api_module)
        with TestClient(api_module.app) as c:
            yield c


@pytest.fixture(scope="module")
def auth_token(client):
    """Obtain a valid JWT by logging in."""
    res = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "testpass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_success(self, client):
        res = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "testpass123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 200
        body = res.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        res = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "wrongpassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 401

    def test_login_wrong_username(self, client):
        res = client.post(
            "/api/auth/login",
            data={"username": "hacker", "password": "testpass123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 401

    def test_login_missing_fields_returns_error(self, client):
        # OAuth2PasswordRequestForm requires both fields; omitting them gives 422
        res = client.post(
            "/api/auth/login",
            data={},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# Protected route enforcement
# ---------------------------------------------------------------------------

PROTECTED_ROUTES = [
    ("GET",   "/api/news"),
    ("GET",   "/api/news/pending"),
    ("GET",   "/api/news/1"),
    ("PATCH", "/api/news/1/status"),
    ("POST",  "/api/news/1/post"),
]

class TestProtectedRoutes:
    @pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
    def test_no_token_returns_401(self, client, method, path):
        res = client.request(method, path)
        assert res.status_code == 401

    @pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
    def test_invalid_token_returns_401(self, client, method, path):
        res = client.request(method, path, headers={"Authorization": "Bearer bad.token.here"})
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# News endpoints (with mocked DB)
# ---------------------------------------------------------------------------

# Fake DB row matching the schema:
# (id, o_title, o_content, t_title, shortened_title, t_content, img, area, source, source_url, status, created_at, last_updated, breaking)
FAKE_ROW = (
    1, "Original Title", "Original content", "Translated Title",
    "Short", "Translated content", "photo.jpg", "Liverpool",
    "echo", "http://example.com", "PENDING", "2024-01-01", "2024-01-01", 0
)

FAKE_ALL_ROWS = [FAKE_ROW]

class TestGetAllNews:
    def test_returns_news_list(self, client, auth_headers):
        with patch("script.news_db.get_all_news", return_value=FAKE_ALL_ROWS):
            res = client.get("/api/news", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert data[0]["id"] == 1
        assert data[0]["status"] == "PENDING"

    def test_empty_db_returns_empty_list(self, client, auth_headers):
        with patch("script.news_db.get_all_news", return_value=[]):
            res = client.get("/api/news", headers=auth_headers)
        assert res.status_code == 200
        assert res.json() == []


class TestGetOneNews:
    def test_existing_news(self, client, auth_headers):
        with patch("script.news_db.get_news_by_id", return_value=FAKE_ROW):
            res = client.get("/api/news/1", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == 1
        assert data["o_title"] == "Original Title"
        assert data["t_title"] == "Translated Title"

    def test_nonexistent_news_returns_404(self, client, auth_headers):
        with patch("script.news_db.get_news_by_id", return_value=None):
            res = client.get("/api/news/999", headers=auth_headers)
        assert res.status_code == 404


class TestGetPendingNews:
    def test_returns_pending_list(self, client, auth_headers):
        with patch("script.news_db.get_pending_news", return_value=[FAKE_ROW]):
            res = client.get("/api/news/pending", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["o_title"] == "Original Title"


class TestUpdateNews:
    NEWS_PAYLOAD = {
        "o_title": "New Title",
        "o_content": "New content",
        "t_title": "New T Title",
        "t_content": "New T content",
        "area": "Wirral",
        "source_url": "http://example.com",
        "img_path": None,
        "shortened_title": None,
        "breaking": 0,
        "status": "APPROVED",
    }

    def test_update_news_success(self, client, auth_headers):
        with patch("script.news_db.update_news_content") as mock_update:
            res = client.put("/api/news/1", json=self.NEWS_PAYLOAD, headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["message"] == "更新成功"
        mock_update.assert_called_once()


class TestPostToSocialMedia:
    def test_post_success(self, client, auth_headers):
        with patch("script.news_db.get_news_by_id", return_value=FAKE_ROW), \
             patch("script.news_db.update_status") as mock_status:
            res = client.post("/api/news/1/post", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["status"] == "success"
        mock_status.assert_called_once_with(1, "POSTED")

    def test_post_nonexistent_returns_404(self, client, auth_headers):
        with patch("script.news_db.get_news_by_id", return_value=None):
            res = client.post("/api/news/999/post", headers=auth_headers)
        assert res.status_code == 404
