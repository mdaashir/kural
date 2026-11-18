"""Tests for kural.runtime — state transitions, processing, and insertion with mocks."""

from unittest.mock import MagicMock, patch

import numpy as np

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

    def test_stop_phrase_triggers_auto_stop_and_strips_phrase(self):
        self.runtime.state = RuntimeState.RECORDING_DICTATION
        self.runtime.recording_mode = "toggle"
        from kural.engine.stop_phrase import StopPhraseMatcher

        self.runtime.stop_phrase_matcher = StopPhraseMatcher(enabled=True)
        self.runtime.stop_and_process = MagicMock()

        # Feed partial text ending with "stop dictation"
        self.runtime._on_live_partial("Let's wrap up this work stop dictation")

        assert self.runtime._stop_phrase_detected is True
        # Verify background stop trigger thread was scheduled
        import time

        time.sleep(0.05)
        self.runtime.stop_and_process.assert_called_once()

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
