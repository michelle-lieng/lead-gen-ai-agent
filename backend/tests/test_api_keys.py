import inspect

import pytest

from app.api.deps import get_api_keys
from app.config import settings
from app.exceptions import ApiKeyNotConfiguredError


def test_keys_come_from_the_environment(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-o")
    monkeypatch.setattr(settings, "jina_api_key", "jn")
    monkeypatch.setattr(settings, "google_places_api_key", "gk")
    keys = get_api_keys()
    assert (keys.require_openai(), keys.require_jina(), keys.require_google()) == ("sk-o", "jn", "gk")


def test_a_missing_key_names_its_env_var(monkeypatch):
    monkeypatch.setattr(settings, "google_places_api_key", None)
    with pytest.raises(ApiKeyNotConfiguredError, match="GOOGLE_PLACES_API_KEY"):
        get_api_keys().require_google()


def test_request_headers_are_not_read():
    assert list(inspect.signature(get_api_keys).parameters) == []
