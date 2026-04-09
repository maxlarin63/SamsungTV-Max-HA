"""Tests for tizen/caps.py — capability detection."""

import pytest

from custom_components.samsungtv_max.tizen.caps import TizenCaps, detect_caps, extract_generation


class TestDetectCaps:
    def test_modern_tv_full_caps(self):
        caps = detect_caps("QE55Q80RATXXH")
        assert caps.meta_tag_nav is True
        assert caps.has_ghost_api is True

    def test_16_series_no_meta_no_ghost(self):
        caps = detect_caps("16_HAWKM_FHD")
        assert caps.meta_tag_nav is False
        assert caps.has_ghost_api is False

    def test_17_series_no_meta_no_ghost(self):
        caps = detect_caps("17_KANTM_UHD")
        assert caps.meta_tag_nav is False
        assert caps.has_ghost_api is False

    def test_18_series_no_meta_has_ghost(self):
        # 18_ blocks meta_tag_nav but NOT has_ghost_api
        caps = detect_caps("18_MUSEL_4K")
        assert caps.meta_tag_nav is False
        assert caps.has_ghost_api is True

    def test_15_series_no_meta_no_ghost(self):
        caps = detect_caps("15_SAHARA")
        assert caps.meta_tag_nav is False
        assert caps.has_ghost_api is False

    def test_empty_model_full_caps(self):
        caps = detect_caps("")
        assert caps == TizenCaps(meta_tag_nav=True, has_ghost_api=True)

    def test_none_model_full_caps(self):
        caps = detect_caps(None)
        assert caps == TizenCaps(meta_tag_nav=True, has_ghost_api=True)

    def test_19_series_full_caps(self):
        caps = detect_caps("19_ARTM_UHD")
        assert caps.meta_tag_nav is True
        assert caps.has_ghost_api is True


class TestExtractGeneration:
    def test_16_model(self):
        assert extract_generation("16_HAWKM_FHD") == "16_"

    def test_modern_model(self):
        result = extract_generation("QE55Q80RATXXH")
        assert result == "modern"

    def test_none(self):
        assert extract_generation(None) == "unknown"

    def test_empty(self):
        assert extract_generation("") == "unknown"
