"""The password login, the key status and the session guard, on a minimal app
(importing app.main would pull in the database)."""

import pytest
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.auth_guard import require_session
from app.api.routes import auth
from app.config import settings
from app.exceptions import AppError


def build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/auth")

    @app.get("/api/ping")
    def ping():
        return {"ok": True}

    @app.get("/api/health")
    def health():
        return {"status": "healthy"}

    @app.get("/docs-like")
    def docs_like():
        return {}

    @app.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc), "code": exc.code})

    app.middleware("http")(require_session)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    return app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "app_password", "pw-1")
    monkeypatch.setattr(settings, "auth_secret", "secret-1")
    monkeypatch.setattr(auth, "FAILED_LOGIN_DELAY_SECONDS", 0)
    return TestClient(build_app())


@pytest.fixture
def token(client):
    return client.post("/api/auth/login", json={"password": "pw-1"}).json()["token"]


def test_login_returns_a_token_that_opens_the_api(client, token):
    assert client.get("/api/ping", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_wrong_password_is_401(client):
    response = client.post("/api/auth/login", json={"password": "nope"})
    assert (response.status_code, response.json()["code"]) == (401, "INVALID_PASSWORD")


def test_no_token_is_401_with_cors_headers(client):
    response = client.get("/api/ping", headers={"Origin": "http://app.test"})
    assert (response.status_code, response.json()["code"]) == (401, "SESSION_REQUIRED")
    assert response.headers["access-control-allow-origin"]


def test_a_crafted_host_header_cannot_change_the_path_the_guard_sees(client):
    # Starlette rebuilds request.url from the Host header, so "a#" would turn
    # the path the guard reads into "" while routing still serves /api/ping.
    for host in ["a#", "x/y?"]:
        assert client.get("/api/ping", headers={"host": host}).status_code == 401


def test_a_bad_token_is_401(client):
    assert client.get("/api/ping", headers={"Authorization": "Bearer 1.abc"}).status_code == 401


def test_scheme_case_and_spacing_are_tolerated(client, token):
    headers = {"Authorization": f"  bearer   {token} "}
    assert client.get("/api/ping", headers=headers).status_code == 200


def test_health_login_preflight_and_non_api_paths_are_open(client):
    assert client.get("/api/health").status_code == 200
    preflight = {"Origin": "http://app.test", "Access-Control-Request-Method": "GET"}
    assert client.options("/api/ping", headers=preflight).status_code == 200
    assert client.get("/docs-like").status_code == 200


def test_unconfigured_auth_is_503_everywhere(client, monkeypatch):
    monkeypatch.setattr(settings, "auth_secret", "")
    assert client.get("/api/ping").json()["code"] == "AUTH_NOT_CONFIGURED"
    assert client.post("/api/auth/login", json={"password": "pw-1"}).status_code == 503


def test_status_reports_which_keys_the_server_has(client, token, monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-x")
    monkeypatch.setattr(settings, "jina_api_key", " ")
    monkeypatch.setattr(settings, "google_places_api_key", None)
    response = client.get("/api/auth/status", headers={"Authorization": f"Bearer {token}"})
    assert response.json() == {"openai": True, "jina": False, "google": False}


def test_status_needs_a_session(client):
    assert client.get("/api/auth/status").status_code == 401
