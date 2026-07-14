"""Create and validate Multilogin + Selenium sessions for Tier 1 setup.

Usage:
  cd backend
  python scripts/create_session.py check
  python scripts/create_session.py diagnose
  python scripts/create_session.py seed-linkedin --profile-id <uuid>

For staged Docker/WSL networking validation, prefer ``check`` over
``probe_tier1.py --connect-test`` (TCP probe before Selenium).

Exit codes:
  0 — success
  1 — missing prereqs / invalid config
  2 — MLX auth or profile lifecycle failed
  3 — Selenium port TCP failed (Docker/WSL networking)
  4 — TCP OK but Selenium Remote/status failed
  5 — LinkedIn session invalid / captcha
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._tier1_setup_common import (  # noqa: E402
    audit_prerequisites,
    check_required_prereqs,
    detect_runtime_context,
    print_prereqs,
    read_etc_hosts_lines,
    resolve_host,
    selenium_hostname,
    suggested_multilogin_host_ip,
    tcp_probe,
)
from app.config import get_settings  # noqa: E402
from app.providers.linkedin.login import (  # noqa: E402
    connect_selenium,
    has_valid_linkedin_session,
    login_linkedin,
)
from app.providers.linkedin.types import LinkedInPhotoError  # noqa: E402
from app.providers.multilogin import MultiloginClient, MultiloginError  # noqa: E402

NETWORK_REMEDIATION = (
    "Selenium port unreachable from this runtime. MLX often binds automation ports "
    "to Windows loopback. On WSL2 + Docker Engine set MULTILOGIN_HOST_IP to the "
    "Windows host IP, recreate the worker (see docker-compose.tier1.yml), and "
    "verify Windows firewall allows inbound on dynamic MLX ports."
)


async def probe_launcher(*, timeout: float) -> tuple[bool, str]:
    """Return (ok, detail) for MLX launcher reachability."""
    try:
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            response = await client.get("https://launcher.mlx.yt:45001/api/v2/")
        return True, f"launcher HTTP {response.status_code}"
    except httpx.HTTPError as exc:
        return False, f"launcher unreachable: {exc}"


async def verify_selenium_http(host: str, port: int, *, timeout: float) -> tuple[bool, str]:
    """Lightweight Selenium /status check."""
    url = f"http://{host}:{port}/status"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
        if response.status_code == 200:
            return True, f"selenium /status HTTP {response.status_code}"
        return False, f"selenium /status HTTP {response.status_code}"
    except httpx.HTTPError as exc:
        return False, f"selenium /status failed: {exc}"


def pick_profile_id(*, profile_id: str | None, profile_ids: list[str]) -> str | None:
    if profile_id:
        return profile_id.strip() or None
    if profile_ids:
        return profile_ids[0]
    return None


async def run_diagnose() -> int:
    settings = get_settings()
    context = detect_runtime_context()
    host = selenium_hostname(settings.multilogin_selenium_host)
    resolved_ip, resolve_error = resolve_host(host)
    suggested_ip = suggested_multilogin_host_ip()

    print("== Tier 1 diagnose ==")
    print(f"runtime_context: {context}")
    print(f"MULTILOGIN_SELENIUM_HOST: {settings.multilogin_selenium_host}")
    print(f"selenium_hostname: {host}")
    if resolved_ip:
        print(f"resolved_ip: {resolved_ip}")
    else:
        print(f"resolved_ip: FAILED ({resolve_error})")

    env_ip = os.environ.get("MULTILOGIN_HOST_IP", "").strip()
    print(f"MULTILOGIN_HOST_IP (env): {env_ip or '(unset)'}")
    if suggested_ip:
        print(f"suggested MULTILOGIN_HOST_IP: {suggested_ip}")
        print(f"  export MULTILOGIN_HOST_IP={suggested_ip}")

    hosts_lines = read_etc_hosts_lines("launcher.mlx.yt", "host.docker.internal")
    if hosts_lines:
        print("/etc/hosts (launcher / host.docker):")
        for line in hosts_lines:
            print(f"  {line}")
    else:
        print("/etc/hosts: no launcher.mlx.yt or host.docker.internal entries")

    print("recreate worker: backend/scripts/_tier1_recreate_worker.sh")
    return 0


async def run_check(
    *,
    profile_id: str | None,
    require_linkedin: bool,
    timeout: float,
) -> int:
    settings = get_settings()
    rows = audit_prerequisites(settings)
    print_prereqs(rows)

    missing = check_required_prereqs(rows)
    if missing:
        print(f"Missing required settings: {', '.join(missing)}")
        return 1

    host = selenium_hostname(settings.multilogin_selenium_host)
    resolved_ip, resolve_error = resolve_host(host)
    context = detect_runtime_context()
    print(f"\n== create_session check (runtime={context}) ==")
    print(f"selenium_hostname: {host}")
    if resolved_ip:
        print(f"resolved_ip: {resolved_ip}")
    else:
        print(f"resolved_ip: FAILED ({resolve_error})")
        return 1

    launcher_ok, launcher_detail = await probe_launcher(timeout=timeout)
    print(f"launcher: {launcher_detail}")
    if not launcher_ok:
        return 2

    mlx = MultiloginClient()
    chosen_profile: str | None = None
    driver: Any | None = None
    token: str | None = None

    try:
        token = await mlx.sign_in(force=True)
        print("MLX sign-in: OK")

        profile_ids = await mlx.list_profiles(token)
        if not profile_ids:
            print("No profiles found in configured folder.")
            return 2
        print(f"Profiles in folder: {len(profile_ids)}")

        chosen_profile = pick_profile_id(profile_id=profile_id, profile_ids=profile_ids)
        if not chosen_profile:
            print("No profile id available.")
            return 2
        print(f"Using profile: {chosen_profile}")

        port = await mlx.start_profile(chosen_profile, token)
        print(f"started_port: {port}")

        if not tcp_probe(host, port, timeout=timeout):
            print(f"tcp_probe: CLOSED ({host}:{port})")
            print(NETWORK_REMEDIATION)
            suggested = suggested_multilogin_host_ip()
            if suggested:
                print(f"Try: export MULTILOGIN_HOST_IP={suggested}")
                print("Then recreate worker with docker-compose.tier1.yml")
            return 3

        print(f"tcp_probe: OPEN ({host}:{port})")

        status_ok, status_detail = await verify_selenium_http(host, port, timeout=timeout)
        print(status_detail)
        if not status_ok:
            return 4

        try:
            driver = await asyncio.to_thread(connect_selenium, port)
            print("selenium: OK")
        except Exception as exc:
            print(f"selenium Remote failed: {exc}")
            return 4

        if require_linkedin:
            session_ok = await asyncio.to_thread(has_valid_linkedin_session, driver)
            if not session_ok:
                print("LinkedIn session: INVALID (not authenticated on feed)")
                print("Run: python scripts/create_session.py seed-linkedin --profile-id", chosen_profile)
                return 5
            print("LinkedIn session: OK")

        print("\ncreate_session check: PASSED")
        return 0
    except MultiloginError as exc:
        print(f"Multilogin error: {exc}")
        return 2
    except Exception as exc:
        print(f"check failed: {exc}")
        return 2
    finally:
        if driver is not None:
            await asyncio.to_thread(driver.quit)
        if chosen_profile is not None:
            try:
                await mlx.stop_profile(chosen_profile, token)
                print(f"Stopped profile: {chosen_profile}")
            except MultiloginError as exc:
                print(f"Warning: stop_profile failed: {exc}")


async def run_seed_linkedin(
    *,
    profile_id: str | None,
    force: bool,
    timeout: float,
) -> int:
    settings = get_settings()
    rows = audit_prerequisites(settings)
    print_prereqs(rows)

    missing = check_required_prereqs(rows)
    bot_missing = not settings.linkedin_bot_email.strip() or not (
        settings.linkedin_bot_password.get_secret_value().strip()
    )
    if bot_missing:
        missing.extend(["LINKEDIN_BOT_EMAIL", "LINKEDIN_BOT_PASSWORD"])
    if missing:
        print(f"Missing required settings: {', '.join(sorted(set(missing)))}")
        return 1

    chosen = (profile_id or settings.multilogin_profile_id).strip()
    if not chosen:
        print("--profile-id required (or set MULTILOGIN_PROFILE_ID)")
        return 1

    host = selenium_hostname(settings.multilogin_selenium_host)
    resolved_ip, resolve_error = resolve_host(host)
    if not resolved_ip:
        print(f"Cannot resolve selenium host: {resolve_error}")
        return 1

    mlx = MultiloginClient()
    driver: Any | None = None
    token: str | None = None

    try:
        token = await mlx.sign_in(force=True)
        print("MLX sign-in: OK")

        port = await mlx.start_profile(chosen, token)
        print(f"started_port: {port}")

        if not tcp_probe(host, port, timeout=timeout):
            print(f"tcp_probe: CLOSED ({host}:{port})")
            print(NETWORK_REMEDIATION)
            return 3

        driver = await asyncio.to_thread(connect_selenium, port)

        if not force:
            session_ok = await asyncio.to_thread(has_valid_linkedin_session, driver)
            if session_ok:
                print("LinkedIn session already valid; skipping login")
                print("seed-linkedin: PASSED")
                return 0

        outcome = await asyncio.to_thread(login_linkedin, driver)
        print(f"login_linkedin outcome: {outcome.value}")

        if outcome == LinkedInPhotoError.SUCCESS:
            print("seed-linkedin: PASSED")
            return 0

        if outcome in {LinkedInPhotoError.CAPTCHA, LinkedInPhotoError.AUTH_REQUIRED}:
            print("Complete LinkedIn challenge manually in Multilogin desktop, then re-run check.")
            return 5

        print(f"LinkedIn login failed: {outcome.value}")
        return 5
    except MultiloginError as exc:
        print(f"Multilogin error: {exc}")
        return 2
    except Exception as exc:
        print(f"seed-linkedin failed: {exc}")
        return 2
    finally:
        if driver is not None:
            await asyncio.to_thread(driver.quit)
        if chosen:
            try:
                await mlx.stop_profile(chosen, token)
                print(f"Stopped profile: {chosen}")
            except MultiloginError as exc:
                print(f"Warning: stop_profile failed: {exc}")


async def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    default_timeout = float(settings.tier1_browser_timeout_seconds)

    parser = argparse.ArgumentParser(description="Create and validate Multilogin sessions for Tier 1")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Staged MLX + Selenium validation gate")
    check_parser.add_argument("--profile-id", default=None, help="Fixed MLX profile UUID")
    check_parser.add_argument(
        "--require-linkedin",
        action="store_true",
        help="Fail when LinkedIn feed session is not authenticated",
    )
    check_parser.add_argument(
        "--timeout",
        type=float,
        default=default_timeout,
        help="TCP/Selenium timeout seconds",
    )

    subparsers.add_parser("diagnose", help="Print runtime, hosts, and MULTILOGIN_HOST_IP guidance")

    seed_parser = subparsers.add_parser("seed-linkedin", help="Log into LinkedIn inside an MLX profile")
    seed_parser.add_argument("--profile-id", default=None, help="MLX profile UUID")
    seed_parser.add_argument(
        "--force",
        action="store_true",
        help="Run login even when session is already valid",
    )
    seed_parser.add_argument(
        "--timeout",
        type=float,
        default=default_timeout,
        help="TCP/Selenium timeout seconds",
    )

    args = parser.parse_args(argv)
    command = args.command or "check"

    if command == "diagnose":
        return await run_diagnose()
    if command == "check":
        return await run_check(
            profile_id=args.profile_id,
            require_linkedin=args.require_linkedin,
            timeout=args.timeout,
        )
    if command == "seed-linkedin":
        return await run_seed_linkedin(
            profile_id=args.profile_id,
            force=args.force,
            timeout=args.timeout,
        )

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
