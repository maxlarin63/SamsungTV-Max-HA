"""Constants for the Samsung TV Max integration."""

from __future__ import annotations

DOMAIN = "samsungtv_max"
DEFAULT_NAME = "Samsung TV"
INTEGRATION_VERSION = "0.0.39"

# ── Network ───────────────────────────────────────────────────────────────────
TIZEN_WS_PORT = 8002          # WebSocket remote control (wss)
TIZEN_REST_PORT = 8001        # REST API + liveness probe (http)
WS_APP_NAME = "HomeAssistant"  # Identifies HA in the token pairing dialog on TV

# ── Config-entry keys ─────────────────────────────────────────────────────────
CONF_HOST = "host"
CONF_PORT = "port"
CONF_TOKEN = "token"
CONF_MAC = "mac"
CONF_MODEL = "model"          # stored for info; e.g. "QE49Q67RATXXH"
CONF_GENERATION = "generation"  # e.g. "19_" or "unknown"

# ── Timeouts (seconds) — ported from Lua millisecond values ──────────────────
WAKING_POLL_INTERVAL = 1.0    # HTTP poll while waking up
WAKING_GIVE_UP = 30.0         # Give up waking after this many seconds
ON_LIVENESS_INTERVAL = 20.0   # Liveness probe while ON
ON_LIVENESS_TIMEOUT = 2.0     # HTTP timeout for liveness probe
# After FSM goes OFF, first HTTP probe uses INITIAL; later retries use OFF_SLOW_POLL.
OFF_SLOW_POLL_INITIAL_DELAY = 5.0   # First :8001 check (e.g. IR power-on soon after HA said off)
OFF_SLOW_POLL = 10.0              # Interval while TV stays unreachable (was 20s — too slow for IR on)
# Matches HC3 POWER_PROBE_HTTP_MS=500. If wake/off polls flap or never reach ON on slow Wi‑Fi,
# raise this again (we previously used 4.0s for that).
POWER_PROBE_TIMEOUT = 0.5   # HTTP timeout for wake + off discovery polls to :8001
TURNING_OFF_TIMEOUT = 20.0    # Optimistic TURNING_OFF → OFF fallback
UNAUTHORIZED_RETRY = 30.0     # Retry WS connect after UNAUTHORIZED
# Wake loop: if REST answers but WebSocket pairing never completes (TV shows allow prompt),
# log "opening WebSocket" each poll — notify user after this many opens.
PAIRING_STUCK_WS_OPENS = 5
# Media player / remote: keep “on” in the UI briefly through FSM dips during boot/reconnect.
UI_OPTIMISTIC_ON_GRACE_SEC = 4.0
# After KEY_POWER over WS for REST=standby, re-check socket / power before WoL + wake cycle.
STANDBY_KEY_WAKE_SETTLE_SEC = 0.35

# ── WebSocket ─────────────────────────────────────────────────────────────────
TIZEN_KEY_DELAY = 0.12        # Inter-key delay in seconds (120 ms)
TIZEN_KEEPALIVE_INTERVAL = 55.0  # WS keepalive ping interval

# ── WOL ───────────────────────────────────────────────────────────────────────
WOL_BURST_ROUNDS = 5
WOL_BURST_STEP = 0.12         # seconds between WOL packets

# ── TV capability detection ───────────────────────────────────────────────────
# Model prefixes that lack specific capabilities.
# Matches the Lua TV_CAPS_UNSUPPORTED table in appLaunch.lua.
#   meta_tag_nav  — platform supports /api/v2/applications/{id} REST polling
#   has_ghost_api — platform supports ed.installedApp.get via WebSocket
TV_CAPS_UNSUPPORTED: dict[str, list[str]] = {
    "meta_tag_nav": ["15_", "16_", "17_", "18_"],
    "has_ghost_api": ["15_", "16_", "17_"],
}

# ── App discovery patterns (name substring → logical key) ────────────────────
APP_NAME_PATTERNS: list[tuple[str, str]] = [
    ("youtube", "APP_YOUTUBE"),
    ("netflix", "APP_NETFLIX"),
    ("spotify", "APP_SPOTIFY"),
    ("browser", "APP_BROWSER"),
    ("internet", "APP_BROWSER"),
]

# User shortcuts (lowercase) → canonical token for lookup after exact + substring
# fail on the raw query (e.g. many TVs label the browser app "Internet", not "Browser").
APP_NAME_ALIASES: dict[str, str] = {
    "browser": "internet",
}

# Minimum character length for substring matching (user query in app display name).
APP_SUBSTRING_QUERY_MIN_LEN = 2

# Hardcoded fallback IDs used only when the TV returned no app list.
TIZEN_APPS_FALLBACK: dict[str, str] = {
    "APP_YOUTUBE": "111299001912",
    "APP_NETFLIX": "3201907018807",
    "APP_SPOTIFY": "3201606009684",
    "APP_BROWSER": "org.tizen.browser",
}

# App IDs known to be native (app_type 4) — WS launch required even without discovery.
TIZEN_NATIVE_IDS: frozenset[str] = frozenset(["org.tizen.browser"])

# ── Key names (non-exhaustive reference list) ─────────────────────────────────
KEY_POWER = "KEY_POWER"
KEY_VOLUMEUP = "KEY_VOLUMEUP"
KEY_VOLUMEDOWN = "KEY_VOLUMEDOWN"
KEY_MUTE = "KEY_MUTE"
KEY_CHUP = "KEY_CHUP"
KEY_CHDOWN = "KEY_CHDOWN"
KEY_UP = "KEY_UP"
KEY_DOWN = "KEY_DOWN"
KEY_LEFT = "KEY_LEFT"
KEY_RIGHT = "KEY_RIGHT"
KEY_ENTER = "KEY_ENTER"
KEY_RETURN = "KEY_RETURN"
KEY_EXIT = "KEY_EXIT"
KEY_HOME = "KEY_HOME"
KEY_MENU = "KEY_MENU"
KEY_SOURCE = "KEY_SOURCE"
KEY_INFO = "KEY_INFO"
KEY_TOOLS = "KEY_TOOLS"
KEY_PLAY = "KEY_PLAY"
KEY_PAUSE = "KEY_PAUSE"
KEY_STOP = "KEY_STOP"
KEY_FF = "KEY_FF"
KEY_REWIND = "KEY_REWIND"
KEY_NEXT = "KEY_NEXT"
KEY_PREV = "KEY_PREV"
KEY_RED = "KEY_RED"
KEY_GREEN = "KEY_GREEN"
KEY_YELLOW = "KEY_YELLOW"
KEY_BLUE = "KEY_BLUE"

# ── WS event names ────────────────────────────────────────────────────────────
WS_EVENT_CHANNEL_CONNECT = "ms.channel.connect"
WS_EVENT_CHANNEL_UNAUTHORIZED = "ms.channel.unauthorized"
WS_EVENT_CHANNEL_DISCONNECT = "ms.channel.disconnect"
WS_EVENT_ERROR = "ms.error"
WS_EVENT_INSTALLED_APP = "ed.installedApp.get"
WS_METHOD_REMOTE_CONTROL = "ms.remote.control"
WS_METHOD_CHANNEL_EMIT = "ms.channel.emit"

# ── HA event names (fired on the event bus) ───────────────────────────────────
EVENT_KEY_SENT = f"{DOMAIN}_key_sent"
EVENT_APP_LAUNCHED = f"{DOMAIN}_app_launched"
EVENT_APPS_UPDATED = f"{DOMAIN}_apps_updated"
EVENT_PAIRING_REQUIRED = f"{DOMAIN}_pairing_required"

# ── Service names ─────────────────────────────────────────────────────────────
SERVICE_SEND_KEY = "send_key"
SERVICE_LAUNCH_APP = "launch_app"
SERVICE_ENUMERATE_APPS = "enumerate_apps"

# ── Platforms ─────────────────────────────────────────────────────────────────
PLATFORMS = ["media_player", "remote"]
