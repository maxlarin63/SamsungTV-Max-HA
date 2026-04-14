"""Samsung TV Max integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    PLATFORMS,
    SERVICE_ENUMERATE_APPS,
    SERVICE_GENERATE_DASHBOARD,
    SERVICE_HOLD_KEY,
    SERVICE_LAUNCH_APP,
    SERVICE_SEND_KEY,
    SERVICE_SEND_TEXT,
)
from .coordinator import SamsungTVCoordinator
from .dashboard_gen import (
    check_missing_prerequisites,
    generate_script_yaml,
    generate_view_yaml,
)

_LOGGER = logging.getLogger(__name__)

type SamsungTVMaxConfigEntry = ConfigEntry[SamsungTVCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SamsungTVMaxConfigEntry) -> bool:
    """Set up Samsung TV Max from a config entry."""
    coordinator = SamsungTVCoordinator(hass, entry)
    entry.runtime_data = coordinator

    await coordinator.async_setup()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _register_services(hass)
    _check_text_input_prerequisites(hass, entry)
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

    if not hass.services.has_service(DOMAIN, SERVICE_GENERATE_DASHBOARD):

        async def handle_generate_dashboard(call: ServiceCall) -> None:
            entry_id = call.data.get("entry_id")
            for entry in hass.config_entries.async_entries(DOMAIN):
                if entry_id and entry.entry_id != entry_id:
                    continue
                view_yaml = generate_view_yaml(hass, entry)
                script_yaml = generate_script_yaml(entry)
                msg = (
                    f"## Dashboard view for {entry.title}\n\n"
                    f"Paste this into **Dashboard → Raw config editor** "
                    f"under `views:`:\n\n"
                    f"```yaml\n{view_yaml}```\n\n"
                    f"---\n\n"
                    f"## Script\n\n"
                    f"Create at **Settings → Automations → Scripts → "
                    f"Add Script → YAML mode**:\n\n"
                    f"```yaml\n{script_yaml}\n```\n\n"
                    f"---\n\n"
                    f"Also create helper **input_text.tv_text_input** "
                    f"(Settings → Helpers → Text, name: **TV Text Input**) "
                    f"if not already created."
                )
                persistent_notification.async_create(
                    hass,
                    msg,
                    title=f"Samsung TV Max — Dashboard YAML ({entry.title})",
                    notification_id=f"{DOMAIN}_dashboard_{entry.entry_id}",
                )

        hass.services.async_register(
            DOMAIN,
            SERVICE_GENERATE_DASHBOARD,
            handle_generate_dashboard,
            schema=vol.Schema({vol.Optional("entry_id"): str}),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_HOLD_KEY):

        async def handle_hold_key(call: ServiceCall) -> None:
            entry_id = call.data.get("entry_id")
            key = call.data["key"]
            duration = float(call.data.get("duration", 0.5))
            for entry in hass.config_entries.async_entries(DOMAIN):
                if entry_id and entry.entry_id != entry_id:
                    continue
                coordinator: SamsungTVCoordinator = entry.runtime_data
                await coordinator.async_hold_key(key, duration)

        hass.services.async_register(
            DOMAIN,
            SERVICE_HOLD_KEY,
            handle_hold_key,
            schema=vol.Schema(
                {
                    vol.Optional("entry_id"): str,
                    vol.Required("key"): cv.string,
                    vol.Optional("duration", default=0.5): vol.All(
                        vol.Coerce(float), vol.Range(min=0.1, max=5.0)
                    ),
                }
            ),
        )


def _check_text_input_prerequisites(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Create a repair-style notification if helper or script is missing."""
    missing = check_missing_prerequisites(hass, entry)
    notif_id = f"{DOMAIN}_prereq_{entry.entry_id}"
    if not missing:
        persistent_notification.async_dismiss(hass, notif_id)
        return
    items = "\n".join(f"- {m}" for m in missing)
    script_yaml = generate_script_yaml(entry)
    persistent_notification.async_create(
        hass,
        (
            f"The text-input feature for **{entry.title}** needs:\n\n"
            f"{items}\n\n"
            f"### Script YAML\n\n"
            f"```yaml\n{script_yaml}\n```\n\n"
            f"Or run **samsungtv_max.generate_dashboard** to get the full "
            f"dashboard YAML with all entity IDs pre-filled."
        ),
        title=f"Samsung TV Max — Setup: create helper & script ({entry.title})",
        notification_id=notif_id,
    )
