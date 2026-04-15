export interface SamsungTvRemoteCardConfig {
  type: string;
  entity: string;
}

export interface AppInfo {
  id: string;
  name: string;
  type: number;
}

export interface Capabilities {
  meta_tag_nav: boolean;
  has_ghost_api: boolean;
}

export interface SamsungTvAttributes {
  apps: AppInfo[];
  power_state: string;
  keyboard_active: boolean;
  tv_awaiting_authorization: boolean;
  tv_host: string;
  tv_model: string;
  tv_generation: string;
  tv_mac: string;
  tv_token: string;
  config_entry_id: string;
  integration_version: string;
  tizen_rest_port: number;
  tizen_ws_port: number;
  capabilities: Capabilities;
}

export interface HomeAssistant {
  states: Record<string, HassEntity>;
  callService(
    domain: string,
    service: string,
    data?: Record<string, unknown>,
    target?: { entity_id?: string },
  ): Promise<void>;
}

export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
}
