"""Tests for util_mac."""

from __future__ import annotations

from custom_components.samsungtv_max.util_mac import (
    directed_broadcast_ipv4,
    normalize_tv_ipv4_host,
    normalize_wol_mac,
)


def test_normalize_colon_mac() -> None:
    assert normalize_wol_mac("AA:BB:CC:DD:EE:FF") == "aa:bb:cc:dd:ee:ff"


def test_normalize_hyphen_mac() -> None:
    assert normalize_wol_mac("aa-bb-cc-dd-ee-ff") == "aa:bb:cc:dd:ee:ff"


def test_normalize_compact_mac() -> None:
    assert normalize_wol_mac("aabbccddeeff") == "aa:bb:cc:dd:ee:ff"


def test_normalize_rejects_duid() -> None:
    assert normalize_wol_mac("uuid:12345678-1234-1234-1234-123456789012") is None


def test_directed_broadcast() -> None:
    assert directed_broadcast_ipv4("192.168.116.55") == "192.168.116.255"


def test_normalize_tv_ipv4() -> None:
    assert normalize_tv_ipv4_host(" 192.168.1.1 ") == "192.168.1.1"


def test_normalize_tv_ipv4_rejects_hostname() -> None:
    assert normalize_tv_ipv4_host("samsung-tv.local") is None


def test_normalize_tv_ipv4_rejects_loopback() -> None:
    assert normalize_tv_ipv4_host("127.0.0.1") is None
