"""Tests for create_session.py and _tier1_setup_common.py (no live MLX)."""

from __future__ import annotations

import socket
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest
from pydantic import SecretStr

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.config import Settings
from scripts import create_session
from scripts._tier1_setup_common import (
    PrereqRow,
    audit_prerequisites,
    check_required_prereqs,
    resolve_host,
    selenium_hostname,
    tcp_probe,
)


def _complete_settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "enable_tier1": True,
        "browser_mode": "multilogin",
        "multilogin_email": "bot@example.com",
        "multilogin_password": SecretStr("secret"),
        "multilogin_folder_id": "folder-uuid",
        "multilogin_selenium_host": "http://launcher.mlx.yt",
        "linkedin_bot_email": "li@example.com",
        "linkedin_bot_password": SecretStr("li-secret"),
    }
    base.update(overrides)
    return Settings.model_construct(**base)


def _complete_prereq_rows() -> list[PrereqRow]:
    return audit_prerequisites(_complete_settings())


def test_tcp_probe_open_and_closed() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    try:
        assert tcp_probe("127.0.0.1", port, timeout=1.0) is True
    finally:
        server.close()

    assert tcp_probe("127.0.0.1", port, timeout=0.5) is False


def test_parse_selenium_host() -> None:
    assert selenium_hostname("http://launcher.mlx.yt") == "launcher.mlx.yt"
    assert selenium_hostname("https://host.docker.internal") == "host.docker.internal"
    assert selenium_hostname("http://127.0.0.1:4444") == "127.0.0.1"


def test_resolve_host_failure_message() -> None:
    ip, error = resolve_host("definitely-not-a-real-host.invalid.")
    assert ip is None
    assert error is not None
    assert "cannot resolve" in error


@pytest.mark.asyncio
async def test_check_fails_exit_1_on_missing_prereqs(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _complete_settings(multilogin_email="")
    monkeypatch.setattr(create_session, "get_settings", lambda: settings)

    code = await create_session.run_check(profile_id=None, require_linkedin=False, timeout=5.0)
    assert code == 1


@pytest.mark.asyncio
async def test_check_fails_exit_2_on_sign_in_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.providers.multilogin import MultiloginError

    settings = _complete_settings()
    monkeypatch.setattr(create_session, "get_settings", lambda: settings)
    monkeypatch.setattr(create_session, "resolve_host", lambda _h: ("127.0.0.1", None))
    monkeypatch.setattr(create_session, "probe_launcher", AsyncMock(return_value=(True, "ok")))

    mock_mlx = MagicMock()
    mock_mlx.sign_in = AsyncMock(side_effect=MultiloginError("sign-in failed"))
    monkeypatch.setattr(create_session, "MultiloginClient", lambda: mock_mlx)

    code = await create_session.run_check(profile_id="profile-1", require_linkedin=False, timeout=5.0)
    assert code == 2


@pytest.mark.asyncio
async def test_check_fails_exit_3_on_tcp_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _complete_settings()
    monkeypatch.setattr(create_session, "get_settings", lambda: settings)
    monkeypatch.setattr(create_session, "resolve_host", lambda _h: ("127.0.0.1", None))
    monkeypatch.setattr(create_session, "probe_launcher", AsyncMock(return_value=(True, "ok")))
    monkeypatch.setattr(create_session, "tcp_probe", lambda *_a, **_k: False)

    mock_mlx = MagicMock()
    mock_mlx.sign_in = AsyncMock(return_value="token")
    mock_mlx.list_profiles = AsyncMock(return_value=["profile-1"])
    mock_mlx.start_profile = AsyncMock(return_value=55355)
    mock_mlx.stop_profile = AsyncMock()
    monkeypatch.setattr(create_session, "MultiloginClient", lambda: mock_mlx)

    code = await create_session.run_check(profile_id="profile-1", require_linkedin=False, timeout=5.0)
    assert code == 3
    mock_mlx.stop_profile.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_fails_exit_4_on_selenium_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _complete_settings()
    monkeypatch.setattr(create_session, "get_settings", lambda: settings)
    monkeypatch.setattr(create_session, "resolve_host", lambda _h: ("127.0.0.1", None))
    monkeypatch.setattr(create_session, "probe_launcher", AsyncMock(return_value=(True, "ok")))
    monkeypatch.setattr(create_session, "tcp_probe", lambda *_a, **_k: True)
    monkeypatch.setattr(
        create_session,
        "verify_selenium_http",
        AsyncMock(return_value=(True, "selenium /status HTTP 200")),
    )

    mock_mlx = MagicMock()
    mock_mlx.sign_in = AsyncMock(return_value="token")
    mock_mlx.list_profiles = AsyncMock(return_value=["profile-1"])
    mock_mlx.start_profile = AsyncMock(return_value=55355)
    mock_mlx.stop_profile = AsyncMock()
    monkeypatch.setattr(create_session, "MultiloginClient", lambda: mock_mlx)

    async def fail_to_thread(fn, *args, **kwargs):
        if fn is create_session.connect_selenium:
            raise RuntimeError("selenium down")
        raise AssertionError(f"unexpected to_thread call: {fn}")

    monkeypatch.setattr(create_session.asyncio, "to_thread", fail_to_thread)

    code = await create_session.run_check(profile_id="profile-1", require_linkedin=False, timeout=5.0)
    assert code == 4
    mock_mlx.stop_profile.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_exit_0_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _complete_settings()
    monkeypatch.setattr(create_session, "get_settings", lambda: settings)
    monkeypatch.setattr(create_session, "resolve_host", lambda _h: ("127.0.0.1", None))
    monkeypatch.setattr(create_session, "probe_launcher", AsyncMock(return_value=(True, "ok")))
    monkeypatch.setattr(create_session, "tcp_probe", lambda *_a, **_k: True)
    monkeypatch.setattr(
        create_session,
        "verify_selenium_http",
        AsyncMock(return_value=(True, "selenium /status HTTP 200")),
    )

    mock_mlx = MagicMock()
    mock_mlx.sign_in = AsyncMock(return_value="token")
    mock_mlx.list_profiles = AsyncMock(return_value=["profile-1"])
    mock_mlx.start_profile = AsyncMock(return_value=55355)
    mock_mlx.stop_profile = AsyncMock()
    monkeypatch.setattr(create_session, "MultiloginClient", lambda: mock_mlx)

    mock_driver = MagicMock()

    async def fake_to_thread(fn, *args, **kwargs):
        if fn is create_session.connect_selenium:
            return mock_driver
        return fn(*args, **kwargs)

    monkeypatch.setattr(create_session.asyncio, "to_thread", fake_to_thread)

    code = await create_session.run_check(profile_id="profile-1", require_linkedin=False, timeout=5.0)
    assert code == 0
    mock_mlx.stop_profile.assert_awaited_once_with("profile-1", "token")
    mock_driver.quit.assert_called_once()


@pytest.mark.asyncio
async def test_seed_linkedin_exit_5_on_captcha(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.providers.linkedin.types import LinkedInPhotoError

    settings = _complete_settings()
    monkeypatch.setattr(create_session, "get_settings", lambda: settings)
    monkeypatch.setattr(create_session, "resolve_host", lambda _h: ("127.0.0.1", None))
    monkeypatch.setattr(create_session, "tcp_probe", lambda *_a, **_k: True)

    mock_mlx = MagicMock()
    mock_mlx.sign_in = AsyncMock(return_value="token")
    mock_mlx.start_profile = AsyncMock(return_value=55355)
    mock_mlx.stop_profile = AsyncMock()
    monkeypatch.setattr(create_session, "MultiloginClient", lambda: mock_mlx)

    mock_driver = MagicMock()

    async def fake_to_thread(fn, *args, **kwargs):
        if fn is create_session.connect_selenium:
            return mock_driver
        if fn is create_session.has_valid_linkedin_session:
            return False
        if fn is create_session.login_linkedin:
            return LinkedInPhotoError.CAPTCHA
        if args and callable(args[0]) and getattr(args[0], "__name__", "") == "quit":
            return None
        return fn(*args, **kwargs)

    monkeypatch.setattr(create_session.asyncio, "to_thread", fake_to_thread)

    code = await create_session.run_seed_linkedin(
        profile_id="profile-1",
        force=False,
        timeout=5.0,
    )
    assert code == 5
    mock_mlx.stop_profile.assert_awaited_once()


def test_check_required_prereqs_detects_missing() -> None:
    rows = _complete_prereq_rows()
    rows = [PrereqRow(name="MULTILOGIN_EMAIL", present=False, detail="unset"), *rows[1:]]
    missing = check_required_prereqs(rows)
    assert "MULTILOGIN_EMAIL" in missing


@pytest.mark.asyncio
async def test_diagnose_prints_multilogin_host_ip_hint(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    settings = _complete_settings()
    monkeypatch.setattr(create_session, "get_settings", lambda: settings)
    monkeypatch.setattr(create_session, "detect_runtime_context", lambda: "host")
    monkeypatch.setattr(create_session, "resolve_host", lambda _h: ("172.26.128.1", None))
    monkeypatch.setattr(create_session, "suggested_multilogin_host_ip", lambda: "172.26.128.1")
    monkeypatch.setattr(create_session, "read_etc_hosts_lines", lambda *_a: [])

    code = await create_session.run_diagnose()
    captured = capsys.readouterr().out

    assert code == 0
    assert "export MULTILOGIN_HOST_IP=172.26.128.1" in captured
