"""MAC / IPv4 helpers for Wake-on-LAN."""

from __future__ import annotations

import ipaddress
import re

_MAC_RE = re.compile(r"^([0-9A-Fa-f]{2})[:-]?([0-9A-Fa-f]{2})[:-]?([0-9A-Fa-f]{2})[:-]?([0-9A-Fa-f]{2})[:-]?([0-9A-Fa-f]{2})[:-]?([0-9A-Fa-f]{2})$")

_CISCO_STYLE_RE = re.compile(
    r"^([0-9A-Fa-f]{4})\.([0-9A-Fa-f]{4})\.([0-9A-Fa-f]{4})$"
)


def normalize_wol_mac(raw: str | None) -> str | None:
    """Return ``aa:bb:cc:dd:ee:ff`` or ``None`` if *raw* is not a usable MAC."""
    if not raw:
        return None
    s = raw.strip().lower()
    if not s:
        return None

    m = _MAC_RE.match(s.replace(".", ":"))
    if m:
        return ":".join(m.groups())

    cm = _CISCO_STYLE_RE.match(s)
    if cm:
        parts = [cm.group(i)[j : j + 2] for i in range(1, 4) for j in (0, 2)]
        return ":".join(parts)

    hexonly = s.replace(":", "").replace("-", "").replace(".", "")
    if len(hexonly) != 12:
        return None
    try:
        int(hexonly, 16)
    except ValueError:
        return None
    return ":".join(hexonly[i : i + 2] for i in range(0, 12, 2))


def normalize_tv_ipv4_host(host: str | None) -> str | None:
    """Return canonical IPv4 string or ``None`` (hostnames and non-unicast are rejected)."""
    if not host:
        return None
    s = host.strip()
    if not s:
        return None
    try:
        addr = ipaddress.IPv4Address(s)
    except ValueError:
        return None
    if addr.is_multicast or addr.is_unspecified or addr.is_loopback or addr.is_link_local:
        return None
    if addr.is_reserved:
        return None
    return str(addr)


def directed_broadcast_ipv4(host: str) -> str | None:
    """Best-effort directed broadcast (assume /24) for *host* like ``192.168.1.50``."""
    parts = host.strip().split(".")
    if len(parts) != 4:
        return None
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return None
    if any(n < 0 or n > 255 for n in nums):
        return None
    return f"{nums[0]}.{nums[1]}.{nums[2]}.255"
