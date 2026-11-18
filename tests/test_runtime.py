"""Tests for kural.runtime — state transitions, processing, and insertion with mocks."""

from unittest.mock import MagicMock, patch

import numpy as np

from kural.control.windows import WindowInfo
from kural.runtime import KuralRuntime, RuntimeState


class TestKuralRuntimeStateTransitions:
    def setup_method(self):
        fake_engine_cls = MagicMock()
        fake_vad_cls = MagicMock()
        fake_rec_cls = MagicMock()
        fake_exec_cls = MagicMock()

        with (
            patch.dict(
                "sys.modules",
                {
                    "kural.engine.voice_activity_detection": MagicMock(VadManager=fake_vad_cls),
                    "kural.engine.whisper_engine": MagicMock(WhisperEngine=fake_engine_cls),
                    "kural.engine.audio_recorder": MagicMock(AudioRecorder=fake_rec_cls),
                    "kural.control.executor": MagicMock(CommandExecutor=fake_exec_cls),
                },
            ),
        ):
            self.runtime = KuralRuntime()
        # Most tests exercise dictation formatting, not a captured foreground HWND.
        self.runtime.config_manager.get_clipboard_config = MagicMock(
            return_value={"return_to_app": False}
        )

    def test_initial_state_idle(self):
        assert self.runtime.state == RuntimeState.IDLE

    def test_toggle_dictation_starts_recording(self):
        self.runtime.toggle_dictation()
        assert self.runtime.state == RuntimeState.RECORDING_DICTATION
        self.runtime.recorder.start_recording.assert_called_once()

    def test_toggle_command_starts_recording(self):
        self.runtime.toggle_command()
        assert self.runtime.state == RuntimeState.RECORDING_COMMAND
        self.runtime.recorder.start_recording.assert_called_once()

    def test_process_audio_dictation_types_text(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.engine.transcribe_audio.return_value = "hello world"

        with patch("kural.runtime.insert_text_at_caret", return_value=True) as mock_insert:
            fake_audio = np.zeros(16000, dtype=np.float32)
            self.runtime._process_audio(fake_audio)
            # Default style is formal (capitalized + trailing period)
            assert mock_insert.call_args[0][0] == "Hello world."
            assert self.runtime.state == RuntimeState.IDLE

    def test_process_audio_copy_only_flashes_copied(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.engine.transcribe_audio.return_value = "copy test"
        self.runtime.config_manager.get_clipboard_config = MagicMock(
            return_value={"delivery_method": "copy"}
        )
        self.runtime.overlay = MagicMock()

        with patch("kural.runtime.insert_text_at_caret", return_value=True):
            fake_audio = np.zeros(16000, dtype=np.float32)
            self.runtime._process_audio(fake_audio)
            self.runtime.overlay.flash_success.assert_called_once_with("Copied")

    def test_process_audio_returns_to_original_app_if_shifted(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.engine.transcribe_audio.return_value = "focus test"
        self.runtime._origin_hwnd = 1001
        self.runtime.config_manager.get_clipboard_config = MagicMock(
            return_value={"return_to_app": True}
        )

        with (
            patch("kural.control.windows.get_foreground_hwnd", side_effect=[2002, 1001]),
            patch(
                "kural.control.windows.get_foreground_window_info",
                return_value=WindowInfo(1001, "Document", "winword.exe"),
            ),
            patch(
                "kural.control.windows.restore_foreground_window", return_value=True
            ) as mock_restore,
            patch("kural.runtime.insert_text_at_caret", return_value=True) as mock_insert,
        ):
            self.runtime._process_audio(np.zeros(16000, dtype=np.float32))
            mock_restore.assert_called_once_with(1001)
            mock_insert.assert_called_once()

    def test_restored_password_manager_suppresses_delivery(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.engine.transcribe_audio.return_value = "secret dictation"
        self.runtime._origin_hwnd = 1001
        self.runtime.config_manager.get_clipboard_config.return_value = {"return_to_app": True}
        self.runtime.app_rules.match_rule = MagicMock(return_value={"suppress": True})

        with (
            patch("kural.control.windows.get_foreground_hwnd", return_value=2002),
            patch("kural.control.windows.restore_foreground_window", return_value=True),
            patch(
                "kural.control.windows.get_foreground_window_info",
                return_value=WindowInfo(1001, "Vault", "bitwarden.exe"),
            ),
            patch("kural.runtime.insert_text_at_caret") as insert,
        ):
            self.runtime._process_audio(np.zeros(16000, dtype=np.float32))
            self.runtime.app_rules.match_rule.assert_called_once_with(
                exe="bitwarden.exe", title="Vault"
            )
            insert.assert_not_called()

    def test_interim_password_manager_does_not_suppress_original_app(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.engine.transcribe_audio.return_value = "draft text"
        self.runtime._origin_hwnd = 1001
        self.runtime.config_manager.get_clipboard_config.return_value = {"return_to_app": True}
        restored = False

        def restore(_hwnd):
            nonlocal restored
            restored = True
            return True

        def window_info():
            if restored:
                return WindowInfo(1001, "Document", "winword.exe")
            return WindowInfo(2002, "Vault", "bitwarden.exe")

        with (
            patch("kural.control.windows.get_foreground_hwnd", side_effect=[2002, 1001]),
            patch("kural.control.windows.restore_foreground_window", side_effect=restore),
            patch("kural.control.windows.get_foreground_window_info", side_effect=window_info),
            patch("kural.runtime.insert_text_at_caret", return_value=True) as insert,
        ):
            self.runtime._process_audio(np.zeros(16000, dtype=np.float32))
            assert restored
            insert.assert_called_once()

    def test_restored_app_rule_controls_formatting_not_interim_app(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.engine.transcribe_audio.return_value = "keep raw"
        self.runtime._origin_hwnd = 1001
        self.runtime.config_manager.get_clipboard_config.return_value = {"return_to_app": True}
        self.runtime.app_rules.match_rule = MagicMock(return_value={"style": "verbatim"})

        with (
            patch("kural.control.windows.get_foreground_hwnd", side_effect=[2002, 1001]),
            patch("kural.control.windows.restore_foreground_window", return_value=True),
            patch(
                "kural.control.windows.get_foreground_window_info",
                return_value=WindowInfo(1001, "Terminal", "pwsh.exe"),
            ),
            patch("kural.runtime.insert_text_at_caret", return_value=True) as insert,
        ):
            self.runtime._process_audio(np.zeros(16000, dtype=np.float32))
            self.runtime.app_rules.match_rule.assert_called_once_with(
                exe="pwsh.exe", title="Terminal"
            )
            assert insert.call_args.args[0] == "keep raw"

    def test_focus_refusal_never_inserts_into_other_app(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.engine.transcribe_audio.return_value = "private dictation"
        self.runtime._origin_hwnd = 1001
        self.runtime.fallback_window = MagicMock()
        self.runtime.config_manager.get_clipboard_config.return_value = {"return_to_app": True}

        with (
            patch("kural.control.windows.get_foreground_hwnd", return_value=2002),
            patch(
                "kural.control.windows.get_foreground_window_info",
                return_value=WindowInfo(2002, "Notification", "teams.exe"),
            ),
            patch("kural.control.windows.restore_foreground_window", return_value=False) as restore,
            patch("kural.runtime.insert_text_at_caret") as insert,
        ):
            self.runtime._process_audio(np.zeros(16000, dtype=np.float32))
            restore.assert_called_once_with(1001)
            insert.assert_not_called()
            self.runtime.fallback_window.show.assert_called_once()
            assert self.runtime.state == RuntimeState.IDLE

    def test_claimed_restoration_without_focus_never_inserts(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.engine.transcribe_audio.return_value = "private dictation"
        self.runtime._origin_hwnd = 1001
        self.runtime.fallback_window = MagicMock()
        self.runtime.config_manager.get_clipboard_config.return_value = {"return_to_app": True}

        with (
            patch("kural.control.windows.get_foreground_hwnd", return_value=2002),
            patch(
                "kural.control.windows.get_foreground_window_info",
                return_value=WindowInfo(2002, "Notification", "teams.exe"),
            ),
            patch("kural.control.windows.restore_foreground_window", return_value=True),
            patch("kural.runtime.insert_text_at_caret") as insert,
        ):
            self.runtime._process_audio(np.zeros(16000, dtype=np.float32))
            insert.assert_not_called()
            self.runtime.fallback_window.show.assert_called_once()

    def test_focus_loss_after_rule_selection_withholds_insertion(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.engine.transcribe_audio.return_value = "private dictation"
        self.runtime._origin_hwnd = 1001
        self.runtime.fallback_window = MagicMock()
        self.runtime.config_manager.get_clipboard_config.return_value = {"return_to_app": True}
        self.runtime.app_rules.match_rule = MagicMock(return_value={"style": "formal"})

        with (
            patch("kural.control.windows.get_foreground_hwnd", return_value=2002),
            patch("kural.control.windows.restore_foreground_window", return_value=True),
            patch(
                "kural.control.windows.get_foreground_window_info",
                return_value=WindowInfo(1001, "Document", "winword.exe"),
            ),
            patch("kural.runtime.insert_text_at_caret") as insert,
        ):
            self.runtime._process_audio(np.zeros(16000, dtype=np.float32))
            self.runtime.app_rules.match_rule.assert_called_once()
            insert.assert_not_called()
            self.runtime.fallback_window.show.assert_called_once()

    def test_missing_original_window_never_inserts(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.engine.transcribe_audio.return_value = "private dictation"
        self.runtime._origin_hwnd = None
        self.runtime.fallback_window = MagicMock()
        self.runtime.config_manager.get_clipboard_config.return_value = {"return_to_app": True}

        with patch("kural.runtime.insert_text_at_caret") as insert:
            self.runtime._process_audio(np.zeros(16000, dtype=np.float32))
            insert.assert_not_called()
            self.runtime.fallback_window.show.assert_called_once()

    def test_copy_only_does_not_refocus_window(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.engine.transcribe_audio.return_value = "copy test"
        self.runtime._origin_hwnd = 1001
        self.runtime.config_manager.get_clipboard_config.return_value = {
            "delivery_method": "copy",
            "return_to_app": True,
        }
        with (
            patch("kural.control.windows.restore_foreground_window") as restore,
            patch("kural.runtime.insert_text_at_caret", return_value=True) as insert,
        ):
            self.runtime._process_audio(np.zeros(16000, dtype=np.float32))
            restore.assert_not_called()
            insert.assert_called_once()

    def test_failed_insertion_triggers_fallback_window(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.engine.transcribe_audio.return_value = "unplaced speech"
        self.runtime.fallback_window = MagicMock()

        # Simulate failed insertion (e.g. no focused window / dropped keystrokes)
        with patch("kural.runtime.insert_text_at_caret", return_value=False):
            fake_audio = np.zeros(16000, dtype=np.float32)
            self.runtime._process_audio(fake_audio)
            self.runtime.fallback_window.show.assert_called_once()
            call_text = self.runtime.fallback_window.show.call_args[0][0]
            assert "Unplaced speech" in call_text

    def test_process_audio_command_routes_to_executor(self):
        self.runtime.state = RuntimeState.RECORDING_COMMAND
        self.runtime.engine.transcribe_audio.return_value = "volume up"
        fake_res = MagicMock()
        fake_res.success = True
        fake_res.feedback = "Volume 70%"
        self.runtime.executor = MagicMock()
        self.runtime.executor.execute.return_value = fake_res

        fake_audio = np.zeros(16000, dtype=np.float32)
        self.runtime._process_audio(fake_audio)
        self.runtime.executor.execute.assert_called_once_with("volume up")
        assert self.runtime.state == RuntimeState.IDLE

    def test_process_empty_audio_resets_to_idle(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime._process_audio(np.array([], dtype=np.float32))
        assert self.runtime.state == RuntimeState.IDLE
        self.runtime.engine.transcribe_audio.assert_not_called()

    def test_cancel_dictation_aborts_and_discards(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.ducker = MagicMock()
        self.runtime.streaming = MagicMock()
        self.runtime.overlay = MagicMock()
        self.runtime.recorder = MagicMock()

        self.runtime.cancel_dictation()

        assert self.runtime.state == RuntimeState.IDLE
        self.runtime.recorder.stop_recording.assert_called_once()
        self.runtime.ducker.restore.assert_called_once()
        self.runtime.streaming.stop.assert_called_once()
        self.runtime.overlay.hide.assert_called_once()
        self.runtime.engine.transcribe_audio.assert_not_called()

    def test_cancel_when_idle_is_noop(self):
        self.runtime.state = RuntimeState.IDLE
        self.runtime.recorder = MagicMock()
        self.runtime.cancel_dictation()
        self.runtime.recorder.stop_recording.assert_not_called()

    def test_repeated_stop_partials_schedule_only_one_stop(self):
        from kural.engine.stop_phrase import StopPhraseMatcher

        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.recording_mode = "toggle"
        self.runtime.stop_phrase_matcher = StopPhraseMatcher(enabled=True)
        with patch("kural.runtime.threading.Thread") as worker:
            self.runtime._on_live_partial("notes stop dictation")
            self.runtime._on_live_partial("notes stop dictation!")
            worker.assert_called_once()
            worker.return_value.start.assert_called_once()
            assert self.runtime._stop_phrase_detected is True

    def test_stop_phrase_state_cleared_on_empty_or_no_speech(self):
        self.runtime._stop_phrase_detected = True
        self.runtime.state = RuntimeState.PROCESSING
        self.runtime._process_audio(np.array([], dtype=np.float32))
        assert self.runtime._stop_phrase_detected is False

        self.runtime._stop_phrase_detected = True
        self.runtime.state = RuntimeState.PROCESSING
        self.runtime.engine.transcribe_audio.return_value = None
        self.runtime._process_audio(np.zeros(16000, dtype=np.float32))
        assert self.runtime._stop_phrase_detected is False
        self.runtime.toggle_dictation()
        assert self.runtime._stop_phrase_detected is False

    def test_cancel_clears_stop_phrase_state(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime._stop_phrase_detected = True
        self.runtime.cancel_dictation()
        assert self.runtime._stop_phrase_detected is False

    def test_detected_stop_phrase_is_stripped_from_final_transcript(self):
        from kural.engine.stop_phrase import StopPhraseMatcher

        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime._stop_phrase_detected = True
        self.runtime.stop_phrase_matcher = StopPhraseMatcher(enabled=True)
        self.runtime.engine.transcribe_audio.return_value = "I will be there. Stop dictation."
        with patch("kural.runtime.insert_text_at_caret", return_value=True) as insert:
            self.runtime._process_audio(np.zeros(16000, dtype=np.float32))
            assert insert.call_args.args[0] == "I will be there."
            assert self.runtime._stop_phrase_detected is False

    def test_partial_stop_mismatch_preserves_final_transcript(self):
        from kural.engine.stop_phrase import StopPhraseMatcher

        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime._stop_phrase_detected = True
        self.runtime.stop_phrase_matcher = StopPhraseMatcher(enabled=True)
        self.runtime.engine.transcribe_audio.return_value = "I will stop dictation tomorrow"
        with patch("kural.runtime.insert_text_at_caret", return_value=True) as insert:
            self.runtime._process_audio(np.zeros(16000, dtype=np.float32))
            assert insert.call_args.args[0] == "I will stop dictation tomorrow."
            assert self.runtime._stop_phrase_detected is False

    def test_stop_phrase_triggers_auto_stop_and_strips_phrase(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.recording_mode = "toggle"
        from kural.engine.stop_phrase import StopPhraseMatcher

        self.runtime.stop_phrase_matcher = StopPhraseMatcher(enabled=True)
        self.runtime._stop_capture_if_current = MagicMock()

        # Feed partial text ending with "stop dictation"
        self.runtime._on_live_partial("Let's wrap up this work stop dictation")

        assert self.runtime._stop_phrase_detected is True
        # Verify background stop trigger thread was scheduled
        import time

        time.sleep(0.05)
        self.runtime._stop_capture_if_current.assert_called_once_with(0)

    def test_stale_stop_request_does_not_stop_next_capture(self):
        old_generation = self.runtime._capture_generation
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.cancel_dictation()
        self.runtime.toggle_dictation()
        with patch.object(self.runtime, "_finish_recording") as finish:
            self.runtime._stop_capture_if_current(old_generation)
            assert self.runtime.state == RuntimeState.RECORDING_DICTATION
            finish.assert_not_called()

    def test_push_to_talk_release_stops_recording(self):
        self.runtime.recording_mode = "push_to_talk"
        self.runtime.state = RuntimeState.RECORDING_DICTATION

        with patch.object(self.runtime, "_finish_recording"):
            self.runtime.on_dictation_release()
            assert self.runtime.state == RuntimeState.PROCESSING

    def test_double_tap_locks_hands_free(self):
        self.runtime.double_tap_to_lock = True
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        import time

        self.runtime._last_dict_press_time = time.time()

        # Second press within 450ms
        self.runtime.toggle_dictation()
        assert self.runtime._hands_free_locked is True
        # State stays recording
        assert self.runtime.state == RuntimeState.RECORDING_DICTATION

    def test_incognito_mode_prevents_history_and_learning(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.engine.transcribe_audio.return_value = "secret dictation"
        self.runtime.last_take = MagicMock()
        self.runtime.adaptive = MagicMock()
        self.runtime.adaptive.apply_corrections.side_effect = lambda t: t

        self.runtime.toggle_incognito()
        assert self.runtime.incognito is True
        self.runtime.last_take.clear.assert_called_once()

        with (
            patch("kural.runtime.insert_text_at_caret"),
            patch("kural.engine.history.append_history") as mock_append_history,
        ):
            fake_audio = np.zeros(16000, dtype=np.float32)
            self.runtime._process_audio(fake_audio)
            # In incognito mode, history is NOT saved and adaptive learner is NOT called
            mock_append_history.assert_not_called()
            self.runtime.adaptive.learn_text.assert_not_called()
            self.runtime.last_take.save.assert_not_called()

    def test_paste_last_invokes_insert_with_ledger_text(self):
        import time

        self.runtime.ledger = MagicMock()
        self.runtime.ledger.last.return_value = "previously dictated sentence"

        with patch("kural.runtime.insert_text_at_caret") as mock_insert:
            self.runtime.paste_last()
            time.sleep(0.35)  # Wait for 0.25s thread delay
            mock_insert.assert_called_once_with("previously dictated sentence")

    def test_retry_last_reruns_cached_audio(self):
        import time

        self.runtime.last_take = MagicMock()
        fake_audio = np.zeros(16000, dtype=np.float32)
        self.runtime.last_take.load.return_value = (fake_audio, {"task": "transcribe"})

        with patch.object(self.runtime, "_process_audio") as mock_proc:
            self.runtime.retry_last()
            time.sleep(0.35)  # Wait for 0.25s thread delay
            mock_proc.assert_called_once()
            assert np.array_equal(mock_proc.call_args[0][0], fake_audio)
