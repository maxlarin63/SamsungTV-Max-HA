"""On-disk cache for TV-native app icons served through the HA static path.

Icons arrive from the TV inline (base64) as part of ``ed.apps.icon`` replies.
We decode, write to ``<integration>/frontend/dist/icons/<host_slug>/<appId>.png``
and expose the path under the integration's static URL so the custom card can
render ``<img src=icon_url>``.

The returned URL carries a short sha1 cache-buster (``?v=abc1234``) that only
changes when the PNG bytes change; the TV sometimes updates icons when apps
update, but the ``iconPath`` field stays stable.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import logging
from pathlib import Path

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_ICONS_SUBDIR = "icons"
_URL_BASE = f"/{DOMAIN}/{_ICONS_SUBDIR}"


def host_slug(host: str) -> str:
    """Filesystem-safe slug from a TV host (IPv4 or hostname)."""
    return "".join(c if c.isalnum() else "_" for c in host) or "tv"


def _safe_app_id(app_id: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in app_id) or "unknown"


def cache_root(integration_dir: Path) -> Path:
    """Directory PNGs live in; mapped to ``/samsungtv_max/icons/`` by HA static path."""
    return integration_dir / "frontend" / "dist" / _ICONS_SUBDIR


def icon_path(integration_dir: Path, host: str, app_id: str) -> Path:
    return cache_root(integration_dir) / host_slug(host) / f"{_safe_app_id(app_id)}.png"


def build_url(host: str, app_id: str, sig: str) -> str:
    """Compose the static URL (relative to HA origin) for an icon."""
    return f"{_URL_BASE}/{host_slug(host)}/{_safe_app_id(app_id)}.png?v={sig}"


def _sig(raw: bytes) -> str:
    return hashlib.sha1(raw, usedforsecurity=False).hexdigest()[:8]


def write_icon_b64(
    integration_dir: Path, host: str, app_id: str, image_b64: str
) -> str | None:
    """Decode *image_b64* and write PNG to the cache; return URL or ``None`` on error.

    Skips the disk write when the existing file already matches; the returned
    URL in that case points to the unchanged bytes (same ``?v=`` sig).
    """
    try:
        raw = base64.b64decode(image_b64, validate=False)
    except (binascii.Error, ValueError) as err:
        _LOGGER.debug("Icon b64 decode failed for %s/%s: %s", host, app_id, err)
        return None
    if not raw:
        return None

    target = icon_path(integration_dir, host, app_id)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as err:
        _LOGGER.debug("Icon mkdir %s failed: %s", target.parent, err)
        return None

    new_sig = _sig(raw)
    if target.exists():
        try:
            if _sig(target.read_bytes()) == new_sig:
                return build_url(host, app_id, new_sig)
        except OSError:
            pass

    try:
        target.write_bytes(raw)
    except OSError as err:
        _LOGGER.debug("Icon write %s failed: %s", target, err)
        return None

    return build_url(host, app_id, new_sig)


def existing_url(integration_dir: Path, host: str, app_id: str) -> str | None:
    """Return a URL for an already-cached icon, or ``None`` if not cached."""
    target = icon_path(integration_dir, host, app_id)
    if not target.is_file():
        return None
    try:
        raw = target.read_bytes()
    except OSError:
        return None
    if not raw:
        return None
    return build_url(host, app_id, _sig(raw))
