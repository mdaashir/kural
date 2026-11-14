"""Tests for kural.control.guardrails — verifying safety checks and policy enforcement."""

from unittest.mock import MagicMock, patch

from kural.control.guardrails import Guardrails


class TestGuardrailsSafetyChecks:
    def setup_method(self):
        self.guard = Guardrails()

    def test_file_deletion_blocked(self):
        blocked_phrases = [
            "delete file report.docx",
            "erase directory project",
            "remove file test.txt",
            "format c:",
            "wipe drive d:",
            "rm -rf myfolder",
        ]
        for phrase in blocked_phrases:
            safe, reason = self.guard.check_command_safety(phrase)
            assert safe is False, f"Expected '{phrase}' to be blocked"
            assert "File deletion" in reason

    def test_autonomous_transactions_blocked(self):
        blocked_phrases = [
            "pay now using credit card",
            "buy this product with money in cart",
            "transfer funds to john",
            "order items from cart",
        ]
        for phrase in blocked_phrases:
            safe, reason = self.guard.check_command_safety(phrase)
            assert safe is False, f"Expected '{phrase}' to be blocked"
            assert "Purchases and payments" in reason

    def test_safe_phrases_allowed(self):
        safe_phrases = [
            "open notepad",
            "open google and search for python",
            "volume up",
            "mute audio",
            "snap window left",
            "open amazon and search for headphones",  # opening search is safe
        ]
        for phrase in safe_phrases:
            safe, reason = self.guard.check_command_safety(phrase)
            assert safe is True, f"Expected '{phrase}' to be safe, got: {reason}"
            assert reason == ""

    def test_protected_targets(self):
        assert self.guard.is_protected_target("explorer.exe") is True
        assert self.guard.is_protected_target("shell") is True
        assert self.guard.is_protected_target("kural") is True
        assert self.guard.is_protected_target("notepad.exe") is False
        assert self.guard.is_protected_target("chrome") is False

    def test_schedule_shutdown_calls_command(self):
        fake_run = MagicMock()
        fake_run.returncode = 0
        with patch("subprocess.run", return_value=fake_run) as mock_run:
            ok, msg = self.guard.schedule_shutdown(restart=False)
            assert ok is True
            assert "Shutdown scheduled" in msg
            mock_run.assert_called_once()
            cmd_arg = mock_run.call_args[0][0]
            assert "shutdown /s /t 60" in cmd_arg

    def test_cancel_shutdown(self):
        fake_run = MagicMock()
        fake_run.returncode = 0
        with patch("subprocess.run", return_value=fake_run) as mock_run:
            ok, msg = self.guard.cancel_shutdown()
            assert ok is True
            assert "cancelled" in msg
            mock_run.assert_called_once()
            assert "shutdown /a" in mock_run.call_args[0][0]
