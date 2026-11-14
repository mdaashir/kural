"""Tests for kural.engine.model_registry — mocks filesystem and faster_whisper."""

from unittest.mock import patch

import pytest


@pytest.fixture()
def Registry():
    from kural.engine.model_registry import ModelRegistry

    return ModelRegistry


class TestModelRegistry:
    def test_empty_registry(self, Registry):
        reg = Registry()
        assert reg.get_model("base") is None
        assert reg.get_source("base") == "base"

    def test_get_source_with_model(self, Registry):
        cfg = {"base": {"source": "Systran/faster-whisper-base", "group": "official"}}
        reg = Registry(whisper_models_config=cfg)
        assert reg.get_source("base") == "Systran/faster-whisper-base"

    def test_get_groups_ordered(self, Registry):
        reg = Registry()
        assert reg.get_groups_ordered() == ["official", "custom"]

    def test_hf_cache_path_uses_userprofile(self, Registry, monkeypatch):
        monkeypatch.setenv("USERPROFILE", "C:\\Users\\test")
        reg = Registry()
        path = reg.get_hf_cache_path()
        assert "test" in path
        assert "huggingface" in path

    def test_is_model_cached_false_when_no_folder(self, Registry, tmp_path, monkeypatch):
        cfg = {"base": {"source": "Systran/faster-whisper-base", "group": "official"}}
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        reg = Registry(whisper_models_config=cfg)
        assert reg.is_model_cached("base") is False

    def test_is_model_cached_local_path_true(self, Registry, tmp_path):
        model_dir = tmp_path / "mymodel"
        model_dir.mkdir()
        (model_dir / "model.bin").touch()
        cfg = {"local": {"source": str(model_dir), "group": "custom"}}
        reg = Registry(whisper_models_config=cfg)
        assert reg.is_model_cached("local") is True

    def test_get_models_by_group(self, Registry):
        cfg = {
            "base": {
                "source": "Systran/faster-whisper-base",
                "group": "official",
                "enabled": True,
            },
            "custom-m": {"source": "/local/path", "group": "custom", "enabled": True},
        }
        reg = Registry(whisper_models_config=cfg)
        official = reg.get_models_by_group("official")
        assert len(official) == 1
        assert official[0].key == "base"

    def test_model_definition_local_unc_path(self, Registry):
        cfg = {"unc": {"source": "\\\\server\\share\\model", "group": "custom"}}
        reg = Registry(whisper_models_config=cfg)
        m = reg.get_model("unc")
        assert m.is_local_path is True

    def test_model_definition_cache_folder_official(self, Registry):
        with patch(
            "kural.engine.model_registry._MODELS",
            {"base": "Systran/faster-whisper-base"},
        ):
            cfg = {"base": {"source": "base", "group": "official"}}
            reg = Registry(whisper_models_config=cfg)
            m = reg.get_model("base")
            assert m.cache_folder == "models--Systran--faster-whisper-base"
