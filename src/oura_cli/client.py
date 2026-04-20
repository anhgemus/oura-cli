"""Thin wrapper around the Oura Ring v2 REST API.

Stdlib-only. Auto-paginates `next_token`. Raises OuraError on HTTP failures.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable

API_BASE = "https://api.ouraring.com/v2/usercollection"

KNOWN_ENDPOINTS: tuple[str, ...] = (
    "personal_info",
    "daily_activity", "daily_sleep", "daily_readiness", "daily_stress",
    "daily_resilience", "daily_cardiovascular_age", "daily_spo2",
    "sleep", "sleep_time", "workout", "session",
    "tag", "enhanced_tag", "rest_mode_period",
    "vo2_max", "ring_configuration",
    "heartrate", "interbeat_interval",
)


class OuraError(Exception):
    """Raised on non-2xx responses from the Oura API."""

    def __init__(self, status: int, endpoint: str, body: str = "") -> None:
        self.status = status
        self.endpoint = endpoint
        self.body = body
        super().__init__(f"HTTP {status} on {endpoint}: {body[:400]}")


class OuraClient:
    """Minimal Oura v2 REST client.

    Parameters
    ----------
    token:
        Personal Access Token. Get one at
        https://cloud.ouraring.com/personal-access-tokens
    api_base:
        Override for testing (default: production endpoint).
    timeout:
        Per-request timeout in seconds.
    verbose_fn:
        Optional callable invoked with each request URL (for logging).
    """

    def __init__(
        self,
        token: str,
        *,
        api_base: str = API_BASE,
        timeout: float = 30.0,
        verbose_fn=None,
    ) -> None:
        if not token:
            raise ValueError("token is required")
        self.token = token.strip()
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self._verbose = verbose_fn

    # ── low-level ────────────────────────────────────────────────────────────

    def get(self, endpoint: str, params: dict | None = None, *, max_pages: int = 50) -> dict:
        """GET /v2/usercollection/<endpoint>, auto-paginating `next_token`."""
        base_url = f"{self.api_base}/{endpoint}"
        q = urllib.parse.urlencode(params or {})
        url = f"{base_url}?{q}" if q else base_url

        collected: list[dict] = []
        pages = 0
        while url and pages < max_pages:
            if self._verbose:
                self._verbose(url)
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"Bearer {self.token}")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    resp = json.loads(r.read())
            except urllib.error.HTTPError as e:
                try:
                    body = e.read().decode()
                except Exception:
                    body = ""
                raise OuraError(e.code, endpoint, body) from None

            if "data" in resp and isinstance(resp["data"], list):
                collected.extend(resp["data"])
                nt = resp.get("next_token")
                if nt:
                    sep = "&" if "?" in base_url else "?"
                    tail = f"{q + '&' if q else ''}next_token={urllib.parse.quote(nt)}"
                    url = f"{base_url}{sep}{tail}"
                    pages += 1
                    continue
                return {"data": collected}
            return resp
        return {"data": collected, "truncated": True}

    # ── typed convenience ────────────────────────────────────────────────────

    def dated(self, endpoint: str, start: str, end: str) -> list[dict]:
        """Fetch a dated endpoint and return the flat list."""
        resp = self.get(endpoint, {"start_date": start, "end_date": end})
        return resp.get("data", [])

    def heartrate(self, start_dt: str, end_dt: str) -> list[dict]:
        """Raw heart rate samples. Uses ISO datetimes, not plain dates."""
        resp = self.get("heartrate", {"start_datetime": start_dt, "end_datetime": end_dt})
        return resp.get("data", [])

    def personal_info(self) -> dict:
        return self.get("personal_info")

    def ring_configuration(self) -> dict:
        return self.get("ring_configuration")

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def index_by_day(items: Iterable[dict]) -> dict[str, list[dict]]:
        """Group entries by their `day` / `date` key (falls back to bedtime_start)."""
        out: dict[str, list[dict]] = {}
        for e in items:
            if not isinstance(e, dict):
                continue
            day = (
                e.get("day")
                or e.get("date")
                or (e.get("bedtime_end") or e.get("bedtime_start") or "")[:10]
                or (e.get("timestamp") or "")[:10]
            )
            if day:
                out.setdefault(day, []).append(e)
        return out
