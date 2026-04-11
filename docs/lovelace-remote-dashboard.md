# Samsung TV Max — stock Lovelace remote dashboard

This adds a **masonry** view that mirrors the bundled remote layout: power and menu, volume/channel, D-pad, transport keys, and app shortcuts. Cards are **Grid** + **Button** only; services are **`remote.*`**, **`media_player.*`**, and **`samsungtv_max.launch_app`**.

Source file: [`lovelace_remote_view.yaml`](lovelace_remote_view.yaml).

## 1. Find your entity IDs

1. Open **Settings → Devices & services → Samsung TV Max**.
2. Open your TV **device**.
3. Note:
   - **Remote** → entity id `remote.*`
   - **Media player** → entity id `media_player.*`

Optional (only if you have **more than one** TV with this integration): copy **Config entry ID** from the remote entity’s **Attributes** (`config_entry_id`).

## 2. Wire placeholders (one edit)

Open `lovelace_remote_view.yaml` and replace:

| Placeholder | Replace with |
|-------------|----------------|
| `remote.REPLACE_ME_REMOTE_ENTITY` | Your `remote.*` id |
| `media_player.REPLACE_ME_MEDIA_PLAYER_ENTITY` | Your `media_player.*` id |

YAML **anchors** are already used: the first `remote.*` line defines `&samsungtv_remote`, and the first media row button defines `&samsungtv_player`. You only change the two placeholder strings.

## 3. Add the view to Home Assistant

### Option A — UI-managed dashboard (typical)

1. Open your dashboard, open the top **three-dots** menu, then **Edit dashboard**.
2. Open **three-dots** again and choose **Raw configuration editor**.
3. Under `views:`, paste the **view list entry** from `lovelace_remote_view.yaml`: from the line `- title: Samsung TV Remote` through the end of the file (omit the top comment block if you prefer).
4. **Save**.

### Option B — YAML mode / extra dashboard

If you use [`lovelace` `dashboards`](https://www.home-assistant.io/dashboards/dashboards/) with a dedicated YAML file, merge the same view object into that file’s `views:` list.

## 4. Multiple TVs

By default, **`samsungtv_max.launch_app`** without `entry_id` runs for **every** Samsung TV Max config entry. With more than one TV, add to **each** `launch_app` `data:` block:

```yaml
entry_id: "your_config_entry_id_here"
```

Use the same value you copied from **Attributes → config_entry_id**.

## 5. Behaviour notes

- **ON** calls **`remote.turn_on`** and shows the remote entity state (`show_state: true`). It does not turn off; add a separate control or use the device tile if you want power-off from the same view.
- **Transport row** uses **`media_player.media_*`** services so behaviour matches the integration’s media player features.
- **App row** uses **`app_name`**. From **0.0.36**, resolution tries **exact** full name (case-insensitive), then **substring** of your label in the TV’s app title (first match), then a small **alias** map (e.g. **Browser** → **Internet**). If nothing resolves, use **`app_id`** or run **`samsungtv_max.enumerate_apps`** and match the catalog.

## 6. Optional tweaks

- **Power off**: add a second button with **`remote.turn_off`** (same **`entity_id`**).
- **Long channel/volume press**: Home Assistant’s stock Button card does not repeat on hold; use **`samsungtv_max.send_key`** with **`count`** if you add automations or a different card later.
- **Channel button labels**: The YAML uses plain text **`CH up`** and **`CH dn`**. To match a classic remote, rename in the visual editor to whatever your browser shows reliably (for example paste Unicode **U+25B2** / **U+25BC** from a character map as **CH** + up-triangle and **CH** + down-triangle), or keep **`CH +`** / **`CH -`** if you prefer ASCII only.

