"""App discovery and launch management.

Ported from appLaunch.lua.

App launch strategy (mirrors Lua):
  app_type == 4 (native)  → WS  ed.apps.launch  (DEEP_LINK)
  app_type == 2 (downloaded) → REST POST /api/v2/applications/{appId}

App-type override: any app in TIZEN_NATIVE_IDS is always launched via WS even if
the discovery data says otherwise.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

import aiohttp

from ..const import (
    APP_NAME_ALIASES,
    APP_NAME_PATTERNS,
    APP_SUBSTRING_QUERY_MIN_LEN,
    TIZEN_APPS_FALLBACK,
    TIZEN_NATIVE_IDS,
    TIZEN_REST_PORT,
)
from .caps import TizenCaps

_LOGGER = logging.getLogger(__name__)

WsLaunchFn = Callable[[str], Coroutine[Any, Any, bool]]


class AppManager:
    """Manages app discovery, ID resolution, and launch."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        caps: TizenCaps,
        ws_launch_fn: WsLaunchFn,
    ) -> None:
        self._session = session
        self._host = host
        self._caps = caps
        self._ws_launch = ws_launch_fn

        # Populated by update_apps() from ws_client callback
        self._apps: list[dict] = []
        # Quick-lookup: name (lowercase) → app dict
        self._by_name: dict[str, dict] = {}
        # Quick-lookup: appId → app dict
        self._by_id: dict[str, dict] = {}
        # Logical-key → appId (e.g. "APP_YOUTUBE" → "111299001912")
        self._logical: dict[str, str] = {}

    def set_caps(self, caps: TizenCaps) -> None:
        """Refresh capability flags after /api/v2/ fills model (deferred setup)."""
        self._caps = caps

    # ── App-list management ───────────────────────────────────────────────────

    def update_apps(self, apps: list[dict]) -> None:
        """Replace the app catalog with fresh data from the TV."""
        self._apps = apps
        self._by_name = {a["name"].lower(): a for a in apps}
        self._by_id = {a["appId"]: a for a in apps}
        self._logical = {}

        for app in apps:
            name_lower = app["name"].lower()
            for substring, key in APP_NAME_PATTERNS:
                if substring in name_lower and key not in self._logical:
                    self._logical[key] = app["appId"]

        _LOGGER.debug(
            "AppManager: %d apps indexed, logical keys: %s",
            len(apps),
            list(self._logical),
        )

    @property
    def apps(self) -> list[dict]:
        return list(self._apps)

    @property
    def app_names(self) -> list[str]:
        return [a["name"] for a in self._apps if a.get("is_visible", True)]

    def resolve_app_id(self, name_or_id: str) -> str | None:
        """Return appId for a given display name or appId string.

        Resolution order:

        1. Direct app id if it exists in the catalog.
        2. Case-insensitive **exact** match on the TV's full app name.
        3. **Substring** (first list order): user query (lowercased) appears in the app name.
        4. **Alias** map (e.g. *browser* → *internet*), then repeat exact + substring on the
           canonical token.
        5. Logical keys from pattern scan (e.g. ``APP_NETFLIX``).
        6. ``TIZEN_APPS_FALLBACK`` for bare logical keys when the list was empty.
        """
        if name_or_id in self._by_id:
            return name_or_id

        norm = name_or_id.strip().lower()
        if not norm:
            return TIZEN_APPS_FALLBACK.get(name_or_id)

        app = self._by_name.get(norm)
        if app:
            return app["appId"]

        sid = self._first_substring_match(norm)
        if sid:
            return sid

        canonical = APP_NAME_ALIASES.get(norm)
        if canonical:
            app = self._by_name.get(canonical)
            if app:
                return app["appId"]
            sid = self._first_substring_match(canonical)
            if sid:
                return sid

        if name_or_id in self._logical:
            return self._logical[name_or_id]

        return TIZEN_APPS_FALLBACK.get(name_or_id)

    def _first_substring_match(self, needle: str) -> str | None:
        """First installed app whose display name contains *needle* (case-insensitive)."""
        if len(needle) < APP_SUBSTRING_QUERY_MIN_LEN:
            return None
        for app in self._apps:
            if needle in app["name"].lower():
                return app["appId"]
        return None

    # ── Launch ────────────────────────────────────────────────────────────────

    async def async_launch(self, app_id: str) -> bool:
        """Launch an app by ID using the correct method."""
        app = self._by_id.get(app_id)
        app_type = app.get("app_type", 2) if app else 2

        # Native apps and known native IDs always go via WS
        if app_id in TIZEN_NATIVE_IDS or app_type == 4:
            return await self._ws_launch(app_id)
        return await self._rest_launch(app_id)

    async def async_launch_by_name(self, name: str) -> bool:
        """Resolve *name* to an app ID and launch it."""
        app_id = self.resolve_app_id(name)
        if not app_id:
            _LOGGER.warning("AppManager: cannot resolve '%s' to an app ID", name)
            return False
        return await self.async_launch(app_id)

    async def _rest_launch(self, app_id: str) -> bool:
        """POST /api/v2/applications/{appId} — for downloaded apps (app_type 2)."""
        url = f"http://{self._host}:{TIZEN_REST_PORT}/api/v2/applications/{app_id}"
        _LOGGER.debug("App launch REST: %s", url)
        try:
            async with self._session.post(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                _LOGGER.debug("App launch REST %s status: %s", app_id, resp.status)
                return resp.status in (200, 201)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("App launch REST failed: %s", exc)
            return False

    # ── REST current-app detection ────────────────────────────────────────────

    async def async_get_running_app(self) -> str | None:
        """Poll each known app via REST GET /api/v2/applications/{id}.

        Returns the *name* of the foregrounded app or None.

        Samsung's REST endpoint reports ``running: true`` for every app
        currently loaded in memory, not just the focused one — so relying on
        ``running`` alone makes the first-loaded app appear "sticky" even
        after the user switches to something else.  We therefore:
          1. Prefer ``visible: true`` (foreground on Tizen firmwares that
             expose the field).
          2. Fall back to ``running: true`` only when exactly one app reports
             it — multiple ``running`` entries mean the TV has several apps
             loaded and we cannot disambiguate, so returning ``None`` is
             better than showing a stale name.

        Requires ``caps.meta_tag_nav == True``.  Skips if app list is empty.
        """
        if not self._caps.meta_tag_nav or not self._apps:
            return None

        tasks = [
            self._check_app_running(a["appId"], a["name"])
            for a in self._apps
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        hits = [r for r in results if isinstance(r, dict)]

        visible = [r for r in hits if r.get("visible")]
        if visible:
            return visible[0]["name"]

        running = [r for r in hits if r.get("running")]
        if len(running) == 1:
            return running[0]["name"]
        return None

    async def _check_app_running(self, app_id: str, name: str) -> dict | None:
        url = (
            f"http://{self._host}:{TIZEN_REST_PORT}/api/v2/applications/{app_id}"
        )
        try:
            async with self._session.get(
                url, timeout=aiohttp.ClientTimeout(total=2)
            ) as resp:
                data = await resp.json(content_type=None)
                running = bool(data.get("running"))
                visible = bool(data.get("visible"))
                if running or visible:
                    _LOGGER.debug(
                        "App status %s (%s): running=%s visible=%s",
                        name, app_id, running, visible,
                    )
                    return {"name": name, "running": running, "visible": visible}
        except Exception:  # noqa: BLE001
            pass
        return None
