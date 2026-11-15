"""Tests for kural.engine.dictionary — adding, removing, and listing hotwords in user_settings.yaml."""

from kural.engine.dictionary import add_hotword, list_hotwords, remove_hotword


class TestDictionaryHotwords:
    def test_list_hotwords_empty_when_file_absent(self, tmp_path):
        dummy_file = tmp_path / "user_settings.yaml"
        assert list_hotwords(settings_path=dummy_file) == []

    def test_add_and_list_hotwords(self, tmp_path):
        dummy_file = tmp_path / "user_settings.yaml"
        assert add_hotword("Aashir", settings_path=dummy_file) is True
        assert add_hotword("குரல்", settings_path=dummy_file) is True

        words = list_hotwords(settings_path=dummy_file)
        assert "Aashir" in words
        assert "குரல்" in words

    def test_add_duplicate_returns_false(self, tmp_path):
        dummy_file = tmp_path / "user_settings.yaml"
        assert add_hotword("PyTorch", settings_path=dummy_file) is True
        assert add_hotword("PyTorch", settings_path=dummy_file) is False

    def test_remove_hotword(self, tmp_path):
        dummy_file = tmp_path / "user_settings.yaml"
        add_hotword("Whisper", settings_path=dummy_file)
        assert "Whisper" in list_hotwords(settings_path=dummy_file)

        assert remove_hotword("Whisper", settings_path=dummy_file) is True
        assert "Whisper" not in list_hotwords(settings_path=dummy_file)

    def test_remove_nonexistent_returns_false(self, tmp_path):
        dummy_file = tmp_path / "user_settings.yaml"
        assert remove_hotword("Nonexistent", settings_path=dummy_file) is False
