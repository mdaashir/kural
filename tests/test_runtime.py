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

        with patch("kural.runtime.insert_text_at_caret") as mock_insert:
            fake_audio = np.zeros(16000, dtype=np.float32)
            self.runtime._process_audio(fake_audio)
            # Default style is formal (capitalized + trailing period)
            mock_insert.assert_called_once_with("Hello world.")
            assert self.runtime.state == RuntimeState.IDLE

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
