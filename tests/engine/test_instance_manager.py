"""Tests for kural.engine.instance_manager — single-instance mutex and graceful takeover."""

import os
from unittest.mock import patch

from kural.engine.instance_manager import (
    acquire_single_instance_lock,
    cleanup_pid_file,
    get_pid_file_path,
    read_existing_pid,
    release_single_instance_lock,
    terminate_process,
    write_pid_file,
)


class TestPidFileOperations:
    def test_pid_file_lifecycle(self, tmp_path):
        with patch(
            "kural.engine.instance_manager.get_user_app_data_path", return_value=str(tmp_path)
        ):
            # Initially no PID file
            assert read_existing_pid("testapp") is None

            # Write current PID
            write_pid_file("testapp")
            assert read_existing_pid("testapp") == os.getpid()

            # Clean up
            cleanup_pid_file("testapp")
            assert read_existing_pid("testapp") is None
            assert not get_pid_file_path("testapp").exists()

    def test_read_corrupted_pid_returns_none(self, tmp_path):
        with patch(
            "kural.engine.instance_manager.get_user_app_data_path", return_value=str(tmp_path)
        ):
            pid_file = get_pid_file_path("corrupt_app")
            pid_file.write_text("not_a_valid_integer", encoding="utf-8")
            assert read_existing_pid("corrupt_app") is None


class TestProcessTermination:
    def test_terminate_process_ignores_self(self):
        assert terminate_process(os.getpid()) is False

    def test_terminate_process_signals_target(self):
        with patch("os.kill") as mock_kill:
            res = terminate_process(99999)
            assert res is True
            mock_kill.assert_called_once()


class TestInstanceLockAcquisition:
    def test_acquire_lock_fresh_instance(self, tmp_path):
        with (
            patch(
                "kural.engine.instance_manager.get_user_app_data_path", return_value=str(tmp_path)
            ),
            patch("kural.engine.instance_manager._create_win32_mutex", return_value=(12345, False)),
        ):
            ok, handle = acquire_single_instance_lock("fresh_app")
            assert ok is True
            assert handle == 12345
            assert read_existing_pid("fresh_app") == os.getpid()

    def test_acquire_lock_already_exists_no_takeover(self, tmp_path):
        with (
            patch(
                "kural.engine.instance_manager.get_user_app_data_path", return_value=str(tmp_path)
            ),
            patch("kural.engine.instance_manager._create_win32_mutex", return_value=(999, True)),
            patch("kural.engine.instance_manager._close_win32_mutex") as mock_close,
        ):
            ok, handle = acquire_single_instance_lock("blocked_app", allow_takeover=False)
            assert ok is False
            assert handle is None
            mock_close.assert_called_once_with(999)

    def test_acquire_lock_with_takeover_terminates_old_and_succeeds(self, tmp_path):
        with (
            patch(
                "kural.engine.instance_manager.get_user_app_data_path", return_value=str(tmp_path)
            ),
            patch("kural.engine.instance_manager.read_existing_pid", return_value=88888),
            patch("kural.engine.instance_manager.terminate_process") as mock_term,
            patch(
                "kural.engine.instance_manager._create_win32_mutex",
                side_effect=[(111, True), (222, False)],
            ),
            patch("kural.engine.instance_manager._close_win32_mutex"),
        ):
            ok, handle = acquire_single_instance_lock("takeover_app", timeout=1.0)
            assert ok is True
            assert handle == 222
            mock_term.assert_called_once_with(88888)

    def test_release_lock_cleans_up(self, tmp_path):
        with (
            patch(
                "kural.engine.instance_manager.get_user_app_data_path", return_value=str(tmp_path)
            ),
            patch("kural.engine.instance_manager._close_win32_mutex") as mock_close,
        ):
            write_pid_file("test_rel")
            release_single_instance_lock(7777, "test_rel")
            assert read_existing_pid("test_rel") is None
            mock_close.assert_called_once_with(7777)
