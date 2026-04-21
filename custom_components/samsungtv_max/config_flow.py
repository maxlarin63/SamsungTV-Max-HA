"""Config flow for Samsung TV Max.

Steps
-----
1. user  — enter IPv4 + name
2. detect — probe REST /api/v2/ on :8001; if the TV is off or has no MAC in the
           API response, the entry is created anyway (model/MAC/token filled at runtime)
3. pair  — only when detection found a MAC: WS on :8002, UNAUTHORIZED form if needed

If the host is wrong (no /api/v2/ JSON), the flow aborts with "unsupported_model".
"""

from __future__ import annotations

import asyncio
import logging

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_GENERATION,
    CONF_HOST,
    CONF_MAC,
    CONF_MODEL,
    CONF_TOKEN,
    DEFAULT_NAME,
    DOMAIN,
    TIZEN_REST_PORT,
    TIZEN_WS_PORT,
)
from .tizen.caps import detect_caps, extract_generation
from .tizen.ws_client import TizenWSClient
from .util_mac import normalize_tv_ipv4_host, normalize_wol_mac

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    }
)


class SamsungTVMaxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Samsung TV Max."""

    VERSION = 1

    def __init__(self) -> None:
        self._host: str = ""
        self._name: str = DEFAULT_NAME
        self._model: str = ""
        self._mac: str = ""
        self._generation: str = ""
        self._token: str = ""

    # ── Step 1: host entry ────────────────────────────────────────────────────

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            raw_host = user_input[CONF_HOST].strip()
            self._name = user_input.get(CONF_NAME, DEFAULT_NAME)

            ipv4 = normalize_tv_ipv4_host(raw_host)
            if not ipv4:
                errors["base"] = "invalid_host"
            else:
                self._host = ipv4
                await self.async_set_unique_id(self._host)
                self._abort_if_unique_id_configured()

                result = await self._async_detect_tv()
                if result == "ok":
                    return await self.async_step_pair()
                if result in ("cannot_connect", "missing_mac"):
                    return self._create_entry_before_pairing()
                errors["base"] = result

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    # ── Step 2: WS pairing ────────────────────────────────────────────────────

    async def async_step_pair(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Attempt WS connect.  If unauthorized, show form prompting user to allow on TV."""
        errors: dict[str, str] = {}

        result = await self._async_attempt_ws_pair()

        if result == "ok":
            return self._create_entry()

        if result == "unauthorized":
            # Show the pairing form — user must accept on the TV, then submit
            return self.async_show_form(
                step_id="pair",
                data_schema=vol.Schema({}),
                errors={"base": "unauthorized"},
                description_placeholders={"host": self._host},
            )

        # Connection failed entirely
        errors["base"] = result
        return self.async_show_form(
            step_id="pair",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={"host": self._host},
        )

    # ── TV detection ──────────────────────────────────────────────────────────

    async def _async_detect_tv(self) -> str:
        """Probe /api/v2/ and populate model/mac/generation.  Returns 'ok' or error key."""
        url = f"http://{self._host}:{TIZEN_REST_PORT}/api/v2/"
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with (
                aiohttp.ClientSession(connector=connector) as session,
                session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp,
            ):
                if resp.status != 200:
                    return "unsupported_model"
                data = await resp.json(content_type=None)
        except aiohttp.ClientConnectionError:
            return "cannot_connect"
        except TimeoutError:
            return "cannot_connect"
        except Exception:  # noqa: BLE001
            return "unknown"

        device = data.get("device", {})
        self._model = device.get("modelName", "")
        self._mac = ""
        for candidate in (
            device.get("wifiMac"),
            device.get("mac"),
            device.get("wiredMac"),
            device.get("ethernetMac"),
        ):
            if not candidate:
                continue
            norm = normalize_wol_mac(str(candidate))
            if norm:
                self._mac = norm
                break
        self._generation = extract_generation(self._model)

        # Detect caps early — if model is legacy (16_ etc) we still continue
        # (we only abort later if it's truly not Tizen at all, i.e. no /api/v2/)
        caps = detect_caps(self._model)
        _LOGGER.debug(
            "Detected model=%s generation=%s caps=%s", self._model, self._generation, caps
        )
        if not self._mac:
            return "missing_mac"
        return "ok"

    # ── WS pairing attempt ────────────────────────────────────────────────────

    async def _async_attempt_ws_pair(self) -> str:
        """Try to open the WS connection and collect the token.

        Returns 'ok', 'unauthorized', 'cannot_connect', or 'unknown'.
        """
        result_event: asyncio.Event = asyncio.Event()
        outcome: list[str] = ["unknown"]

        connector = aiohttp.TCPConnector(ssl=False)
        session = aiohttp.ClientSession(connector=connector)

        async def on_connected() -> None:
            outcome[0] = "ok"
            result_event.set()

        async def on_disconnected(was_unauth: bool) -> None:
            outcome[0] = "unauthorized" if was_unauth else "cannot_connect"
            result_event.set()

        async def on_token(token: str) -> None:
            self._token = token

        ws = TizenWSClient(
            session,
            self._host,
            port=TIZEN_WS_PORT,
            token=self._token,
            on_connected=on_connected,
            on_disconnected=on_disconnected,
            on_token_received=on_token,
        )

        try:
            await ws.async_connect()
            await asyncio.wait_for(result_event.wait(), timeout=15)
        except TimeoutError:
            outcome[0] = "cannot_connect"
        finally:
            await ws.async_close()
            await session.close()

        return outcome[0]

    # ── Entry creation ────────────────────────────────────────────────────────

    def _create_entry(self) -> FlowResult:
        return self.async_create_entry(
            title=self._name,
            data={
                CONF_HOST: self._host,
                CONF_MODEL: self._model,
                CONF_MAC: self._mac,
                CONF_GENERATION: self._generation,
                CONF_TOKEN: self._token,
            },
        )

    def _create_entry_before_pairing(self) -> FlowResult:
        """Finish setup without WS pairing (TV off, no MAC in API, or connect timeout)."""
        return self.async_create_entry(
            title=self._name,
            data={
                CONF_HOST: self._host,
                CONF_MODEL: self._model,
                CONF_MAC: self._mac,
                CONF_GENERATION: self._generation,
                CONF_TOKEN: "",
            },
        )
