"""Generate a ready-to-paste Lovelace dashboard YAML for a specific config entry."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

_INPUT_TEXT_ENTITY = "input_text.tv_text_input"

_SCRIPT_YAML = """\
alias: "TV Send Text — {title}"
sequence:
  - service: samsungtv_max.send_text
    data:
      text: "{{{{ states('input_text.tv_text_input') }}}}"
      entry_id: "{entry_id}"
  - service: input_text.set_value
    target:
      entity_id: input_text.tv_text_input
    data:
      value: ""\
"""

_VIEW_YAML = """\
- title: "TV {short}"
  path: tv-{slug}
  icon: mdi:television
  type: masonry
  cards:
    - type: vertical-stack
      cards:
        # ── Power & Menu ──────────────────────────────────────────────────
        - type: grid
          columns: 2
          square: false
          cards:
            - type: button
              entity: {remote}
              name: "ON"
              icon: mdi:power
              show_state: true
              tap_action:
                action: call-service
                service: remote.toggle
                target:
                  entity_id: {remote}
            - type: button
              name: Menu
              icon: mdi:menu
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_MENU

        # ── Text input (visible when TV text field focused) ───────────────
        - type: conditional
          conditions:
            - entity: {kbd_sensor}
              state: "on"
          card:
            type: vertical-stack
            cards:
              - type: entities
                entities:
                  - entity: input_text.tv_text_input
                    name: "Type URL / text"
              - type: grid
                columns: 2
                square: false
                cards:
                  - type: button
                    name: Send
                    icon: mdi:send
                    tap_action:
                      action: call-service
                      service: {script}
                  - type: button
                    name: Clear
                    icon: mdi:close-circle-outline
                    tap_action:
                      action: call-service
                      service: input_text.set_value
                      target:
                        entity_id: input_text.tv_text_input
                      data:
                        value: ""

        # ── Vol+ / Mute / CH+ ─────────────────────────────────────────────
        - type: grid
          columns: 3
          square: false
          cards:
            - type: button
              name: Vol +
              icon: mdi:volume-plus
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_VOLUP
              hold_action:
                action: call-service
                service: samsungtv_max.send_key
                data:
                  key: KEY_VOLUP
                  count: 5
                  entry_id: {entry_id}
            - type: button
              name: Mute
              icon: mdi:volume-off
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_MUTE
            - type: button
              name: CH up
              icon: mdi:arrow-up-bold
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_CHUP
              hold_action:
                action: call-service
                service: samsungtv_max.send_key
                data:
                  key: KEY_CHUP
                  count: 5
                  entry_id: {entry_id}

        # ── Vol− / Source / CH− ───────────────────────────────────────────
        - type: grid
          columns: 3
          square: false
          cards:
            - type: button
              name: Vol −
              icon: mdi:volume-minus
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_VOLDOWN
              hold_action:
                action: call-service
                service: samsungtv_max.send_key
                data:
                  key: KEY_VOLDOWN
                  count: 5
                  entry_id: {entry_id}
            - type: button
              name: Source
              icon: mdi:video-input-hdmi
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_SOURCE
            - type: button
              name: CH dn
              icon: mdi:arrow-down-bold
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_CHDOWN
              hold_action:
                action: call-service
                service: samsungtv_max.send_key
                data:
                  key: KEY_CHDOWN
                  count: 5
                  entry_id: {entry_id}

        # ── Home / Up / Info ──────────────────────────────────────────────
        - type: grid
          columns: 3
          square: false
          cards:
            - type: button
              name: Home
              icon: mdi:home
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_HOME
            - type: button
              icon: mdi:arrow-up
              show_name: false
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_UP
              hold_action:
                action: call-service
                service: samsungtv_max.send_key
                data:
                  key: KEY_UP
                  count: 5
                  entry_id: {entry_id}
            - type: button
              name: Info
              icon: mdi:information
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_INFO

        # ── Left / OK / Right ─────────────────────────────────────────────
        - type: grid
          columns: 3
          square: false
          cards:
            - type: button
              icon: mdi:arrow-left
              show_name: false
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_LEFT
              hold_action:
                action: call-service
                service: samsungtv_max.send_key
                data:
                  key: KEY_LEFT
                  count: 5
                  entry_id: {entry_id}
            - type: button
              name: OK
              icon: mdi:keyboard-return
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_ENTER
            - type: button
              icon: mdi:arrow-right
              show_name: false
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_RIGHT
              hold_action:
                action: call-service
                service: samsungtv_max.send_key
                data:
                  key: KEY_RIGHT
                  count: 5
                  entry_id: {entry_id}

        # ── Back / Down / Exit ────────────────────────────────────────────
        - type: grid
          columns: 3
          square: false
          cards:
            - type: button
              name: Back
              icon: mdi:keyboard-backspace
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_RETURN
            - type: button
              icon: mdi:arrow-down
              show_name: false
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_DOWN
              hold_action:
                action: call-service
                service: samsungtv_max.send_key
                data:
                  key: KEY_DOWN
                  count: 5
                  entry_id: {entry_id}
            - type: button
              name: Exit
              icon: mdi:close
              tap_action:
                action: call-service
                service: remote.send_command
                target:
                  entity_id: {remote}
                data:
                  command: KEY_EXIT

        # ── Transport ─────────────────────────────────────────────────────
        - type: grid
          columns: 5
          square: false
          cards:
            - type: button
              entity: {player}
              name: Play
              icon: mdi:play
              tap_action:
                action: call-service
                service: media_player.media_play
                target:
                  entity_id: {player}
            - type: button
              entity: {player}
              name: Pause
              icon: mdi:pause
              tap_action:
                action: call-service
                service: media_player.media_pause
                target:
                  entity_id: {player}
            - type: button
              entity: {player}
              name: Stop
              icon: mdi:stop
              tap_action:
                action: call-service
                service: media_player.media_stop
                target:
                  entity_id: {player}
            - type: button
              entity: {player}
              name: Prev
              icon: mdi:skip-previous
              tap_action:
                action: call-service
                service: media_player.media_previous_track
                target:
                  entity_id: {player}
            - type: button
              entity: {player}
              name: Next
              icon: mdi:skip-next
              tap_action:
                action: call-service
                service: media_player.media_next_track
                target:
                  entity_id: {player}

        # ── App shortcuts ─────────────────────────────────────────────────
        - type: grid
          columns: 4
          square: false
          cards:
            - type: button
              name: YT
              icon: mdi:youtube
              tap_action:
                action: call-service
                service: samsungtv_max.launch_app
                data:
                  app_name: YouTube
                  entry_id: {entry_id}
            - type: button
              name: Netflix
              icon: mdi:netflix
              tap_action:
                action: call-service
                service: samsungtv_max.launch_app
                data:
                  app_name: Netflix
                  entry_id: {entry_id}
            - type: button
              name: Spotify
              icon: mdi:spotify
              tap_action:
                action: call-service
                service: samsungtv_max.launch_app
                data:
                  app_name: Spotify
                  entry_id: {entry_id}
            - type: button
              name: Web
              icon: mdi:earth
              tap_action:
                action: call-service
                service: samsungtv_max.launch_app
                data:
                  app_name: Browser
                  entry_id: {entry_id}
"""


def _find_entity_id(
    ent_reg: er.EntityRegistry, entry_id: str, domain: str, unique_suffix: str,
) -> str:
    """Find an entity_id by its unique_id pattern, or return a placeholder."""
    unique_id = f"{entry_id}_{unique_suffix}"
    ent = ent_reg.async_get_entity_id(domain, DOMAIN, unique_id)
    return ent or f"{domain}.UNKNOWN_{unique_suffix}"


def _short_name(title: str) -> str:
    """Derive a short label from the entry title (e.g. 'Samsung K45' → 'K45')."""
    parts = title.split()
    if len(parts) >= 2:
        return parts[-1]
    return title


def _slug(title: str) -> str:
    """URL-safe slug from title (e.g. 'Samsung K45' → 'samsung-k45')."""
    return title.lower().replace(" ", "-").replace("_", "-")


def script_entity_id(entry: ConfigEntry) -> str:
    """Per-TV script entity id (e.g. script.tv_send_text_k45)."""
    return f"script.tv_send_text_{_slug(entry.title).replace('-', '_')}"


def generate_view_yaml(hass: HomeAssistant, entry: ConfigEntry) -> str:
    """Return a fully resolved Lovelace view YAML snippet for this TV."""
    ent_reg = er.async_get(hass)
    remote = _find_entity_id(ent_reg, entry.entry_id, "remote", "remote")
    player = _find_entity_id(ent_reg, entry.entry_id, "media_player", "media_player")
    kbd = _find_entity_id(ent_reg, entry.entry_id, "binary_sensor", "keyboard_active")
    return _VIEW_YAML.format(
        short=_short_name(entry.title),
        slug=_slug(entry.title),
        remote=remote,
        player=player,
        kbd_sensor=kbd,
        entry_id=entry.entry_id,
        script=script_entity_id(entry),
    )


def generate_script_yaml(entry: ConfigEntry) -> str:
    """Return the tv_send_text script YAML snippet for this TV."""
    return _SCRIPT_YAML.format(
        title=entry.title,
        entry_id=entry.entry_id,
    )


def check_missing_prerequisites(hass: HomeAssistant, entry: ConfigEntry) -> list[str]:
    """Return list of missing HA objects needed for the text input feature."""
    missing = []
    if not hass.states.get(_INPUT_TEXT_ENTITY):
        missing.append(f"{_INPUT_TEXT_ENTITY} (Helper → Text, name: TV Text Input)")
    sc_id = script_entity_id(entry)
    if not hass.states.get(sc_id):
        missing.append(f"{sc_id} (see notification for YAML)")
    return missing
