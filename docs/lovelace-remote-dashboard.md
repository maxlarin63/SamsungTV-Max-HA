# Samsung TV Max — stock Lovelace remote dashboard

This adds a **masonry** view that mirrors the bundled remote layout: power and menu, text input (conditional), volume/channel, D-pad, transport keys, and app shortcuts. Cards are **Grid** + **Button** + **Entities** + **Conditional** only; services are **`remote.*`**, **`media_player.*`**, **`samsungtv_max.launch_app`**, and **`samsungtv_max.send_text`**.

Source file (template with placeholders): [`lovelace_remote_view.yaml`](lovelace_remote_view.yaml).

## Quick start (recommended)

The **`samsungtv_max.generate_dashboard`** service produces a ready-to-paste YAML with all entity IDs and `entry_id` pre-filled — no manual placeholder replacement needed.

1. Create helper **`input_text.tv_text_input`** (Settings → Helpers → Text, name: **TV Text Input**).
2. In **Developer Tools → Actions**, call **`samsungtv_max.generate_dashboard`** (no parameters needed; or pass `entry_id` for a specific TV).
3. Open **Settings → Notifications**. Two blocks appear:
   - **Script YAML** — create it at Settings → Automations → Scripts → Add Script → YAML mode.
   - **Dashboard view YAML** — paste into Dashboard → Raw config editor under `views:`.
4. Done. The view tab appears as **"TV K45"** (or your TV's short name) with `mdi:television` icon.

If the helper or script is missing at setup time, a notification reminds you with the exact YAML to create.

## Manual setup (alternative)

If you prefer to fill in the placeholders manually instead of using the service:

### 1. Find your entity IDs

1. Open **Settings → Devices & services → Samsung TV Max**.
2. Open your TV **device**.
3. Note:
   - **Remote** → entity id `remote.*`
   - **Media player** → entity id `media_player.*`
   - **Keyboard Active** → entity id `binary_sensor.*_keyboard_active`
   - **Config entry ID** → remote entity → Attributes → `config_entry_id`

### 2. Create prerequisites

**Helper — `input_text.tv_text_input`**

Settings → Devices & Services → Helpers → Create Helper → Text
- Name: **TV Text Input**
- Max length: 255 (default)

**Script — `script.tv_send_text`**

Settings → Automations & Scenes → Scripts → Add Script → switch to YAML mode:

```yaml
alias: TV Send Text
sequence:
  - service: samsungtv_max.send_text
    data:
      text: "{{ states('input_text.tv_text_input') }}"
      entry_id: "YOUR_ENTRY_ID_HERE"
  - service: input_text.set_value
    target:
      entity_id: input_text.tv_text_input
    data:
      value: ""
```

### 3. Replace placeholders

Open `lovelace_remote_view.yaml` and replace:

| Placeholder | Replace with | Example |
|---|---|---|
| `REPLACE_SHORT_NAME` | Short label for the view tab | `K45` |
| `REPLACE_SLUG` | URL slug (lowercase, no spaces) | `k45` |
| `REPLACE_REMOTE` | Your `remote.*` id | `remote.samsung_k45_remote` |
| `REPLACE_PLAYER` | Your `media_player.*` id | `media_player.samsung_k45` |
| `REPLACE_KBD_SENSOR` | Your `binary_sensor.*` id | `binary_sensor.samsung_k45_keyboard_active` |
| `REPLACE_ENTRY_ID` | Your config entry id | `abcdef1234567890` |

### 4. Paste the view

Open Dashboard → Raw config editor → paste under `views:`.

## Multiple TVs

Each TV gets its own view tab (e.g. "TV K39", "TV K45"). The `entry_id` in every `samsungtv_max.*` call ensures commands go to the correct TV only.

- Run `samsungtv_max.generate_dashboard` once — it generates a separate notification for each TV.
- Or fill in `lovelace_remote_view.yaml` twice with different placeholder values.

## Behaviour notes

- **ON** calls **`remote.turn_on`** and shows the remote entity state (`show_state: true`). It does not turn off; add a separate control or use the device tile if you want power-off from the same view.
- **Text input row** appears only when `binary_sensor.*_keyboard_active` is `on` (TV text field focused). When the browser URL bar is selected, `ms.remote.imeUpdate` pre-fills the helper with the current URL.
- **D-pad in browser**: when touch mode is active (`ms.remote.touchEnable`), arrow keys automatically redirect to pointer moves and OK becomes a click — matching HC3 behaviour.
- **Transport row** uses **`media_player.media_*`** services so behaviour matches the integration's media player features.
- **App row** uses **`app_name`**. Resolution tries **exact** full name (case-insensitive), then **substring**, then **alias** map (e.g. **Browser** → **Internet**). If nothing resolves, use **`app_id`** or run **`samsungtv_max.enumerate_apps`** and match the catalog.

## Optional tweaks

- **Power off**: add a second button with **`remote.turn_off`** (same **`entity_id`**).
- **Long channel/volume press**: Home Assistant's stock Button card does not repeat on hold; use **`samsungtv_max.send_key`** with **`count`** if you add automations or a different card later.
