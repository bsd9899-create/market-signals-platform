"""
tests/test_command_listener.py
-------------------------------------
اختبار حقيقي لـTelegramCommandListener - **بلا أي اتصال شبكة إطلاقاً**:
provider._client.get تُستبدَل بدالة وهمية تُرجِع httpx.Response حقيقية
(نفس أسلوب test_alpaca_provider.py).
"""

from __future__ import annotations

import httpx
import pytest

from app.infrastructure.telegram import command_listener as command_listener_module
from app.infrastructure.telegram.command_listener import TelegramCommandListener

_DUMMY_REQUEST = httpx.Request("GET", "https://example.invalid/")


def _response(status_code: int, json_body: dict) -> httpx.Response:
    return httpx.Response(status_code=status_code, json=json_body, request=_DUMMY_REQUEST)


def _update(update_id: int, chat_id: int, text: str) -> dict:
    return {"update_id": update_id, "message": {"chat": {"id": chat_id}, "text": text}}


def test_poll_parses_new_text_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    listener = TelegramCommandListener("123:FAKE")
    body = {"ok": True, "result": [_update(1001, 555, "تجربة"), _update(1002, 555, "hello")]}
    monkeypatch.setattr(listener._client, "get", lambda url, params=None: _response(200, body))

    messages = listener.poll()
    assert len(messages) == 2
    assert messages[0].chat_id == "555"
    assert messages[0].text == "تجربة"
    assert messages[1].text == "hello"


def test_poll_advances_offset_past_last_update_id(monkeypatch: pytest.MonkeyPatch) -> None:
    listener = TelegramCommandListener("123:FAKE")
    calls: list[dict] = []

    def fake_get(url: str, params=None):
        calls.append(params or {})
        return _response(200, {"ok": True, "result": [_update(2001, 555, "test")]})

    monkeypatch.setattr(listener._client, "get", fake_get)

    listener.poll()
    assert "offset" not in calls[0]  # أول استدعاء: بلا offset

    listener.poll()
    assert calls[1]["offset"] == 2002  # الاستدعاء الثاني: update_id + 1


def test_poll_ignores_updates_without_text(monkeypatch: pytest.MonkeyPatch) -> None:
    listener = TelegramCommandListener("123:FAKE")
    body = {"ok": True, "result": [{"update_id": 1, "message": {"chat": {"id": 555}, "sticker": {}}}]}
    monkeypatch.setattr(listener._client, "get", lambda url, params=None: _response(200, body))

    assert listener.poll() == []


def test_poll_empty_result_returns_empty_list(monkeypatch: pytest.MonkeyPatch) -> None:
    listener = TelegramCommandListener("123:FAKE")
    monkeypatch.setattr(listener._client, "get", lambda url, params=None: _response(200, {"ok": True, "result": []}))
    assert listener.poll() == []


def test_poll_http_error_status_returns_empty_list_not_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(command_listener_module, "_ERROR_BACKOFF_SECONDS", 0.01)
    listener = TelegramCommandListener("123:FAKE", poll_timeout_seconds=1.0)
    monkeypatch.setattr(listener._client, "get", lambda url, params=None: _response(409, {"ok": False, "description": "Conflict"}))
    assert listener.poll() == []


def test_poll_network_exception_returns_empty_list_not_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(command_listener_module, "_ERROR_BACKOFF_SECONDS", 0.01)
    listener = TelegramCommandListener("123:FAKE", poll_timeout_seconds=1.0)

    def raise_error(url: str, params=None):
        raise httpx.ConnectError("network down")

    monkeypatch.setattr(listener._client, "get", raise_error)
    assert listener.poll() == []
