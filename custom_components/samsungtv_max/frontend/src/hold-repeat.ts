const REPEAT_INTERVAL_MS = 150;

/**
 * Attach hold-to-repeat behaviour to an element.
 * pointerdown → immediate first call + repeat at 150 ms.
 * pointerup / pointerleave / pointercancel → stop.
 */
export function bindHoldRepeat(
  el: HTMLElement,
  callback: () => void,
): void {
  let timer: ReturnType<typeof setInterval> | undefined;

  const stop = () => {
    if (timer !== undefined) {
      clearInterval(timer);
      timer = undefined;
    }
  };

  el.addEventListener("pointerdown", (ev: PointerEvent) => {
    if (ev.button !== 0) return;
    ev.preventDefault();
    stop();
    callback();
    timer = setInterval(callback, REPEAT_INTERVAL_MS);
  });

  el.addEventListener("pointerup", stop);
  el.addEventListener("pointerleave", stop);
  el.addEventListener("pointercancel", stop);
}
