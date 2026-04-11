# Samsung TV Max — Home Assistant Custom Integration

Controls a Samsung Tizen Smart TV over WebSocket (wss :8002).

Migrated from a FIBARO HC3 Quick App (Lua, v0.4.101).

> **Supported:** Samsung Tizen TVs, 2016+ (model prefix 16_+ or no prefix)
> **Not supported:** Legacy Samsung TVs (pre-2016, TCP protocol)

---

## Features

| Capability | Detail |
|---|---|
| Power on/off | WOL burst (5 packets) + WS connect / `KEY_POWER` |
| Power detection | 5-state FSM: OFF / WAKING_UP / ON / TURNING_OFF / UNAUTHORIZED |
| App enumeration | `ed.installedApp.get` WS message → `source_list` + remote `activity_list` |
| App launch | REST POST (downloaded apps) / WS deep-link (native apps) |
| Key sending | `ms.remote.control` via WS; 120 ms inter-key queue |
| TV generation detection | Model prefix → capability flags (`meta_tag_nav`, `has_ghost_api`) |
| Token rotation | Token from `ms.channel.connect` persisted to config entry immediately |
| Volume / mute | `KEY_VOLUMEUP`, `KEY_VOLUMEDOWN`, `KEY_MUTE` |
| Custom services | `send_key`, `launch_app`, `enumerate_apps` |
| Remote entity | Full `activity_list` + rich `extra_state_attributes` (app catalog, caps, generation) |
| Protocol | Tizen WebSocket only (wss :8002) |

---

## Installation

### HACS (recommended)
1. Add this repo as a custom integration in HACS.
2. Install **Samsung TV Max**.
3. Restart Home Assistant.
4. **Settings → Devices & services → Add integration → Samsung TV Max**.

### Manual
1. Copy `custom_components/samsungtv_max/` to `<config>/custom_components/samsungtv_max/`
2. Restart Home Assistant.
3. **Settings → Devices & services → Add integration → Samsung TV Max**.

---

## Configuration

| Field | Description |
|---|---|
| Host | IP address of the TV (static DHCP lease recommended) |
| Name | Friendly name for the device |

The integration auto-detects the TV model, generation, and MAC address from
`GET /api/v2/`. Token pairing is handled interactively during config flow.

---

## Services

### `samsungtv_max.send_key`
```yaml
service: samsungtv_max.send_key
data:
  key: KEY_VOLUMEUP
  count: 3
```

### `samsungtv_max.launch_app`
```yaml
service: samsungtv_max.launch_app
data:
  app_name: YouTube
```

### `samsungtv_max.enumerate_apps`
```yaml
service: samsungtv_max.enumerate_apps
```
Fires `samsungtv_max_apps_updated` event on the HA event bus when complete.

---

## Remote entity

The `remote.samsungtv_max_*` entity exposes the full app catalog and TV state in
`extra_state_attributes` — designed as the foundation for a future custom remote panel:

```json
{
  "apps": [{"id": "111299001912", "name": "YouTube", "type": 2}],
  "power_state": "on",
  "tv_model": "QE55Q80RATXXH",
  "tv_generation": "modern",
  "capabilities": {"meta_tag_nav": true, "has_ghost_api": true}
}
```

---

## Development

Open `samsungtv-max-ha.code-workspace` in Cursor or VS Code (or open this folder — `.vscode/settings.json` applies the same interpreter and pytest options).

After a cold reboot, the workspace uses `.venv` automatically: **Python: Select Interpreter** should point at `.venv\\Scripts\\python.exe` (Windows) or `.venv/bin/python` (Linux/macOS — change the path in **User** settings if you are not on Windows). New integrated terminals activate that venv.

### Setup

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install pytest pytest-asyncio pytest-homeassistant-custom-component pytest-socket ruff aiohttp wakeonlan voluptuous
```

**Linux / macOS:**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pytest pytest-asyncio pytest-homeassistant-custom-component pytest-socket ruff aiohttp wakeonlan voluptuous
```

### Run tests
```bash
pytest tests/ -v
```

### Lint
```bash
ruff check custom_components/
```

### Deploy to HA

Copy `.env.ha.example` → `.env.ha` and fill in `HA_HOST` (and optionally `HA_USER`,
`HA_HTTP_URL`, `HA_TOKEN`). Then use the workspace task **Deploy to HA** or run directly:

```bash
# Linux / macOS / WSL
bash scripts/deploy-ha-rsync.sh

# Windows
powershell -File scripts/deploy-ha-scp.ps1
```

See `README` sections in [AC-Mitsubishi-HA](https://github.com/maxlarin63/AC-Mitsubishi-HA)
for full SSH key setup instructions — same pattern applies here.

---

## License
MIT
