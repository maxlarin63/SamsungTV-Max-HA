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

/* ── Card picker registration ────────────────────────────────────────── */

interface CardPickerEntry { type: string; name: string; description: string }
const _w = window as unknown as { customCards: CardPickerEntry[] };
_w.customCards = _w.customCards || [];
if (!_w.customCards.some((c) => c.type === TAG)) {
  _w.customCards.push({
    type: TAG,
    name: "Samsung TV Remote",
    description: "Full remote control for Samsung Tizen TVs (Samsung TV Max)",
  });
}

/* ── Types ───────────────────────────────────────────────────────────── */

interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
}

interface Hass {
  states: Record<string, HassEntity>;
  callService(
    domain: string,
    service: string,
    data?: Record<string, unknown>,
    target?: { entity_id?: string },
  ): Promise<void>;
}

interface CardConfig {
  type: string;
  entity: string;
}

/* ── Button definitions ──────────────────────────────────────────────── */

interface Btn { key: string; icon: string; label?: string; hold?: boolean }

const ROW_POWER: Btn[] = [
  { key: "_POWER", icon: "mdi:power", label: "ON" },
  { key: "KEY_MENU", icon: "mdi:menu", label: "Menu" },
];
const VOL_CH_UP: Btn[] = [
  { key: "KEY_VOLUP", icon: "mdi:volume-plus", label: "Vol +", hold: true },
  { key: "KEY_MUTE", icon: "mdi:volume-off", label: "Mute" },
  { key: "KEY_CHUP", icon: "mdi:arrow-up-bold", label: "CH up", hold: true },
];
const VOL_CH_DN: Btn[] = [
  { key: "KEY_VOLDOWN", icon: "mdi:volume-minus", label: "Vol \u2212", hold: true },
  { key: "KEY_SOURCE", icon: "mdi:video-input-hdmi", label: "Source" },
  { key: "KEY_CHDOWN", icon: "mdi:arrow-down-bold", label: "CH dn", hold: true },
];
const DPAD_TOP: Btn[] = [
  { key: "KEY_HOME", icon: "mdi:home", label: "Home" },
  { key: "KEY_UP", icon: "mdi:arrow-up", hold: true },
  { key: "KEY_INFO", icon: "mdi:information", label: "Info" },
];
const DPAD_MID: Btn[] = [
  { key: "KEY_LEFT", icon: "mdi:arrow-left", hold: true },
  { key: "KEY_ENTER", icon: "mdi:keyboard-return", label: "OK" },
  { key: "KEY_RIGHT", icon: "mdi:arrow-right", hold: true },
];
const DPAD_BOT: Btn[] = [
  { key: "KEY_RETURN", icon: "mdi:keyboard-backspace", label: "Back" },
  { key: "KEY_DOWN", icon: "mdi:arrow-down", hold: true },
  { key: "KEY_EXIT", icon: "mdi:close", label: "Exit" },
];

interface TransportBtn { service: string; icon: string }
const TRANSPORTS: TransportBtn[] = [
  { service: "media_play", icon: "mdi:play" },
  { service: "media_pause", icon: "mdi:pause" },
  { service: "media_stop", icon: "mdi:stop" },
  { service: "media_previous_track", icon: "mdi:skip-previous" },
  { service: "media_next_track", icon: "mdi:skip-next" },
];

interface AppBtn { name: string; icon: string; label: string }
const APPS: AppBtn[] = [
  { name: "YouTube", icon: "mdi:youtube", label: "YT" },
  { name: "Netflix", icon: "mdi:netflix", label: "Netflix" },
  { name: "Spotify", icon: "mdi:spotify", label: "Spotify" },
  { name: "Browser", icon: "mdi:earth", label: "Web" },
];

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
  cursor: pointer; font-size: 13px; padding: 10px 0; min-height: 42px;
  touch-action: manipulation; user-select: none;
  -webkit-tap-highlight-color: transparent;
  transition: opacity .1s;
}
button:active { opacity: .6; }
button ha-icon { --mdc-icon-size: 22px; }
button.power-on { color: var(--btn-active); border-color: var(--btn-active); }

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
`;

/* ── Hold-repeat helper ──────────────────────────────────────────────── */

const HOLD_INTERVAL_MS = 150;

function bindHoldRepeat(el: HTMLElement, cb: () => void): () => void {
  let timer: ReturnType<typeof setInterval> | undefined;
  const stop = () => {
    if (timer !== undefined) { clearInterval(timer); timer = undefined; }
  };
  const down = (ev: PointerEvent) => {
    if (ev.button !== 0) return;
    ev.preventDefault();
    stop();
    cb();
    timer = setInterval(cb, HOLD_INTERVAL_MS);
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
  /* Keeps the element in Lovelace's DOM tree even when the view tab is hidden. */
  public connectedWhileHidden = true;

  private _config: CardConfig | null = null;
  private _hass: Hass | null = null;
  private _prevEntityState: HassEntity | null = null;
  private _textValue = "";
  private _holdCleanups: (() => void)[] = [];
  private _domReady = false;

  /* Cached DOM refs (set once in _createDom) */
  private _powerBtn: HTMLButtonElement | null = null;
  private _textRow: HTMLElement | null = null;
  private _textInput: HTMLInputElement | null = null;
  private _transportRow: HTMLElement | null = null;
  private _statusLine: HTMLElement | null = null;

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  /* ── HA lifecycle ─────────────────────────────────────────────────── */

  set hass(value: Hass) {
    this._hass = value;
    if (!this._config?.entity) return;
    const newState = value?.states?.[this._config.entity] ?? null;
    if (newState !== this._prevEntityState) {
      this._prevEntityState = newState;
      this._refresh();
    }
  }

  get hass(): Hass | null {
    return this._hass;
  }

  public setConfig(config: CardConfig): void {
    console.log(`[${TAG}] setConfig entity=${config?.entity}`);
    this._config = config ? { ...config } : null;
    this._domReady = false;
    this._prevEntityState = null;
    this._refresh();
  }

  public getCardSize(): number {
    return 8;
  }

  public connectedCallback(): void {
    this._refresh();
  }

  public disconnectedCallback(): void {
    this._holdCleanups.forEach((fn) => fn());
    this._holdCleanups = [];
  }

  /* ── Render orchestration ─────────────────────────────────────────── */

  private _refresh(): void {
    const sr = this.shadowRoot;
    if (!sr || !this._config || !this._hass) return;

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

  private _showMessage(msg: string): void {
    this.shadowRoot!.innerHTML =
      `<style>${CARD_CSS}</style><ha-card><div class="status">${msg}</div></ha-card>`;
    this._domReady = false;
  }

  /* ── One-time DOM creation ────────────────────────────────────────── */

  private _createDom(): void {
    this._holdCleanups.forEach((fn) => fn());
    this._holdCleanups = [];

    const sr = this.shadowRoot!;
    sr.innerHTML = `<style>${CARD_CSS}</style><ha-card>
${_rowHtml(ROW_POWER, "row-2")}
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
<div class="row-5" id="transport-row">${TRANSPORTS.map((t) =>
  `<button data-transport="${t.service}"><ha-icon icon="${t.icon}"></ha-icon></button>`).join("")
}</div>
<div class="row-4">${APPS.map((a) =>
  `<button data-app="${a.name}"><ha-icon icon="${a.icon}"></ha-icon>&nbsp;${a.label}</button>`).join("")
}</div>
<div class="status" id="status-line"></div>
</ha-card>`;

    this._powerBtn = sr.querySelector('button[data-key="_POWER"]');
    this._textRow = sr.getElementById("text-row");
    this._textInput = sr.querySelector<HTMLInputElement>("#text-row input");
    this._transportRow = sr.getElementById("transport-row");
    this._statusLine = sr.getElementById("status-line");

    this._bindEvents(sr);
    this._domReady = true;
  }

  /* ── Selective DOM updates (no innerHTML, preserves focus) ─────────── */

  private _updateDom(stateObj: HassEntity): void {
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
      const model = (attrs.tv_model as string) || "Samsung TV";
      const power = (attrs.power_state as string) ?? "unknown";
      this._statusLine.textContent = `${model} \u00b7 ${power}`;
    }
  }

  /* ── Event binding (runs once after _createDom) ───────────────────── */

  private _bindEvents(sr: ShadowRoot): void {
    const card = sr.querySelector("ha-card")!;

    card.addEventListener("click", (e: Event) => {
      const btn = (e.target as HTMLElement).closest("button") as HTMLButtonElement | null;
      if (!btn) return;
      if (btn.dataset.hold) return;

      if (btn.dataset.key) {
        this._handleKeyTap(btn.dataset.key);
      } else if (btn.dataset.transport) {
        const mp = this._transportRow?.dataset.mpEntity;
        if (mp) this._callMediaPlayer(btn.dataset.transport, mp);
      } else if (btn.dataset.app) {
        this._launchApp(btn.dataset.app);
      } else if (btn.classList.contains("send-btn")) {
        this._sendText();
      } else if (btn.classList.contains("clear-btn")) {
        this._textValue = "";
        if (this._textInput) this._textInput.value = "";
      }
    });

    sr.querySelectorAll<HTMLButtonElement>("button[data-hold]").forEach((btn) => {
      const key = btn.dataset.key!;
      this._holdCleanups.push(bindHoldRepeat(btn, () => this._sendKey(key)));
    });

    if (this._textInput) {
      this._textInput.addEventListener("input", () => {
        this._textValue = this._textInput!.value;
      });
      this._textInput.addEventListener("keydown", (e: KeyboardEvent) => {
        if (e.key === "Enter") this._sendText();
      });
    }
  }

  /* ── Actions ──────────────────────────────────────────────────────── */

  private _handleKeyTap(key: string): void {
    if (!this._hass || !this._config) return;
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

  private _sendKey(key: string): void {
    if (!this._hass) return;
    this._hass.callService("samsungtv_max", "send_key", {
      key,
      entry_id: this._getEntryId(),
    });
  }

  private _sendText(): void {
    if (!this._textValue || !this._hass) return;
    this._hass.callService("samsungtv_max", "send_text", {
      text: this._textValue,
      entry_id: this._getEntryId(),
    });
    this._textValue = "";
    if (this._textInput) this._textInput.value = "";
  }

  private _launchApp(name: string): void {
    if (!this._hass || !this._config) return;
    const attrs = this._hass.states[this._config.entity]?.attributes;
    this._hass.callService("samsungtv_max", "launch_app", {
      app_name: name,
      entry_id: (attrs?.config_entry_id as string) || "",
    });
  }

  private _callMediaPlayer(service: string, entityId: string): void {
    if (!this._hass) return;
    this._hass.callService("media_player", service, undefined, {
      entity_id: entityId,
    });
  }

  /* ── Helpers ──────────────────────────────────────────────────────── */

  private _getEntryId(): string {
    if (!this._hass || !this._config) return "";
    const ent = this._hass.states[this._config.entity];
    return (ent?.attributes?.config_entry_id as string) ?? "";
  }

  private _findMediaPlayer(attrs: Record<string, unknown>): string | undefined {
    if (!this._hass || !this._config) return undefined;
    const entryId = attrs.config_entry_id as string;
    for (const eid of Object.keys(this._hass.states)) {
      if (!eid.startsWith("media_player.")) continue;
      if (this._hass.states[eid].attributes?.config_entry_id === entryId) return eid;
    }
    const prefix = this._config.entity
      .replace("remote.", "media_player.")
      .replace(/_remote$/, "");
    if (this._hass.states[prefix]) return prefix;
    return undefined;
  }
}

/* ── Static helpers (outside the class for smaller closures) ─────────── */

function _rowHtml(btns: Btn[], cls: string): string {
  return `<div class="${cls}">${btns.map((b) => {
    const hold = b.hold ? ' data-hold="1"' : "";
    const lbl = b.label ? `&nbsp;${b.label}` : "";
    return `<button data-key="${b.key}"${hold}>`
      + `<ha-icon icon="${b.icon}"></ha-icon>${lbl}</button>`;
  }).join("")}</div>`;
}

/* ── Register element ────────────────────────────────────────────────── */

const _existing = customElements.get(TAG);
if (_existing) {
  console.warn(
    `[${TAG}] ALREADY registered by another module (stale SW cache?).`
    + ` Existing class: ${_existing.name}`,
  );
} else {
  customElements.define(TAG, SamsungTvRemoteCard);
  console.log(`[${TAG}] defined`);
}
console.log(
  `[${TAG}] ready @${performance.now().toFixed(0)}ms`
  + ` (eval ${(performance.now() - _t0).toFixed(1)}ms)`,
);

/* Expose load timestamp for debugging from browser console:
   window.__samsungTvCard → { defined: true, time: 42, cls: "SamsungTvRemoteCard" } */
(window as unknown as Record<string, unknown>).__samsungTvCard = {
  defined: !_existing,
  time: performance.now(),
  cls: customElements.get(TAG)?.name,
};
