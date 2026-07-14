"""Shared Tier 1 setup helpers for probe and create_session scripts."""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from app.config import Settings, get_settings

RuntimeContext = Literal["docker_worker", "host"]


@dataclass
class PrereqRow:
    name: str
    present: bool
    detail: str


def detect_runtime_context() -> RuntimeContext:
    """Return docker_worker when running inside a container."""
    if Path("/.dockerenv").exists():
        return "docker_worker"
    return "host"


def selenium_hostname(selenium_host: str) -> str:
    """Strip scheme and trailing slashes from MULTILOGIN_SELENIUM_HOST."""
    raw = selenium_host.strip()
    if "://" in raw:
        parsed = urlparse(raw)
        host = parsed.hostname or ""
    else:
        host = raw.split("/")[0]
    return host.rstrip("/")


def resolve_host(host: str) -> tuple[str | None, str | None]:
    """Resolve hostname to IP; return (ip, error_message)."""
    if not host:
        return None, "empty selenium hostname"
    try:
        return socket.gethostbyname(host), None
    except socket.gaierror as exc:
        return None, f"cannot resolve {host!r}: {exc}"


def tcp_probe(host: str, port: int, *, timeout: float = 5.0) -> bool:
    """Return True when a TCP connection to host:port succeeds."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def read_etc_hosts_lines(*patterns: str) -> list[str]:
    """Return /etc/hosts lines matching any pattern (case-insensitive)."""
    hosts_path = Path("/etc/hosts")
    if not hosts_path.is_file():
        return []
    lines: list[str] = []
    lowered = [p.lower() for p in patterns]
    for line in hosts_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if any(p in line.lower() for p in lowered):
            lines.append(line.strip())
    return lines


def detect_wsl_default_gateway() -> str | None:
    """Best-effort WSL default gateway (often the Windows host IP)."""
    route_path = Path("/proc/net/route")
    if not route_path.is_file():
        return None
    for line in route_path.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 3 and parts[1] == "00000000":
            gateway_hex = parts[2]
            try:
                gateway_int = int(gateway_hex, 16)
                return socket.inet_ntoa(gateway_int.to_bytes(4, byteorder="little"))
            except (ValueError, OSError):
                return None
    return None


def suggested_multilogin_host_ip() -> str | None:
    """Return MULTILOGIN_HOST_IP from env or WSL gateway heuristic."""
    env_ip = os.environ.get("MULTILOGIN_HOST_IP", "").strip()
    if env_ip:
        return env_ip
    return detect_wsl_default_gateway()


def audit_prerequisites(settings: Settings | None = None) -> list[PrereqRow]:
    """Audit Tier 1 env vars required for Multilogin connectivity checks."""
    cfg = settings or get_settings()
    rows: list[PrereqRow] = []

    def env(name: str, value: str, env_key: str) -> None:
        ok = bool(value.strip())
        rows.append(PrereqRow(name=name, present=ok, detail=value.strip() or f"{env_key} unset"))

    env("ENABLE_TIER1", str(cfg.enable_tier1).lower(), "ENABLE_TIER1")
    env("BROWSER_MODE", cfg.browser_mode, "BROWSER_MODE")
    env("MULTILOGIN_EMAIL", cfg.multilogin_email, "MULTILOGIN_EMAIL")
    env(
        "MULTILOGIN_PASSWORD",
        "***" if cfg.multilogin_password.get_secret_value().strip() else "",
        "MULTILOGIN_PASSWORD",
    )
    env("MULTILOGIN_FOLDER_ID", cfg.multilogin_folder_id, "MULTILOGIN_FOLDER_ID")
    env("MULTILOGIN_WORKSPACE_ID", cfg.multilogin_workspace_id, "MULTILOGIN_WORKSPACE_ID")
    env("MULTILOGIN_PROFILE_ID", cfg.multilogin_profile_id, "MULTILOGIN_PROFILE_ID")
    env("MULTILOGIN_API_URL", cfg.multilogin_api_url, "MULTILOGIN_API_URL")
    env("MULTILOGIN_LAUNCHER_URL", cfg.multilogin_launcher_url, "MULTILOGIN_LAUNCHER_URL")
    env("MULTILOGIN_SELENIUM_HOST", cfg.multilogin_selenium_host, "MULTILOGIN_SELENIUM_HOST")
    env("LINKEDIN_BOT_EMAIL", cfg.linkedin_bot_email, "LINKEDIN_BOT_EMAIL")
    env(
        "LINKEDIN_BOT_PASSWORD",
        "***" if cfg.linkedin_bot_password.get_secret_value().strip() else "",
        "LINKEDIN_BOT_PASSWORD",
    )

    try:
        import selenium  # noqa: F401

        rows.append(PrereqRow(name="selenium", present=True, detail="package installed"))
    except ImportError:
        rows.append(
            PrereqRow(
                name="selenium",
                present=False,
                detail="pip install selenium (worker image or pip install selenium)",
            )
        )

    return rows


def check_required_prereqs(rows: list[PrereqRow]) -> list[str]:
    """Return missing required keys for create_session check (not full Tier 1 boot)."""
    required = {
        "MULTILOGIN_EMAIL",
        "MULTILOGIN_PASSWORD",
        "MULTILOGIN_FOLDER_ID",
        "MULTILOGIN_SELENIUM_HOST",
        "selenium",
    }
    missing: list[str] = []
    for row in rows:
        if row.name in required and not row.present:
            missing.append(row.name)
    return missing


def print_prereqs(rows: list[PrereqRow]) -> None:
    print("== Tier 1 prerequisites ==")
    for row in rows:
        mark = "OK" if row.present else "MISS"
        print(f"{mark:4}  {row.name}: {row.detail}")
