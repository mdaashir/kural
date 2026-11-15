"""Tests for kural.control.app_rules — foreground app rule matching and formatting styles."""

from kural.control.app_rules import AppRules, apply_formatting_style


class TestFormattingStyles:
    def test_formal_style_capitalizes_and_punctuates(self):
        raw = "hello world"
        formatted = apply_formatting_style(raw, "formal")
        assert formatted == "Hello world."

    def test_verbatim_style_preserves_case_and_strips_period(self):
        raw = "git status."
        formatted = apply_formatting_style(raw, "verbatim")
        assert formatted == "git status"

    def test_casual_style_strips_trailing_period(self):
        raw = "see you tomorrow."
        formatted = apply_formatting_style(raw, "casual")
        assert formatted == "see you tomorrow"

    def test_empty_string_safe(self):
        assert apply_formatting_style("", "formal") == ""
        assert apply_formatting_style("   ", "verbatim") == ""


class TestAppRulesMatching:
    def test_matches_password_manager_suppress(self, tmp_path):
        rules_yaml = tmp_path / "app_rules.yaml"
        app_rules = AppRules(user_rules_path=rules_yaml)

        # 1Password match
        rule = app_rules.match_rule(exe="1password.exe", title="1Password")
        assert rule is not None
        assert rule.get("id") == "password-managers"
        assert rule.get("suppress") is True

        # Bitwarden title match in browser
        rule = app_rules.match_rule(exe="chrome.exe", title="Bitwarden Vault - Google Chrome")
        assert rule is not None
        assert rule.get("id") == "password-managers"

    def test_matches_terminals_verbatim(self, tmp_path):
        app_rules = AppRules(user_rules_path=tmp_path / "app_rules.yaml")
        rule = app_rules.match_rule(exe="wt.exe", title="PowerShell")
        assert rule is not None
        assert rule.get("id") == "terminals"
        assert rule.get("style") == "verbatim"

    def test_matches_code_editors_verbatim(self, tmp_path):
        app_rules = AppRules(user_rules_path=tmp_path / "app_rules.yaml")
        rule = app_rules.match_rule(exe="code.exe", title="kural — VS Code")
        assert rule is not None
        assert rule.get("id") == "code-editors"
        assert rule.get("style") == "verbatim"

    def test_matches_chat_apps_casual(self, tmp_path):
        app_rules = AppRules(user_rules_path=tmp_path / "app_rules.yaml")
        rule = app_rules.match_rule(exe="slack.exe", title="Slack | Engineering")
        assert rule is not None
        assert rule.get("id") == "chat-apps"
        assert rule.get("style") == "casual"

    def test_unmatched_returns_none(self, tmp_path):
        app_rules = AppRules(user_rules_path=tmp_path / "app_rules.yaml")
        rule = app_rules.match_rule(exe="random_unlisted_app.exe", title="Calculator")
        assert rule is None
