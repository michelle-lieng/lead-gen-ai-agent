import pytest

from app.config import settings
from app.services.auth_service import (
    TOKEN_LIFETIME_SECONDS,
    auth_configured,
    check_password,
    issue_token,
    verify_token,
)


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(settings, "app_password", "pw-1")
    monkeypatch.setattr(settings, "auth_secret", "secret-1")


def test_a_fresh_token_verifies():
    assert verify_token(issue_token(now=1000), now=1001)


def test_an_expired_token_fails():
    assert not verify_token(issue_token(now=1000), now=1000 + TOKEN_LIFETIME_SECONDS + 1)


def test_an_extended_expiry_with_the_old_signature_fails():
    expiry, signature = issue_token(now=1000).split(".")
    assert not verify_token(f"{int(expiry) + 3600}.{signature}", now=1001)


def test_malformed_tokens_fail():
    for token in [None, "", "abc", "1.2.3", "x.y"]:
        assert not verify_token(token, now=0)


def test_changing_the_password_signs_everyone_out(monkeypatch):
    token = issue_token(now=1000)
    monkeypatch.setattr(settings, "app_password", "pw-2")
    assert not verify_token(token, now=1001)


def test_check_password():
    assert check_password("pw-1")
    assert not check_password("pw-2")
    assert not check_password("")


def test_nothing_verifies_when_auth_is_not_configured(monkeypatch):
    token = issue_token(now=1000)
    monkeypatch.setattr(settings, "auth_secret", "")
    assert not auth_configured()
    assert not verify_token(token, now=1001)
    assert not check_password("pw-1")
