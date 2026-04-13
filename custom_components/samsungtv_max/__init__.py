"""Samsung TV Max integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    PLATFORMS,
    SERVICE_ENUMERATE_APPS,
    SERVICE_LAUNCH_APP,
    SERVICE_SEND_KEY,
    SERVICE_SEND_TEXT,
)
from .coordinator import SamsungTVCoordinator

_LOGGER = logging.getLogger(__name__)

type SamsungTVMaxConfigEntry = ConfigEntry[SamsungTVCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SamsungTVMaxConfigEntry) -> bool:
    """Set up Samsung TV Max from a config entry."""
    coordinator = SamsungTVCoordinator(hass, entry)
    entry.runtime_data = coordinator

    await coordinator.async_setup()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SamsungTVMaxConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: SamsungTVCoordinator = entry.runtime_data
    await coordinator.async_shutdown()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


# ── Services ──────────────────────────────────────────────────────────────────

def _register_services(hass: HomeAssistant) -> None:
    """Register custom services (each guarded individually so new services appear on reload)."""

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_KEY):

        async def handle_send_key(call: ServiceCall) -> None:
            entry_id = call.data.get("entry_id")
            key = call.data["key"]
            count = int(call.data.get("count", 1))
            for entry in hass.config_entries.async_entries(DOMAIN):
                if entry_id and entry.entry_id != entry_id:
                    continue
                coordinator: SamsungTVCoordinator = entry.runtime_data
                coordinator.send_key(key, count)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_KEY,
            handle_send_key,
            schema=vol.Schema(
                {
                    vol.Optional("entry_id"): str,
                    vol.Required("key"): cv.string,
                    vol.Optional("count", default=1): vol.All(
                        int, vol.Range(min=1, max=20)
                    ),
                }
            ),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_LAUNCH_APP):

        async def handle_launch_app(call: ServiceCall) -> None:
            entry_id = call.data.get("entry_id")
            app = call.data.get("app_id") or call.data.get("app_name", "")
            for entry in hass.config_entries.async_entries(DOMAIN):
                if entry_id and entry.entry_id != entry_id:
                    continue
                coordinator: SamsungTVCoordinator = entry.runtime_data
                await coordinator.async_launch_app(app)

        hass.services.async_register(
            DOMAIN,
            SERVICE_LAUNCH_APP,
            handle_launch_app,
            schema=vol.Schema(
                {
                    vol.Optional("entry_id"): str,
                    vol.Optional("app_id"): cv.string,
                    vol.Optional("app_name"): cv.string,
                }
            ),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_ENUMERATE_APPS):

        async def handle_enumerate_apps(call: ServiceCall) -> None:
            entry_id = call.data.get("entry_id")
            for entry in hass.config_entries.async_entries(DOMAIN):
                if entry_id and entry.entry_id != entry_id:
                    continue
                coordinator: SamsungTVCoordinator = entry.runtime_data
                await coordinator.async_enumerate_apps()

        hass.services.async_register(
            DOMAIN,
            SERVICE_ENUMERATE_APPS,
            handle_enumerate_apps,
            schema=vol.Schema({vol.Optional("entry_id"): str}),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_TEXT):

        async def handle_send_text(call: ServiceCall) -> None:
            entry_id = call.data.get("entry_id")
            text = call.data["text"]
            for entry in hass.config_entries.async_entries(DOMAIN):
                if entry_id and entry.entry_id != entry_id:
                    continue
                coordinator: SamsungTVCoordinator = entry.runtime_data
                await coordinator.async_send_text(text)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_TEXT,
            handle_send_text,
            schema=vol.Schema(
                {
                    vol.Optional("entry_id"): str,
                    vol.Required("text"): cv.string,
                }
            ),
        )
