"""Samsung TV capability detection based on model string generation prefix.

Direct port of the Lua _detectCaps() / TV_CAPS_UNSUPPORTED table from appLaunch.lua.

Platform generations are encoded in the model prefix returned by GET /api/v2/:
  device.model  e.g. "16_HAWKM_FHD"  (older, 16xx series)
                     "QE49Q67RATXXH"  (19_+ generation — no numeric prefix)

Capability flags
----------------
meta_tag_nav  : TV supports REST polling GET /api/v2/applications/{id}
                (returns {"running": true/false}).
                False for generations 15_–18_.
has_ghost_api : TV supports app enumeration via ed.installedApp.get WS message.
                False for generations 15_–17_.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ..const import TV_CAPS_UNSUPPORTED

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class TizenCaps:
    """Immutable capability flags for a specific TV model."""

    meta_tag_nav: bool = True
    has_ghost_api: bool = True

    def __str__(self) -> str:
        return f"meta_tag_nav={self.meta_tag_nav} has_ghost_api={self.has_ghost_api}"


def detect_caps(model: str | None) -> TizenCaps:
    """Return capability flags for *model*.

    If *model* is empty or None, assume full capabilities (modern TV).
    """
    if not model:
        _LOGGER.debug("caps: model unknown — assuming full capabilities")
        return TizenCaps()

    kwargs: dict[str, bool] = {}
    for cap, prefixes in TV_CAPS_UNSUPPORTED.items():
        flagged = any(model.startswith(p) for p in prefixes)
        kwargs[cap] = not flagged

    caps = TizenCaps(**kwargs)
    _LOGGER.debug("caps: model=%s | %s", model, caps)
    return caps


def extract_generation(model: str | None) -> str:
    """Return the generation prefix string (e.g. '16_', '19_') or 'unknown'."""
    if not model:
        return "unknown"
    # Older models have a numeric prefix like "16_HAWKM_FHD"
    for prefix_len in (3, 2):
        prefix = model[:prefix_len]
        if prefix.rstrip("_").isdigit():
            return model[: prefix_len + (1 if "_" not in prefix else 0)].split("_")[0] + "_"
    return "modern"
