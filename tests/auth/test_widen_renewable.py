"""Offline acceptance checks for Widen's renewable CLI session (#2941)."""
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from kernel.clock import now_utc, timedelta

from specify_cli.auth.session import StoredSession, Team
from specify_cli.saas_client.client import SaasClient
from specify_cli.saas_client.errors import SaasAuthError, SaasConsentError

pytestmark = [pytest.mark.unit, pytest.mark.fast]


@pytest.fixture
def login(monkeypatch):
    now = now_utc()
    session = StoredSession(
        user_id="u1", email="u@example.test", name="User",
        teams=[Team("private", "Private", "owner", True), Team("team", "Team", "member")],
        default_team_id="private", access_token="old", refresh_token="refresh",
        session_id="s1", issued_at=now, access_token_expires_at=now + timedelta(hours=1),
        refresh_token_expires_at=None, scope="openid", storage_backend="file",
        last_used_at=now, auth_method="device_code", issuer_url="https://team.example",
    )
    manager = MagicMock()
    manager.get_current_session.return_value = session
    manager.is_authenticated = True
    manager.get_access_token = AsyncMock(side_effect=lambda: manager.get_current_session().access_token)
    async def refresh():
        session.access_token = "renewed"
        return True
    manager.refresh_if_needed = AsyncMock(side_effect=refresh)
    monkeypatch.setattr("specify_cli.saas_client.client.get_token_manager", lambda: manager)
    monkeypatch.setattr("specify_cli.auth.transport.get_token_manager", lambda: manager)
    return manager, session


def make_client(handler):
    return SaasClient("https://team.example", "old", _http=httpx.Client(transport=httpx.MockTransport(handler)))


def test_widen_uses_rotated_token(login):
    manager, session = login
    sent = []
    client = make_client(lambda request: sent.append(request) or httpx.Response(200, json={}))
    session.access_token = "rotated"
    client.post_widen("decision", [7])
    assert sent[0].headers["Authorization"] == "Bearer rotated"


def test_widen_refreshes_and_retries_once(login):
    manager, session = login
    sent = []
    def handler(request):
        sent.append(request)
        return httpx.Response(401, json={"error": "access_token_expired"}) if len(sent) == 1 else httpx.Response(200, json={})
    client = make_client(handler)
    client.post_widen("decision", [7])
    assert [r.headers["Authorization"] for r in sent] == ["Bearer old", "Bearer renewed"]
    assert sent[0].content == sent[1].content
    manager.refresh_if_needed.assert_awaited_once()


def test_widen_logout_prevents_send(login):
    manager, session = login
    sent = []
    client = make_client(lambda request: sent.append(request) or httpx.Response(200, json={}))
    manager.get_current_session.return_value = None
    with pytest.raises((SaasAuthError, SaasConsentError)):
        client.post_widen("decision", [7])
    assert sent == []


def test_widen_refresh_identity_change_prevents_replay(login):
    manager, session = login
    sent = []
    async def refresh():
        session.access_token = "renewed"
        session.user_id = "other-user"
    manager.refresh_if_needed.side_effect = refresh
    client = make_client(lambda request: sent.append(request) or httpx.Response(401, json={"error": "access_token_expired"}))
    with pytest.raises((SaasAuthError, SaasConsentError)):
        client.post_widen("decision", [7])
    assert len(sent) == 1
    manager.refresh_if_needed.assert_awaited_once()
