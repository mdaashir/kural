"""Tests for kural.config.defaults_merge — testing layer merging and overrides."""

from kural.config.defaults_merge import (
    DISABLED_KEY,
    _merge_dicts,
    _merge_lists,
    load_layered,
)


class TestMergeLists:
    def test_shipped_order_preserved(self):
        shipped = [{"id": "1", "name": "First"}, {"id": "2", "name": "Second"}]
        user = []
        merged = _merge_lists(shipped, user, id_key="id")
        assert [e["id"] for e in merged] == ["1", "2"]

    def test_user_own_entry_at_front(self):
        shipped = [{"id": "1", "name": "First"}]
        user = [{"id": "custom", "name": "Custom"}]
        merged = _merge_lists(shipped, user, id_key="id")
        assert merged[0]["id"] == "custom"
        assert merged[1]["id"] == "1"

    def test_user_override_merges_keys(self):
        shipped = [{"id": "1", "name": "First", "val": 10}]
        user = [{"id": "1", "val": 99}]
        merged = _merge_lists(shipped, user, id_key="id")
        assert len(merged) == 1
        assert merged[0]["name"] == "First"
        assert merged[0]["val"] == 99

    def test_disabled_shipped_entry_dropped(self):
        shipped = [{"id": "1", "name": "First"}, {"id": "2", "name": "Second"}]
        user = [{"id": "1", DISABLED_KEY: True}]
        merged = _merge_lists(shipped, user, id_key="id")
        assert len(merged) == 1
        assert merged[0]["id"] == "2"


class TestMergeDicts:
    def test_merge_dicts_basic(self):
        shipped = {"rule1": {"threshold": 0.5, "action": "run"}}
        user = {"rule1": {"threshold": 0.8}, "rule2": {"action": "stop"}}
        merged = _merge_dicts(shipped, user)
        assert merged["rule1"]["threshold"] == 0.8
        assert merged["rule1"]["action"] == "run"
        assert merged["rule2"]["action"] == "stop"


class TestLoadLayered:
    def test_creates_user_file_if_missing(self, tmp_path):
        user_file = tmp_path / "commands.yaml"
        merged, raw = load_layered(
            defaults_filename="commands.defaults.yaml",
            user_path=user_file,
            section="commands",
            header="# Commands\n",
            id_key="trigger",
        )
        assert user_file.exists()
        assert len(merged) > 0
        assert any(cmd.get("trigger") == "undo" for cmd in merged)
