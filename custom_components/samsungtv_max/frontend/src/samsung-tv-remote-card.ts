import { LitElement, html, nothing, type PropertyValues, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { cardStyles } from "./styles.js";
import { bindHoldRepeat } from "./hold-repeat.js";
import type {
  HomeAssistant,
  SamsungTvRemoteCardConfig,
  SamsungTvAttributes,
} from "./types.js";

/* ── Card picker registration ─────────────────────────────────────────────── */

// eslint-disable-next-line @typescript-eslint/no-explicit-any
(window as any).customCards = (window as any).customCards || [];
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(window as any).customCards.push({
  type: "samsung-tv-remote-card",
  name: "Samsung TV Remote",
  description: "Full remote control for Samsung Tizen TVs (Samsung TV Max)",
});

/* ── Key definitions ──────────────────────────────────────────────────────── */

interface BtnDef {
  key: string;
  icon: string;
  label?: string;
  hold?: boolean;
}

const ROW_POWER: BtnDef[] = [
  { key: "_POWER", icon: "mdi:power", label: "ON" },
  { key: "KEY_MENU", icon: "mdi:menu", label: "Menu" },
];

const ROW_VOL_CH_UP: BtnDef[] = [
  { key: "KEY_VOLUP", icon: "mdi:volume-plus", label: "Vol +", hold: true },
  { key: "KEY_MUTE", icon: "mdi:volume-off", label: "Mute" },
  { key: "KEY_CHUP", icon: "mdi:arrow-up-bold", label: "CH up", hold: true },
];

const ROW_VOL_CH_DN: BtnDef[] = [
  { key: "KEY_VOLDOWN", icon: "mdi:volume-minus", label: "Vol −", hold: true },
  { key: "KEY_SOURCE", icon: "mdi:video-input-hdmi", label: "Source" },
  { key: "KEY_CHDOWN", icon: "mdi:arrow-down-bold", label: "CH dn", hold: true },
];

const ROW_DPAD_TOP: BtnDef[] = [
  { key: "KEY_HOME", icon: "mdi:home", label: "Home" },
  { key: "KEY_UP", icon: "mdi:arrow-up", hold: true },
  { key: "KEY_INFO", icon: "mdi:information", label: "Info" },
];

const ROW_DPAD_MID: BtnDef[] = [
  { key: "KEY_LEFT", icon: "mdi:arrow-left", hold: true },
  { key: "KEY_ENTER", icon: "mdi:keyboard-return", label: "OK" },
  { key: "KEY_RIGHT", icon: "mdi:arrow-right", hold: true },
];

const ROW_DPAD_BOT: BtnDef[] = [
  { key: "KEY_RETURN", icon: "mdi:keyboard-backspace", label: "Back" },
  { key: "KEY_DOWN", icon: "mdi:arrow-down", hold: true },
  { key: "KEY_EXIT", icon: "mdi:close", label: "Exit" },
];

interface TransportDef {
  service: string;
  icon: string;
  label: string;
}

const TRANSPORT: TransportDef[] = [
  { service: "media_play", icon: "mdi:play", label: "Play" },
  { service: "media_pause", icon: "mdi:pause", label: "Pause" },
  { service: "media_stop", icon: "mdi:stop", label: "Stop" },
  { service: "media_previous_track", icon: "mdi:skip-previous", label: "Prev" },
  { service: "media_next_track", icon: "mdi:skip-next", label: "Next" },
];

interface AppDef {
  name: string;
  icon: string;
  label: string;
}

const APP_SHORTCUTS: AppDef[] = [
  { name: "YouTube", icon: "mdi:youtube", label: "YT" },
  { name: "Netflix", icon: "mdi:netflix", label: "Netflix" },
  { name: "Spotify", icon: "mdi:spotify", label: "Spotify" },
  { name: "Browser", icon: "mdi:earth", label: "Web" },
];

/* ── Card ──────────────────────────────────────────────────────────────────── */

@customElement("samsung-tv-remote-card")
export class SamsungTvRemoteCard extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @state() private _config?: SamsungTvRemoteCardConfig;
  @state() private _textValue = "";

  static styles = cardStyles;

  /* ── Lifecycle ──────────────────────────────────────────────────────────── */

  public setConfig(config: SamsungTvRemoteCardConfig): void {
    if (!config.entity) {
      throw new Error("entity is required");
    }
    this._config = config;
  }

  public getCardSize(): number {
    return 8;
  }

  protected updated(changed: PropertyValues): void {
    super.updated(changed);
    if (changed.has("hass") && this.hass && this._config) {
      const ent = this.hass.states[this._config.entity];
      if (ent) {
        const attrs = ent.attributes as unknown as SamsungTvAttributes;
        if (attrs.keyboard_active && this._textValue === "") {
          /* will be filled by imeUpdate pre-fill via input_text watcher */
        }
      }
    }
  }

  protected firstUpdated(): void {
    this._bindHoldButtons();
  }

  /* ── Render ─────────────────────────────────────────────────────────────── */

  protected render(): TemplateResult {
    if (!this._config || !this.hass) return html``;

    const entity = this.hass.states[this._config.entity];
    if (!entity) {
      return html`<ha-card><div class="status">Entity not found: ${this._config.entity}</div></ha-card>`;
    }

    const attrs = entity.attributes as unknown as SamsungTvAttributes;
    const isOn = entity.state === "on";

    return html`
      <ha-card>
        ${this._renderRow(ROW_POWER, "row-2", isOn)}
        ${attrs.keyboard_active ? this._renderTextInput() : nothing}
        ${this._renderRow(ROW_VOL_CH_UP, "row-3")}
        ${this._renderRow(ROW_VOL_CH_DN, "row-3")}
        ${this._renderRow(ROW_DPAD_TOP, "row-3")}
        ${this._renderRow(ROW_DPAD_MID, "row-3")}
        ${this._renderRow(ROW_DPAD_BOT, "row-3")}
        ${this._renderTransport(attrs)}
        ${this._renderApps(attrs)}
        <div class="status">
          ${attrs.tv_model || "Samsung TV"} &middot; ${attrs.power_state}
        </div>
      </ha-card>
    `;
  }

  private _renderRow(
    buttons: BtnDef[],
    gridClass: string,
    isOn?: boolean,
  ): TemplateResult {
    return html`
      <div class="${gridClass}">
        ${buttons.map(
          (b) => html`
            <button
              class="${b.key === "_POWER" && isOn ? "power-on" : ""}"
              data-key="${b.key}"
              @click=${() => this._handleKeyTap(b.key)}
            >
              <ha-icon icon="${b.icon}"></ha-icon>
              ${b.label ? html`&nbsp;${b.label}` : nothing}
            </button>
          `,
        )}
      </div>
    `;
  }

  private _renderTextInput(): TemplateResult {
    return html`
      <div class="text-row">
        <input
          type="text"
          placeholder="Type URL / text…"
          .value=${this._textValue}
          @input=${(e: InputEvent) => {
            this._textValue = (e.target as HTMLInputElement).value;
          }}
          @keydown=${(e: KeyboardEvent) => {
            if (e.key === "Enter") this._sendText();
          }}
        />
        <button @click=${this._sendText}>
          <ha-icon icon="mdi:send"></ha-icon>
        </button>
        <button @click=${() => { this._textValue = ""; }}>
          <ha-icon icon="mdi:close-circle-outline"></ha-icon>
        </button>
      </div>
    `;
  }

  private _renderTransport(attrs: SamsungTvAttributes): TemplateResult {
    const mpEntity = this._findMediaPlayer(attrs);
    if (!mpEntity) return html``;
    return html`
      <div class="row-5">
        ${TRANSPORT.map(
          (t) => html`
            <button @click=${() => this._callMediaPlayer(t.service, mpEntity)}>
              <ha-icon icon="${t.icon}"></ha-icon>
            </button>
          `,
        )}
      </div>
    `;
  }

  private _renderApps(attrs: SamsungTvAttributes): TemplateResult {
    return html`
      <div class="row-4">
        ${APP_SHORTCUTS.map(
          (a) => html`
            <button @click=${() => this._launchApp(a.name, attrs)}>
              <ha-icon icon="${a.icon}"></ha-icon>
              &nbsp;${a.label}
            </button>
          `,
        )}
      </div>
    `;
  }

  /* ── Hold-repeat wiring ─────────────────────────────────────────────────── */

  private _bindHoldButtons(): void {
    const root = this.shadowRoot;
    if (!root) return;
    root.querySelectorAll<HTMLButtonElement>("button[data-key]").forEach((btn) => {
      const key = btn.dataset.key!;
      const def = [
        ...ROW_VOL_CH_UP, ...ROW_VOL_CH_DN,
        ...ROW_DPAD_TOP, ...ROW_DPAD_MID, ...ROW_DPAD_BOT,
      ].find((d) => d.key === key);
      if (def?.hold) {
        bindHoldRepeat(btn, () => this._sendKey(key));
      }
    });
  }

  /* ── Actions ────────────────────────────────────────────────────────────── */

  private _handleKeyTap(key: string): void {
    if (key === "_POWER") {
      this.hass.callService("remote", "toggle", undefined, {
        entity_id: this._config!.entity,
      });
      return;
    }
    this.hass.callService("remote", "send_command", { command: key }, {
      entity_id: this._config!.entity,
    });
  }

  private _sendKey(key: string): void {
    const entryId = this._getEntryId();
    this.hass.callService("samsungtv_max", "send_key", {
      key,
      entry_id: entryId,
    });
  }

  private _sendText(): void {
    if (!this._textValue) return;
    const entryId = this._getEntryId();
    this.hass.callService("samsungtv_max", "send_text", {
      text: this._textValue,
      entry_id: entryId,
    });
    this._textValue = "";
  }

  private _launchApp(name: string, attrs: SamsungTvAttributes): void {
    this.hass.callService("samsungtv_max", "launch_app", {
      app_name: name,
      entry_id: attrs.config_entry_id,
    });
  }

  private _callMediaPlayer(service: string, entityId: string): void {
    this.hass.callService("media_player", service, undefined, {
      entity_id: entityId,
    });
  }

  /* ── Helpers ────────────────────────────────────────────────────────────── */

  private _getEntryId(): string {
    const ent = this.hass.states[this._config!.entity];
    return (ent?.attributes as unknown as SamsungTvAttributes)?.config_entry_id ?? "";
  }

  private _findMediaPlayer(attrs: SamsungTvAttributes): string | undefined {
    const entryId = attrs.config_entry_id;
    for (const eid of Object.keys(this.hass.states)) {
      if (!eid.startsWith("media_player.")) continue;
      const s = this.hass.states[eid];
      if (s.attributes?.config_entry_id === entryId) return eid;
    }
    const prefix = this._config!.entity
      .replace("remote.", "media_player.")
      .replace(/_remote$/, "");
    if (this.hass.states[prefix]) return prefix;
    return undefined;
  }
}
