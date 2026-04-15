import { css } from "lit";

export const cardStyles = css`
  :host {
    --btn-bg: var(--card-background-color, #1c1c1c);
    --btn-fg: var(--primary-text-color, #e0e0e0);
    --btn-active: var(--primary-color, #03a9f4);
    --btn-radius: 12px;
    --gap: 6px;
  }

  ha-card {
    padding: 12px;
    overflow: hidden;
  }

  /* ── Common button ──────────────────────────────────────── */

  button {
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--btn-bg);
    color: var(--btn-fg);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--btn-radius);
    cursor: pointer;
    font-size: 13px;
    padding: 10px 0;
    min-height: 42px;
    touch-action: manipulation;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
    transition: opacity 0.1s;
  }

  button:active {
    opacity: 0.6;
  }

  button ha-icon {
    --mdc-icon-size: 22px;
  }

  /* Power button special */
  button.power-on {
    color: var(--btn-active);
    border-color: var(--btn-active);
  }

  /* ── Grid rows ──────────────────────────────────────────── */

  .row-2 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--gap);
    margin-bottom: var(--gap);
  }

  .row-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--gap);
    margin-bottom: var(--gap);
  }

  .row-4 {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--gap);
    margin-bottom: var(--gap);
  }

  .row-5 {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: var(--gap);
    margin-bottom: var(--gap);
  }

  /* ── Text input row ─────────────────────────────────────── */

  .text-row {
    display: flex;
    gap: var(--gap);
    margin-bottom: var(--gap);
    animation: slideIn 0.2s ease-out;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      max-height: 0;
    }
    to {
      opacity: 1;
      max-height: 60px;
    }
  }

  .text-row input {
    flex: 1;
    min-width: 0;
    background: var(--btn-bg);
    color: var(--btn-fg);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--btn-radius);
    padding: 8px 12px;
    font-size: 14px;
    outline: none;
  }

  .text-row input:focus {
    border-color: var(--btn-active);
  }

  .text-row button {
    flex-shrink: 0;
    padding: 8px 14px;
    min-height: 0;
  }

  /* ── Status line ────────────────────────────────────────── */

  .status {
    text-align: center;
    font-size: 11px;
    color: var(--secondary-text-color, #888);
    padding: 2px 0 6px;
  }
`;
