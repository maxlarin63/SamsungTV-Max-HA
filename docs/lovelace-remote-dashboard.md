# Samsung TV Max — stock Lovelace remote dashboard

This adds a **masonry** view that mirrors the bundled remote layout: power and menu, text input (conditional), volume/channel, D-pad, transport keys, and app shortcuts. Cards are **Grid** + **Button** + **Entities** + **Conditional** only; services are **`remote.*`**, **`media_player.*`**, **`samsungtv_max.launch_app`**, and **`samsungtv_max.send_text`**.

Source file: [`lovelace_remote_view.yaml`](lovelace_remote_view.yaml).

## 1. Find your entity IDs

1. Open **Settings → Devices & services → Samsung TV Max**.
2. Open your TV **device**.
3. Note:
   - **Remote** → entity id `remote.*`
   - **Media player** → entity id `media_player.*`
   - **Keyboard Active** → entity id `binary_sensor.*_keyboard_active`

Optional (only if you have **more than one** TV with this integration): copy **Config entry ID** from the remote entity's **Attributes** (`config_entry_id`).

## 2. Prerequisites for text input

The dashboard includes a conditional text-input row that appears when the TV's browser (or any app) focuses a text field. Create these before pasting the YAML:

### Helper — `input_text.tv_text_input`

**Settings → Devices & Services → Helpers → Create Helper → Text**
- Name: **TV Text Input**
- Max length: 255 (default)

### Script — `script.tv_send_text`

**Settings → Automations & Scenes → Scripts → Add Script** → switch to YAML mode:

```yaml
alias: TV Send Text
sequence:
  - service: samsungtv_max.send_text
    data:
      text: "{{ states('input_text.tv_text_input') }}"
  - service: input_text.set_value
    target:
      entity_id: input_text.tv_text_input
    data:
      value: ""
```

The script reads the helper value, sends it to the TV, then clears the field. Jinja templates only work in scripts/automations — not in dashboard button `data:` — which is why this script is needed.

## 3. Wire placeholders (one edit)

Open `lovelace_remote_view.yaml` and replace:

| Placeholder | Replace with |
|-------------|----------------|
| `remote.samsung_k45_remote` | Your `remote.*` id |
| `media_player.samsung_k45` | Your `media_player.*` id |
| `binary_sensor.samsung_k45_keyboard_active` | Your `binary_sensor.*_keyboard_active` id |

YAML **anchors** are already used: the first `remote.*` line defines `&samsungtv_remote`, and the first media row button defines `&samsungtv_player`. The `binary_sensor` and `input_text` entity IDs appear only once each.

## 4. Add the view to Home Assistant

### Option A — UI-managed dashboard (typical)

1. Open your dashboard, open the top **three-dots** menu, then **Edit dashboard**.
2. Open **three-dots** again and choose **Raw configuration editor**.
3. Under `views:`, paste the **view list entry** from `lovelace_remote_view.yaml`: from the line `- title: Samsung TV Remote` through the end of the file (omit the top comment block if you prefer).
4. **Save**.

### Option B — YAML mode / extra dashboard

If you use [`lovelace` `dashboards`](https://www.home-assistant.io/dashboards/dashboards/) with a dedicated YAML file, merge the same view object into that file's `views:` list.

## 5. Multiple TVs

By default, **`samsungtv_max.launch_app`** and **`samsungtv_max.send_text`** without `entry_id` run for **every** Samsung TV Max config entry. With more than one TV, add to **each** service `data:` block:

```yaml
entry_id: "your_config_entry_id_here"
```

Use the same value you copied from **Attributes → config_entry_id**.

## 6. Behaviour notes

- **ON** calls **`remote.turn_on`** and shows the remote entity state (`show_state: true`). It does not turn off; add a separate control or use the device tile if you want power-off from the same view.
- **Text input row** (rows 2–3) appears only when `binary_sensor.*_keyboard_active` is `on` (TV text field focused). When the browser URL bar is selected, `ms.remote.imeUpdate` pre-fills the helper with the current URL.
- **D-pad in browser**: when touch mode is active (`ms.remote.touchEnable`), arrow keys automatically redirect to pointer moves and OK becomes a click — matching HC3 behaviour.
- **Transport row** uses **`media_player.media_*`** services so behaviour matches the integration's media player features.
- **App row** uses **`app_name`**. From **0.0.36**, resolution tries **exact** full name (case-insensitive), then **substring** of your label in the TV's app title (first match), then a small **alias** map (e.g. **Browser** → **Internet**). If nothing resolves, use **`app_id`** or run **`samsungtv_max.enumerate_apps`** and match the catalog.

## 7. Optional tweaks

- **Power off**: add a second button with **`remote.turn_off`** (same **`entity_id`**).
- **Long channel/volume press**: Home Assistant's stock Button card does not repeat on hold; use **`samsungtv_max.send_key`** with **`count`** if you add automations or a different card later.
- **Channel button labels**: The YAML uses plain text **`CH up`** and **`CH dn`**. To match a classic remote, rename in the visual editor to whatever your browser shows reliably (for example paste Unicode **U+25B2** / **U+25BC** from a character map as **CH** + up-triangle and **CH** + down-triangle), or keep **`CH +`** / **`CH -`** if you prefer ASCII only.
