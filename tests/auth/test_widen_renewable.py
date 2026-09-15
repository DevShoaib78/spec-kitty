"""Offline acceptance checks for Widen's renewable CLI session (#2941)."""

from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

import httpx
import pytest
from kernel.clock import now_utc, timedelta

from specify_cli.auth.session import StoredSession, Team
from specify_cli.saas_client.client import SaasClient
from specify_cli.saas_client.errors import SaasAuthError, SaasConsentError

pytestmark = [pytest.mark.unit, pytest.mark.fast]


@pytest.fixture
def login(monkeypatch):
    monkeypatch.setattr("specify_cli.zeitgeist_client.repo_identity.origin_url", lambda cwd, deadline: "https://github.com/acme/project.git")
    now = now_utc()
    session = StoredSession(
        user_id="u1",
        email="u@example.test",
        name="User",
        teams=[Team("private", "Private", "owner", True), Team("team", "Team", "member")],
        default_team_id="private",
        access_token="old",
        refresh_token="refresh",
        session_id="s1",
        issued_at=now,
        access_token_expires_at=now + timedelta(hours=1),
        refresh_token_expires_at=None,
        scope="openid",
        storage_backend="file",
        last_used_at=now,
        auth_method="device_code",
        issuer_url="https://team.example",
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
    def admitted_transport(request):
        if "repo-admission" in request.url.path:
            return httpx.Response(200, json={"admitted": True, "repo_slug": "acme/project", "team": {"id": "team", "slug": "team"}})
        return handler(request)

    return SaasClient("https://team.example", "old", project_root=Path("/synthetic/project"), _http=httpx.Client(transport=httpx.MockTransport(admitted_transport)))


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


def test_widen_persistent_401_is_bounded(login):
    manager, session = login
    sent = []
    client = make_client(lambda request: sent.append(request) or httpx.Response(401, json={"error": "access_token_expired"}))
    with pytest.raises(SaasAuthError):
        client.post_widen("decision", [7])
    assert len(sent) == 2
    manager.refresh_if_needed.assert_awaited_once()


def test_widen_issuer_change_prevents_send(login):
    manager, session = login
    sent = []
    client = make_client(lambda request: sent.append(request) or httpx.Response(200, json={}))
    session.issuer_url = "https://other.example"
    with pytest.raises(SaasConsentError):
        client.post_widen("decision", [7])
    assert sent == []


def test_widen_refresh_revocation_never_replays(login):
    from specify_cli.auth.errors import SessionInvalidError

    manager, session = login
    sent = []
    manager.refresh_if_needed.side_effect = SessionInvalidError("revoked")
    client = make_client(lambda request: sent.append(request) or httpx.Response(401, json={"error": "access_token_expired"}))
    with pytest.raises(SaasAuthError):
        client.post_widen("decision", [7])
    assert len(sent) == 1


@pytest.mark.parametrize("legacy_file", [False, True])
def test_widen_factory_uses_login_session(login, monkeypatch, tmp_path, legacy_file):
    from specify_cli.saas_client import auth
    from types import SimpleNamespace

    manager, session = login
    monkeypatch.setattr(auth, "_token_manager", lambda: manager)
    monkeypatch.setattr(auth, "_resolved_server_target", lambda: SimpleNamespace(resolved_server_url="https://team.example"))
    (tmp_path / ".kittify").mkdir()
    if legacy_file:
        (tmp_path / ".kittify" / "saas-auth.json").write_text('{"token":"legacy","saas_url":"https://untrusted.example"}')
    client = SaasClient.from_env(tmp_path)
    assert client._base_url == "https://team.example"
    assert client._token == "old"


def test_legacy_credential_file_is_ignored_in_consumer_contract():
    from specify_cli.state.contract import get_runtime_gitignore_entries

    assert ".kittify/saas-auth.json" in get_runtime_gitignore_entries()


def test_prerequisite_timeout_reaches_canonical_transport(login):
    sent = []

    def handler(request):
        sent.append(request)
        return httpx.Response(200, json={"admitted": True, "repo_slug": "acme/project", "team": {"id": "team", "slug": "team"}})

    client = SaasClient("https://team.example", "old", project_root=Path("/synthetic/project"), _http=httpx.Client(transport=httpx.MockTransport(handler)))
    client.get_team_integrations("team")
    assert len(sent) == 2
    assert [request.extensions["timeout"]["read"] for request in sent] == [0.5, 0.5]


def test_widen_from_encrypted_login_and_logout(login, monkeypatch, tmp_path):
    """Exercise ordinary login persistence and a new process's session reader."""
    import respx
    from specify_cli.auth.secure_storage import EncryptedFileStorage
    from specify_cli.auth.token_manager import TokenManager

    _, session = login
    storage = EncryptedFileStorage(base_dir=tmp_path / "encrypted-auth")
    TokenManager(storage, saas_base_url="https://team.example").set_session(session)
    assert session.access_token not in (tmp_path / "encrypted-auth" / "session.json").read_text()
    manager = TokenManager(storage, saas_base_url="https://team.example")
    manager.load_from_storage_sync()
    assert manager.get_current_session() is not session
    monkeypatch.setattr("specify_cli.auth.get_token_manager", lambda: manager)
    monkeypatch.setattr("specify_cli.saas_client.client.get_token_manager", lambda: manager)
    monkeypatch.setattr("specify_cli.auth.transport.get_token_manager", lambda: manager)
    monkeypatch.setenv("SPEC_KITTY_SAAS_URL", "https://team.example")
    monkeypatch.delenv("SPEC_KITTY_SAAS_TOKEN", raising=False)
    project = tmp_path / "project"
    project.mkdir()
    assert not (project / ".kittify" / "saas-auth.json").exists()
    with respx.mock as router:
        router.get("https://team.example/api/v1/sync/repo-admission/").mock(
            return_value=httpx.Response(200, json={"admitted": True, "repo_slug": "acme/project", "team": {"id": "team", "slug": "team"}})
        )
        endpoint = router.post("https://team.example/a/team/collaboration/decision-points/decision/widen").mock(return_value=httpx.Response(200, json={}))
        client = SaasClient.from_env(project)
        client.post_widen("decision", [7])
        assert endpoint.call_count == 1
        assert endpoint.calls[0].request.headers["Authorization"] == "Bearer old"
        manager.clear_session()
        with pytest.raises(SaasAuthError):
            client.post_widen("decision", [7])
        assert endpoint.call_count == 1
        assert storage.read() is None


def test_widen_read_timeout_never_replays_or_falls_back(login, monkeypatch):
    from specify_cli.saas_client.errors import SaasTimeoutError

    fallback = MagicMock(side_effect=AssertionError("mutation replay is forbidden"))
    monkeypatch.setattr("specify_cli.auth.http.transport.request_with_stdlib_fallback_sync", fallback)
    sent = []

    def timed_out(request):
        sent.append(request)
        raise httpx.ReadTimeout("response lost after server accepted request", request=request)

    client = make_client(timed_out)
    with pytest.raises(SaasTimeoutError):
        client.post_widen("decision", [7])
    assert len(sent) == 1
    fallback.assert_not_called()
