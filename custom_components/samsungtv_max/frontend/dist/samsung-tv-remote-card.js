/**
 * Samsung TV Remote Card — Vanilla Web Component (zero external dependencies).
 *
 * Designed to load near-instantly from cache so the custom element is defined
 * before Lovelace creates the card, eliminating the "Configuration error"
 * timing race on page refresh.
 */
const TAG = "samsung-tv-remote-card";
const _t0 = performance.now();
console.log(`[${TAG}] module eval @${_t0.toFixed(0)}ms`);
const _w = window;
_w.customCards = _w.customCards || [];
if (!_w.customCards.some((c) => c.type === TAG)) {
    _w.customCards.push({
        type: TAG,
        name: "Samsung TV Remote",
        description: "Full remote control for Samsung Tizen TVs (Samsung TV Max)",
    });
}
const ROW_POWER = [
    { key: "_POWER", icon: "mdi:power", label: "ON" },
    { key: "_APPS", icon: "mdi:apps", label: "Apps" },
    { key: "KEY_MENU", icon: "mdi:menu", label: "Menu" },
];
const VOL_CH_UP = [
    { key: "KEY_VOLUP", icon: "mdi:volume-plus", label: "Vol +", hold: true },
    { key: "KEY_MUTE", icon: "mdi:volume-off", label: "Mute" },
    { key: "KEY_CHUP", icon: "mdi:arrow-up-bold", label: "CH up", hold: true },
];
const VOL_CH_DN = [
    { key: "KEY_VOLDOWN", icon: "mdi:volume-minus", label: "Vol \u2212", hold: true },
    { key: "KEY_SOURCE", icon: "mdi:video-input-hdmi", label: "Source" },
    { key: "KEY_CHDOWN", icon: "mdi:arrow-down-bold", label: "CH dn", hold: true },
];
const DPAD_TOP = [
    { key: "KEY_HOME", icon: "mdi:home", label: "Home" },
    { key: "KEY_UP", icon: "mdi:arrow-up", hold: true },
    { key: "KEY_INFO", icon: "mdi:information", label: "Info" },
];
const DPAD_MID = [
    { key: "KEY_LEFT", icon: "mdi:arrow-left", hold: true },
    { key: "KEY_ENTER", icon: "mdi:keyboard-return", label: "OK" },
    { key: "KEY_RIGHT", icon: "mdi:arrow-right", hold: true },
];
const DPAD_BOT = [
    { key: "KEY_RETURN", icon: "mdi:keyboard-backspace", label: "Back" },
    { key: "KEY_DOWN", icon: "mdi:arrow-down", hold: true },
    { key: "KEY_EXIT", icon: "mdi:close", label: "Exit" },
];
const TRANSPORTS = [
    { service: "media_play", icon: "mdi:play" },
    { service: "media_pause", icon: "mdi:pause" },
    { service: "media_stop", icon: "mdi:stop" },
    { service: "media_previous_track", icon: "mdi:skip-previous" },
    { service: "media_next_track", icon: "mdi:skip-next" },
];
const APPS = [
    { name: "YouTube", icon: "mdi:youtube", label: "YT" },
    { name: "Netflix", icon: "mdi:netflix", label: "Netflix" },
    { name: "Spotify", icon: "mdi:spotify", label: "Spotify" },
    { name: "Browser", icon: "mdi:earth", label: "Web" },
];
/* Fallback MDI icons for the full app-picker modal when the TV never delivers
   (or fails to deliver) a PNG for a given app.  Matched case-insensitively
   against the display name; first substring hit wins. */
const APP_ICON_MDI_FALLBACKS = [
    ["youtube", "mdi:youtube"],
    ["netflix", "mdi:netflix"],
    ["spotify", "mdi:spotify"],
    ["prime video", "mdi:amazon"],
    ["amazon", "mdi:amazon"],
    ["disney", "mdi:star-four-points"],
    ["apple tv", "mdi:apple"],
    ["plex", "mdi:plex"],
    ["internet", "mdi:earth"],
    ["browser", "mdi:earth"],
    ["web", "mdi:earth"],
    ["tunein", "mdi:radio"],
    ["music", "mdi:music"],
    ["game", "mdi:gamepad-variant"],
    ["news", "mdi:newspaper"],
];
function mdiForAppName(name) {
    const lower = name.toLowerCase();
    for (const [needle, icon] of APP_ICON_MDI_FALLBACKS) {
        if (lower.includes(needle))
            return icon;
    }
    return "mdi:application";
}
/* ── CSS ─────────────────────────────────────────────────────────────── */
const CARD_CSS = /* css */ `
:host {
  --btn-bg: var(--card-background-color, #1c1c1c);
  --btn-fg: var(--primary-text-color, #e0e0e0);
  --btn-active: var(--primary-color, #03a9f4);
  --btn-radius: 12px;
  --gap: 6px;
}
ha-card { padding: 12px; overflow: hidden; }

button {
  display: flex; align-items: center; justify-content: center;
  background: var(--btn-bg); color: var(--btn-fg);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: var(--btn-radius);
  cursor: pointer; font-size: 16px; padding: 12px 0; min-height: 48px;
  touch-action: manipulation; user-select: none;
  -webkit-tap-highlight-color: transparent;
  transition: transform .1s ease, background .1s ease, border-color .1s ease;
}
button:active {
  transform: scale(0.92);
  background: rgba(255,255,255,.06);
  border-color: rgba(255,255,255,.18);
}
button ha-icon { --mdc-icon-size: 24px; }
button.power-on { color: var(--btn-active); border-color: var(--btn-active); }
button.power-on:active {
  background: color-mix(in srgb, var(--btn-active) 15%, transparent);
  border-color: var(--btn-active);
}

.row-2 { display:grid; grid-template-columns:repeat(2,1fr); gap:var(--gap); margin-bottom:var(--gap); }
.row-3 { display:grid; grid-template-columns:repeat(3,1fr); gap:var(--gap); margin-bottom:var(--gap); }
.row-4 { display:grid; grid-template-columns:repeat(4,1fr); gap:var(--gap); margin-bottom:var(--gap); }
.row-5 { display:grid; grid-template-columns:repeat(5,1fr); gap:var(--gap); margin-bottom:var(--gap); }

.text-row {
  display: flex; gap: var(--gap); margin-bottom: var(--gap);
  animation: slideIn .2s ease-out;
}
@keyframes slideIn {
  from { opacity:0; max-height:0; }
  to   { opacity:1; max-height:60px; }
}
.text-row input {
  flex:1; min-width:0;
  background: var(--btn-bg); color: var(--btn-fg);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: var(--btn-radius);
  padding: 8px 12px; font-size: 14px; outline: none;
}
.text-row input:focus { border-color: var(--btn-active); }
.text-row button { flex-shrink:0; padding:8px 14px; min-height:0; }

.status {
  text-align:center; font-size:11px;
  color: var(--secondary-text-color, #888);
  padding: 2px 0 6px;
}

/* ── App picker modal ───────────────────────────────────────────────── */
.apps-modal {
  position: fixed; inset: 0; z-index: 9999;
  display: flex; align-items: center; justify-content: center;
}
.apps-modal[hidden] { display: none; }
.apps-backdrop {
  position: absolute; inset: 0; background: rgba(0,0,0,.65);
  -webkit-backdrop-filter: blur(4px); backdrop-filter: blur(4px);
  animation: fadeIn .15s ease-out;
}
.apps-panel {
  position: relative; width: min(92vw, 380px); max-height: 82vh;
  background: var(--card-background-color, #1c1c1c);
  color: var(--primary-text-color, #e0e0e0);
  border-radius: 16px; padding: 14px;
  box-shadow: 0 12px 40px rgba(0,0,0,.55);
  display: flex; flex-direction: column;
  animation: popIn .18s ease-out;
}
@keyframes fadeIn { from { opacity:0 } to { opacity:1 } }
@keyframes popIn {
  from { opacity:0; transform: translateY(8px) scale(.97); }
  to   { opacity:1; transform: none; }
}
.apps-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 2px 10px; font-size: 15px; font-weight: 500;
}
.apps-head button {
  width: 34px; min-height: 34px; padding: 0;
  background: transparent; border-color: transparent;
}
.apps-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;
  overflow-y: auto; padding: 2px;
}
.apps-tile {
  display: flex; flex-direction: column; align-items: center;
  justify-content: flex-start; gap: 4px;
  padding: 10px 6px 8px;
  border-radius: 12px;
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.06);
  cursor: pointer;
  min-height: 0;
  transition: transform .1s ease, background .1s ease, border-color .1s ease;
}
.apps-tile:active { transform: scale(.94); background: rgba(255,255,255,.1); }
.apps-tile.active {
  border-color: var(--btn-active);
  background: color-mix(in srgb, var(--btn-active) 18%, transparent);
}
.apps-tile .tile-icon {
  width: 56px; height: 56px; display: flex; align-items: center; justify-content: center;
  border-radius: 10px; background: #fff; overflow: hidden;
}
.apps-tile .tile-icon img { width: 100%; height: 100%; object-fit: contain; }
.apps-tile .tile-icon ha-icon { --mdc-icon-size: 40px; color: #333; }
.apps-tile .tile-name {
  font-size: 11px; line-height: 1.2; text-align: center;
  width: 100%;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
}
.apps-empty {
  text-align: center; color: var(--secondary-text-color, #888);
  padding: 20px 8px; font-size: 13px;
}
`;
function haptic(type = "light") {
    window.dispatchEvent(new CustomEvent("haptic", { detail: type }));
}
/* ── Hold-repeat helper ──────────────────────────────────────────────── */
const HOLD_INTERVAL_MS = 150;
function bindHoldRepeat(el, cb) {
    let timer;
    const stop = () => {
        if (timer !== undefined) {
            clearInterval(timer);
            timer = undefined;
        }
    };
    const down = (ev) => {
        if (ev.button !== 0)
            return;
        ev.preventDefault();
        stop();
        haptic("medium");
        cb();
        timer = setInterval(() => {
            haptic("selection");
            cb();
        }, HOLD_INTERVAL_MS);
    };
    el.addEventListener("pointerdown", down);
    el.addEventListener("pointerup", stop);
    el.addEventListener("pointerleave", stop);
    el.addEventListener("pointercancel", stop);
    return () => {
        el.removeEventListener("pointerdown", down);
        el.removeEventListener("pointerup", stop);
        el.removeEventListener("pointerleave", stop);
        el.removeEventListener("pointercancel", stop);
        stop();
    };
}
/* ── Card class ──────────────────────────────────────────────────────── */
class SamsungTvRemoteCard extends HTMLElement {
    constructor() {
        super();
        /* Keeps the element in Lovelace's DOM tree even when the view tab is hidden. */
        this.connectedWhileHidden = true;
        this._config = null;
        this._hass = null;
        this._prevEntityState = null;
        this._textValue = "";
        this._holdCleanups = [];
        this._domReady = false;
        /* Cached DOM refs (set once in _createDom) */
        this._powerBtn = null;
        this._textRow = null;
        this._textInput = null;
        this._transportRow = null;
        this._statusLine = null;
        this._appsModal = null;
        this._appsGrid = null;
        this._appsModalOpen = false;
        this.attachShadow({ mode: "open" });
    }
    /* ── HA lifecycle ─────────────────────────────────────────────────── */
    set hass(value) {
        this._hass = value;
        if (!this._config?.entity)
            return;
        const newState = value?.states?.[this._config.entity] ?? null;
        if (newState !== this._prevEntityState) {
            this._prevEntityState = newState;
            this._refresh();
        }
    }
    get hass() {
        return this._hass;
    }
    setConfig(config) {
        console.log(`[${TAG}] setConfig entity=${config?.entity}`);
        this._config = config ? { ...config } : null;
        this._domReady = false;
        this._prevEntityState = null;
        this._refresh();
    }
    getCardSize() {
        return 8;
    }
    connectedCallback() {
        this._refresh();
    }
    disconnectedCallback() {
        this._holdCleanups.forEach((fn) => fn());
        this._holdCleanups = [];
    }
    /* ── Render orchestration ─────────────────────────────────────────── */
    _refresh() {
        const sr = this.shadowRoot;
        if (!sr || !this._config || !this._hass)
            return;
        if (!this._config.entity) {
            this._showMessage("Set \u201centity\u201d to a remote.* entity in card config");
            return;
        }
        const stateObj = this._hass.states[this._config.entity];
        if (!stateObj) {
            this._showMessage(`Entity not found: ${this._config.entity}`);
            return;
        }
        if (!this._domReady) {
            this._createDom();
        }
        this._updateDom(stateObj);
    }
    _showMessage(msg) {
        this.shadowRoot.innerHTML =
            `<style>${CARD_CSS}</style><ha-card><div class="status">${msg}</div></ha-card>`;
        this._domReady = false;
    }
    /* ── One-time DOM creation ────────────────────────────────────────── */
    _createDom() {
        this._holdCleanups.forEach((fn) => fn());
        this._holdCleanups = [];
        const sr = this.shadowRoot;
        sr.innerHTML = `<style>${CARD_CSS}</style><ha-card>
${_rowHtml(ROW_POWER, "row-3")}
<div class="text-row" id="text-row" style="display:none">
  <input type="text" placeholder="Type URL / text\u2026" />
  <button class="send-btn"><ha-icon icon="mdi:send"></ha-icon></button>
  <button class="clear-btn"><ha-icon icon="mdi:close-circle-outline"></ha-icon></button>
</div>
${_rowHtml(VOL_CH_UP, "row-3")}
${_rowHtml(VOL_CH_DN, "row-3")}
${_rowHtml(DPAD_TOP, "row-3")}
${_rowHtml(DPAD_MID, "row-3")}
${_rowHtml(DPAD_BOT, "row-3")}
<div class="row-5" id="transport-row">${TRANSPORTS.map((t) => `<button data-transport="${t.service}"><ha-icon icon="${t.icon}"></ha-icon></button>`).join("")}</div>
<div class="row-4">${APPS.map((a) => `<button data-app="${a.name}"><ha-icon icon="${a.icon}"></ha-icon>&nbsp;${a.label}</button>`).join("")}</div>
<div class="status" id="status-line"></div>
<div class="apps-modal" id="apps-modal" hidden>
  <div class="apps-backdrop" id="apps-backdrop"></div>
  <div class="apps-panel" role="dialog" aria-label="Apps">
    <div class="apps-head">
      <span>Apps</span>
      <button class="apps-close" aria-label="Close"><ha-icon icon="mdi:close"></ha-icon></button>
    </div>
    <div class="apps-grid" id="apps-grid"></div>
  </div>
</div>
</ha-card>`;
        this._powerBtn = sr.querySelector('button[data-key="_POWER"]');
        this._textRow = sr.getElementById("text-row");
        this._textInput = sr.querySelector("#text-row input");
        this._transportRow = sr.getElementById("transport-row");
        this._statusLine = sr.getElementById("status-line");
        this._appsModal = sr.getElementById("apps-modal");
        this._appsGrid = sr.getElementById("apps-grid");
        this._bindEvents(sr);
        this._domReady = true;
    }
    /* ── Selective DOM updates (no innerHTML, preserves focus) ─────────── */
    _updateDom(stateObj) {
        const attrs = stateObj.attributes;
        const isOn = stateObj.state === "on";
        if (this._powerBtn) {
            this._powerBtn.className = isOn ? "power-on" : "";
        }
        if (this._textRow) {
            this._textRow.style.display = attrs.keyboard_active ? "" : "none";
        }
        if (this._transportRow) {
            const mp = this._findMediaPlayer(attrs);
            this._transportRow.style.display = mp ? "" : "none";
            this._transportRow.dataset.mpEntity = mp || "";
        }
        if (this._statusLine) {
            const model = attrs.tv_model || "Samsung TV";
            const power = attrs.power_state ?? "unknown";
            // `current_activity` is RemoteEntity's standard attribute for the
            // running app name; hidden when unknown or TV is not on.
            const activity = attrs.current_activity || "";
            const parts = [model, power];
            if (activity && power === "on")
                parts.push(activity);
            this._statusLine.textContent = parts.join(" \u00b7 ");
        }
        if (this._appsModalOpen) {
            this._renderAppsGrid();
        }
    }
    /* ── Event binding (runs once after _createDom) ───────────────────── */
    _bindEvents(sr) {
        const card = sr.querySelector("ha-card");
        card.addEventListener("click", (e) => {
            const btn = e.target.closest("button");
            if (!btn)
                return;
            if (btn.dataset.hold)
                return;
            if (btn.classList.contains("apps-close")) {
                haptic("light");
                this._closeAppsModal();
                return;
            }
            if (btn.dataset.tileAppId !== undefined) {
                haptic("selection");
                this._launchAppById(btn.dataset.tileAppId, btn.dataset.tileAppName || "");
                this._closeAppsModal();
                return;
            }
            haptic("light");
            if (btn.dataset.key === "_APPS") {
                this._openAppsModal();
            }
            else if (btn.dataset.key) {
                this._handleKeyTap(btn.dataset.key);
            }
            else if (btn.dataset.transport) {
                const mp = this._transportRow?.dataset.mpEntity;
                if (mp)
                    this._callMediaPlayer(btn.dataset.transport, mp);
            }
            else if (btn.dataset.app) {
                this._launchApp(btn.dataset.app);
            }
            else if (btn.classList.contains("send-btn")) {
                this._sendText();
            }
            else if (btn.classList.contains("clear-btn")) {
                this._textValue = "";
                if (this._textInput)
                    this._textInput.value = "";
            }
        });
        const backdrop = sr.getElementById("apps-backdrop");
        if (backdrop) {
            backdrop.addEventListener("click", () => this._closeAppsModal());
        }
        sr.querySelectorAll("button[data-hold]").forEach((btn) => {
            const key = btn.dataset.key;
            this._holdCleanups.push(bindHoldRepeat(btn, () => this._sendKey(key)));
        });
        if (this._textInput) {
            this._textInput.addEventListener("input", () => {
                this._textValue = this._textInput.value;
            });
            this._textInput.addEventListener("keydown", (e) => {
                if (e.key === "Enter")
                    this._sendText();
            });
        }
    }
    /* ── Actions ──────────────────────────────────────────────────────── */
    _handleKeyTap(key) {
        if (!this._hass || !this._config)
            return;
        if (key === "_POWER") {
            this._hass.callService("remote", "toggle", undefined, {
                entity_id: this._config.entity,
            });
            return;
        }
        this._hass.callService("remote", "send_command", { command: key }, {
            entity_id: this._config.entity,
        });
    }
    _sendKey(key) {
        if (!this._hass)
            return;
        this._hass.callService("samsungtv_max", "send_key", {
            key,
            entry_id: this._getEntryId(),
        });
    }
    _sendText() {
        if (!this._textValue || !this._hass)
            return;
        this._hass.callService("samsungtv_max", "send_text", {
            text: this._textValue,
            entry_id: this._getEntryId(),
        });
        this._textValue = "";
        if (this._textInput)
            this._textInput.value = "";
    }
    _launchApp(name) {
        if (!this._hass || !this._config)
            return;
        const attrs = this._hass.states[this._config.entity]?.attributes;
        this._hass.callService("samsungtv_max", "launch_app", {
            app_name: name,
            entry_id: attrs?.config_entry_id || "",
        });
    }
    _launchAppById(appId, fallbackName) {
        if (!this._hass)
            return;
        const entryId = this._getEntryId();
        if (appId) {
            this._hass.callService("samsungtv_max", "launch_app", {
                app_id: appId,
                entry_id: entryId,
            });
        }
        else if (fallbackName) {
            this._hass.callService("samsungtv_max", "launch_app", {
                app_name: fallbackName,
                entry_id: entryId,
            });
        }
    }
    /* ── Apps modal ───────────────────────────────────────────────────── */
    _openAppsModal() {
        if (!this._appsModal)
            return;
        this._appsModalOpen = true;
        this._renderAppsGrid();
        this._appsModal.hidden = false;
    }
    _closeAppsModal() {
        if (!this._appsModal)
            return;
        this._appsModalOpen = false;
        this._appsModal.hidden = true;
    }
    _currentAppsList() {
        if (!this._hass || !this._config)
            return [];
        const st = this._hass.states[this._config.entity];
        const raw = st?.attributes?.apps ?? [];
        if (!Array.isArray(raw))
            return [];
        return raw.filter((a) => !!a && typeof a === "object");
    }
    _currentSource() {
        if (!this._hass || !this._config)
            return "";
        const mp = this._findMediaPlayer(this._hass.states[this._config.entity]?.attributes ?? {});
        if (!mp)
            return "";
        const src = this._hass.states[mp]?.attributes?.source;
        return typeof src === "string" ? src : "";
    }
    _renderAppsGrid() {
        const grid = this._appsGrid;
        if (!grid)
            return;
        const apps = this._currentAppsList();
        if (!apps.length) {
            grid.innerHTML =
                `<div class="apps-empty">No apps yet \u2014 wait a few seconds or `
                    + `run <code>samsungtv_max.enumerate_apps</code>.</div>`;
            return;
        }
        const currentName = this._currentSource().toLowerCase();
        const sorted = [...apps].sort((a, b) => (a.name || "").localeCompare(b.name || "", undefined, { sensitivity: "base" }));
        grid.innerHTML = sorted.map((a) => {
            const name = _escapeHtml(a.name || a.id || "");
            const iconUrl = a.icon_url || "";
            const active = currentName && name.toLowerCase() === currentName ? " active" : "";
            const iconInner = iconUrl
                ? `<img src="${_escapeHtml(iconUrl)}" loading="lazy" alt="">`
                : `<ha-icon icon="${mdiForAppName(a.name || "")}"></ha-icon>`;
            return `<button class="apps-tile${active}"`
                + ` data-tile-app-id="${_escapeHtml(a.id || "")}"`
                + ` data-tile-app-name="${name}">`
                + `<span class="tile-icon">${iconInner}</span>`
                + `<span class="tile-name">${name}</span>`
                + `</button>`;
        }).join("");
    }
    _callMediaPlayer(service, entityId) {
        if (!this._hass)
            return;
        this._hass.callService("media_player", service, undefined, {
            entity_id: entityId,
        });
    }
    /* ── Helpers ──────────────────────────────────────────────────────── */
    _getEntryId() {
        if (!this._hass || !this._config)
            return "";
        const ent = this._hass.states[this._config.entity];
        return ent?.attributes?.config_entry_id ?? "";
    }
    _findMediaPlayer(attrs) {
        if (!this._hass || !this._config)
            return undefined;
        const entryId = attrs.config_entry_id;
        for (const eid of Object.keys(this._hass.states)) {
            if (!eid.startsWith("media_player."))
                continue;
            if (this._hass.states[eid].attributes?.config_entry_id === entryId)
                return eid;
        }
        const prefix = this._config.entity
            .replace("remote.", "media_player.")
            .replace(/_remote$/, "");
        if (this._hass.states[prefix])
            return prefix;
        return undefined;
    }
}
/* ── Static helpers (outside the class for smaller closures) ─────────── */
function _rowHtml(btns, cls) {
    return `<div class="${cls}">${btns.map((b) => {
        const hold = b.hold ? ' data-hold="1"' : "";
        const lbl = b.label ? `&nbsp;${b.label}` : "";
        return `<button data-key="${b.key}"${hold}>`
            + `<ha-icon icon="${b.icon}"></ha-icon>${lbl}</button>`;
    }).join("")}</div>`;
}
function _escapeHtml(s) {
    return s
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}
/* ── Register element ────────────────────────────────────────────────── */
const _existing = customElements.get(TAG);
if (_existing) {
    console.warn(`[${TAG}] ALREADY registered by another module (stale SW cache?).`
        + ` Existing class: ${_existing.name}`);
}
else {
    customElements.define(TAG, SamsungTvRemoteCard);
    console.log(`[${TAG}] defined`);
}
console.log(`[${TAG}] ready @${performance.now().toFixed(0)}ms`
    + ` (eval ${(performance.now() - _t0).toFixed(1)}ms)`);
/* Expose load timestamp for debugging from browser console:
   window.__samsungTvCard → { defined: true, time: 42, cls: "SamsungTvRemoteCard" } */
window.__samsungTvCard = {
    defined: !_existing,
    time: performance.now(),
    cls: customElements.get(TAG)?.name,
};
