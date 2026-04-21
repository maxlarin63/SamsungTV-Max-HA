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
| Browser touch mode | `ms.remote.touchEnable` → d-pad keys auto-redirect to pointer moves/clicks (HC3 parity) |
| Text input (IME) | `send_text` service types into the focused on-screen field (URL bar, search box) |
| Keyboard active sensor | `binary_sensor` turns on when the TV text field is focused (`ms.remote.imeStart`) |
| TV generation detection | Model prefix → capability flags (`meta_tag_nav`, `has_ghost_api`) |
| Token rotation | Token from `ms.channel.connect` persisted to config entry immediately |
| Volume / mute | `KEY_VOLUMEUP`, `KEY_VOLUMEDOWN`, `KEY_MUTE` |
| Custom services | `send_key`, `launch_app`, `enumerate_apps`, `send_text`, `hold_key` |
| Custom remote card | Bundled Lit card — power, d-pad, volume, transport, apps, text input |
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

### `samsungtv_max.send_text`
```yaml
service: samsungtv_max.send_text
data:
  text: "https://www.google.com"
```
Types text into the focused on-screen input field (browser URL bar, search box).
Works when the TV signals `ms.remote.imeStart` — the `binary_sensor.*_keyboard_active`
entity turns on to indicate a text field is focused.

### `samsungtv_max.hold_key`
```yaml
service: samsungtv_max.hold_key
data:
  key: KEY_VOLUMEUP
  duration: 1.0
```
Simulates a long press: sends Press, waits for the duration (TV auto-repeats), then sends Release.

---

## Entities

| Platform | Entity example | Description |
|---|---|---|
| `remote` | `remote.samsung_*_remote` | Power, key sending, app launch; rich `extra_state_attributes` (apps, caps, `keyboard_active`) |
| `media_player` | `media_player.samsung_*` | Power, volume, source select, transport controls |
| `binary_sensor` | `binary_sensor.samsung_*_keyboard_active` | On when the TV has a text field focused (browser URL bar, search). Drives the text-input row visibility in the card. |

---

## Remote entity

The `remote.samsungtv_max_*` entity exposes the full app catalog and TV state in
`extra_state_attributes` — the custom remote card reads these directly:

```json
{
  "apps": [{"id": "111299001912", "name": "YouTube", "type": 2}],
  "power_state": "on",
  "keyboard_active": false,
  "tv_model": "QE55Q80RATXXH",
  "tv_generation": "modern",
  "capabilities": {"meta_tag_nav": true, "has_ghost_api": true}
}
```

---

## Dashboard — custom remote card

The integration bundles a custom Lovelace card (`custom:samsung-tv-remote-card`)
that provides a complete TV remote: power, d-pad, volume, transport, app
shortcuts, and text input.

### Setup

1. After installing the integration, the card JS is registered automatically.
2. In any Lovelace dashboard, **Add card → Samsung TV Remote**.
3. Set the `entity` to your `remote.*` entity (e.g. `remote.samsung_k45_remote`).
4. Done.

The integration registers the bundled JS with the HA frontend and, in **Lovelace
storage** mode, also adds a **JavaScript module** under **Settings → Dashboards →
Resources** so WebKit (iOS Safari / Chrome) loads the card reliably. If you use
**YAML** resources only, add the same URL manually:

```yaml
resources:
  - url: /samsungtv_max/samsung-tv-remote-card.js
    type: module
```

### Multiple TVs

Add one card per TV, each pointing to its own `remote.*` entity. The card reads
`entry_id` from the remote entity's attributes, so all service calls target the
correct TV automatically.

### Text input

When the TV browser (or any app) focuses a text field, the card shows an inline
text input row. `ms.remote.imeUpdate` pre-fills the field with the current URL.
Type or edit, then press **Send** — the card calls `samsungtv_max.send_text`
directly; no HA helpers or scripts needed.

### Troubleshooting

- **Card blank in a desktop browser but works in the Companion app:** check the
  card's **Visibility** conditions in the dashboard editor. `media_query` rules
  may exclude desktop viewports. Remove or widen those rules.
- **Card shows "Custom element doesn't exist":** restart HA so the frontend
  module registers. Hard-refresh the browser (`Ctrl+F5`).

---

## Upgrading from stock Lovelace dashboard (pre-v0.2.0)

Prior versions provided a stock Lovelace YAML remote panel (via
`samsungtv_max.generate_dashboard`) and required HA helpers and scripts. The
custom card replaces all of that. After upgrading:

### What to remove from HA

1. **Helper `input_text.tv_text_input`** — Settings → Helpers → delete it.
   The custom card has its own built-in text field.
2. **Scripts `script.tv_send_text_*`** (e.g. `script.tv_send_text_samsung_k45`) —
   Settings → Automations → Scripts → delete them.
   The card calls `samsungtv_max.send_text` directly.
3. **Old dashboard view(s)** — edit Dashboard → Raw config editor, remove the
   view(s) that were generated by `samsungtv_max.generate_dashboard`.
4. **Persistent notifications** — dismiss any leftover "Samsung TV Max — Setup"
   or "Samsung TV Max — Dashboard YAML" notifications in Settings → Notifications.

### What was removed from the integration

- `samsungtv_max.generate_dashboard` service — no longer exists.
- `docs/lovelace_remote_view.yaml` — template file removed.
- `docs/lovelace-remote-dashboard.md` — setup guide removed.
- `dashboard_gen.py` — module removed.
- Startup prerequisite check (notification about missing helpers/scripts) — removed.

---

## Development

Open `samsungtv-max-ha.code-workspace` in Cursor or VS Code (or open this folder — `.vscode/settings.json` applies the same interpreter and pytest options).

After a cold reboot, the workspace uses `.venv` automatically: **Python: Select Interpreter** should point at `.venv\\Scripts\\python.exe` (Windows) or `.venv/bin/python` (Linux/macOS — change the path in **User** settings if you are not on Windows). New integrated terminals activate that venv.

### Setup

Use **Python 3.12** — `pytest-homeassistant-custom-component` pulls in
`lru-dict`, which has no prebuilt Windows wheel for 3.13 yet (would fall back
to a C source build that requires MSVC Build Tools). CI also pins 3.12.

**Windows (PowerShell):**
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

**Linux / macOS:**
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

`requirements-dev.txt` mirrors the exact install list used by
`.github/workflows/validate.yml`, so a green local run == a green CI run.

### Frontend (custom card)

```bash
cd custom_components/samsungtv_max/frontend
npm install
npm run build
```

The compiled bundle lands in `frontend/dist/samsung-tv-remote-card.js` and is
committed to the repo so no build step is needed during deployment.

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
