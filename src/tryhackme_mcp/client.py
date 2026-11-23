"""Thin async client for the TryHackMe web API (tryhackme.com/api/v2).

These are the same endpoints the tryhackme.com website calls from your browser.
They are not an official, documented public API and can change without notice.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from . import __version__

BASE_URL = "https://tryhackme.com"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    f"(KHTML, like Gecko) Chrome/131.0 Safari/537.36 tryhackme-mcp/{__version__}"
)
PLACEHOLDERS = {"", "your_connect_sid_here", "changeme", "<your-connect-sid>"}


class THMError(Exception):
    """A readable error that is returned to the model instead of a stack trace."""


def _cookies() -> dict[str, str]:
    """Cookies from the environment.

    THM_COOKIE   full Cookie header copied from the browser (takes priority)
    THM_SESSION  value of the connect.sid cookie only
    """
    raw = os.environ.get("THM_COOKIE", "").strip()
    if raw and raw not in PLACEHOLDERS:
        jar = {}
        for part in raw.split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                jar[k.strip()] = v.strip()
        return jar
    sid = os.environ.get("THM_SESSION", "").strip()
    if sid and sid not in PLACEHOLDERS:
        return {"connect.sid": sid}
    return {}


def is_authenticated() -> bool:
    return bool(_cookies())


def writes_enabled() -> bool:
    return os.environ.get("THM_ALLOW_WRITES", "").strip().lower() in {"1", "true", "yes", "on"}


class THMClient:
    def __init__(self, timeout: float = 20.0, transport: httpx.AsyncBaseTransport | None = None):
        jar = httpx.Cookies()
        for k, v in _cookies().items():
            jar.set(k, v, domain="tryhackme.com")
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            cookies=jar,
            timeout=timeout,
            follow_redirects=False,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------ transport

    async def _send(self, method: str, path: str, *, params=None, json=None, headers=None) -> httpx.Response:
        try:
            return await self._client.request(method, path, params=params, json=json, headers=headers)
        except httpx.TimeoutException as e:
            raise THMError(f"TryHackMe did not answer in time ({path}).") from e
        except httpx.HTTPError as e:
            raise THMError(f"Network error talking to TryHackMe: {e}") from e

    @staticmethod
    def _need_auth() -> None:
        if not is_authenticated():
            raise THMError(
                "This tool needs your TryHackMe login. Set THM_SESSION (your connect.sid "
                "cookie) in the MCP server's env block. See README > Authentication."
            )

    @staticmethod
    def _check(r: httpx.Response, path: str, clean: dict | None = None) -> None:
        if r.headers.get("x-vercel-mitigated") or (
            r.status_code in (403, 429) and "text/html" in r.headers.get("content-type", "")
        ):
            raise THMError(
                "TryHackMe's bot protection answered instead of the API. This server does "
                "not try to bypass it; wait a few minutes and retry."
            )
        if r.status_code == 401:
            raise THMError(
                "TryHackMe says you're not logged in (401). Your THM_SESSION cookie is "
                "missing or expired; copy a fresh connect.sid from your browser."
            )
        if r.status_code == 404:
            raise THMError(f"Not found on TryHackMe: {path} {clean or ''}".strip())
        if r.status_code >= 400:
            msg = ""
            try:
                body = r.json()
                msg = body.get("message") or body.get("error") or ""
            except ValueError:
                pass
            raise THMError(f"TryHackMe returned HTTP {r.status_code} for {path}. {msg}".strip())
        if 300 <= r.status_code < 400:
            raise THMError(f"TryHackMe redirected {path} (HTTP {r.status_code}); the endpoint may have moved.")

    @staticmethod
    def _data(r: httpx.Response, path: str) -> Any:
        if not r.content:
            return None
        try:
            body = r.json()
        except ValueError as e:
            raise THMError(f"TryHackMe returned non-JSON for {path}; the endpoint may have changed.") from e
        if isinstance(body, dict) and body.get("status") not in (None, "success"):
            raise THMError(f"TryHackMe error for {path}: {body.get('message') or body.get('status')}")
        return body.get("data") if isinstance(body, dict) and "data" in body else body

    # ------------------------------------------------------------ public API

    async def get(self, path: str, params: dict[str, Any] | None = None, *, auth: bool = False) -> Any:
        """GET an /api/v2 endpoint and return its `data` field."""
        if auth:
            self._need_auth()
        clean = {k: v for k, v in (params or {}).items() if v is not None and v != ""}
        r = await self._send("GET", path, params=clean)
        self._check(r, path, clean)
        return self._data(r, path)

    async def get_html(self, path: str) -> str:
        """GET a normal tryhackme.com page (used where data is only server-rendered)."""
        r = await self._send("GET", path, headers={"Accept": "text/html"})
        self._check(r, path)
        return r.text

    async def post(self, path: str, body: dict[str, Any]) -> Any:
        """POST to an /api/v2 endpoint the way the website does: CSRF token first.

        Only callable when THM_ALLOW_WRITES is on and a login is configured.
        """
        if not writes_enabled():
            raise THMError(
                "Write actions are disabled. Set THM_ALLOW_WRITES=1 in the MCP server's env "
                "block to allow starting machines, voting, and joining rooms."
            )
        self._need_auth()
        r = await self._send("GET", "/api/v2/auth/csrf")
        self._check(r, "/api/v2/auth/csrf")
        token = (self._data(r, "/api/v2/auth/csrf") or {}).get("token")
        if not token:
            raise THMError("Couldn't get a CSRF token from TryHackMe; your session may have expired.")
        r = await self._send("POST", path, json=body, headers={"csrf-token": token})
        self._check(r, path)
        return self._data(r, path)
