# MIT License — Copyright (c) 2025 drajb & Rohit Burani
# Designed and implemented for Kural
"""Live runtime event loop and hotkey controller for Kural.

Manages recording state machine (IDLE <-> RECORDING <-> PROCESSING), global hotkey
bindings (Ctrl+Space for dictation, Ctrl+Shift+Space for commands), audio capture,
GPU inference with faster-whisper, caret insertion, and command execution.
"""

import contextlib
import logging
import threading
import time
from enum import Enum

import numpy as np

from kural.config import ConfigManager
from kural.control.executor import CommandExecutor
from kural.control.windows import insert_text_at_caret
from kural.engine.utils import beautify_hotkey, get_version

logger = logging.getLogger("kural.runtime")


class RuntimeState(Enum):
    IDLE = "idle"
    RECORDING_DICTATION = "recording_dictation"
    RECORDING_COMMAND = "recording_command"
    PROCESSING = "processing"


class KuralRuntime:
    """Central daemon coordinating global hotkeys, audio capture, transcription, and action."""

    def __init__(self, config_manager: ConfigManager | None = None):
        self.config_manager = config_manager or ConfigManager(quiet=True)
        self.state = RuntimeState.IDLE
        self._state_lock = threading.Lock()
        self._running = False

        # Load configurations
        self.whisper_cfg = self.config_manager.get_whisper_config()
        self.hotkey_cfg = self.config_manager.get_hotkey_config()
        self.vad_cfg = self.config_manager.get_vad_config()

        # Voice activity detector (lazy import)
        from kural.engine.voice_activity_detection import VadEvent, VadManager

        self._vad_event_cls = VadEvent
        self.vad_manager = VadManager(
            vad_precheck_enabled=self.vad_cfg.get("precheck_enabled", True),
            vad_realtime_enabled=self.vad_cfg.get("realtime_enabled", False),
            vad_onset_threshold=float(self.vad_cfg.get("vad_onset_threshold", 0.7)),
            vad_offset_threshold=float(self.vad_cfg.get("vad_offset_threshold", 0.55)),
            vad_min_speech_duration=float(self.vad_cfg.get("vad_min_speech_duration", 0.1)),
            vad_silence_timeout_seconds=float(
                self.vad_cfg.get("vad_silence_timeout_seconds", 20.0)
            ),
        )

        # Whisper engine targeting RTX 3050 CUDA float16 with idle unload
        from kural.engine.whisper_engine import WhisperEngine

        self.engine = WhisperEngine(
            model_key=self.whisper_cfg.get("model", "large-v3-turbo"),
            device=self.whisper_cfg.get("device", "cuda"),
            compute_type=self.whisper_cfg.get("compute_type", "float16"),
            language=self.whisper_cfg.get("language", "en"),
            beam_size=int(self.whisper_cfg.get("beam_size", 5)),
            initial_prompt=self.whisper_cfg.get("initial_prompt", ""),
            vad_manager=self.vad_manager,
            idle_unload_minutes=int(self.whisper_cfg.get("idle_unload_minutes", 5)),
            languages=self.whisper_cfg.get("languages", ["en", "ta"]),
        )

        # Audio capture stream (lazy import)
        from kural.engine.audio_recorder import AudioRecorder

        self.recorder = AudioRecorder(
            on_vad_event=self._on_vad_event,
            max_duration=int(self.config_manager.get_audio_config().get("max_duration", 30)),
            on_max_duration_reached=self._on_max_duration,
            vad_manager=self.vad_manager,
        )

        # Command execution brain
        self.executor = CommandExecutor()

        # Visual overlay (Tkinter pill) and optional system tray
        from kural.ui.overlay import LevelOverlay
        from kural.ui.tray import SystemTray

        overlay_cfg = self.config_manager.config.get("overlay") or {}
        self.overlay = LevelOverlay(
            level_provider=self._current_mic_level,
            position=overlay_cfg.get("position", "bottom-center"),
            click_through=bool(overlay_cfg.get("click_through", True)),
            enabled=bool(overlay_cfg.get("enabled", True)),
        )

        tray_cfg = self.config_manager.config.get("system_tray") or {}
        self.tray = SystemTray(
            on_toggle_dictation=self.toggle_dictation,
            on_toggle_command=self.toggle_command,
            on_exit=self.request_exit,
            enabled=bool(tray_cfg.get("enabled", True)),
        )

    def _current_mic_level(self) -> float:
        """Return the current microphone input level (0.0 - 1.0) for the overlay meter."""
        recorder = getattr(self, "recorder", None)
        if recorder is None:
            return 0.0
        getter = getattr(recorder, "get_current_level", None)
        if getter is None:
            return 0.0
        try:
            return float(getter() or 0.0)
        except Exception:
            return 0.0

    def request_exit(self) -> None:
        """Request the runtime loop to stop (used by the tray Exit menu item)."""
        self._running = False

    def _on_vad_event(self, event) -> None:
        """Handle silence timeout from continuous VAD."""
        if getattr(event, "name", "") == "SILENCE_TIMEOUT":
            logger.info("VAD detected prolonged silence, auto-stopping recording")
            self.stop_and_process()

    def _on_max_duration(self, audio_data: np.ndarray) -> None:
        """Handle max duration reached."""
        self._process_audio(audio_data)

    def toggle_dictation(self) -> None:
        """Toggle dictation recording state on hotkey press."""
        with self._state_lock:
            if self.state == RuntimeState.IDLE:
                self.state = RuntimeState.RECORDING_DICTATION
                self.recorder.start_recording()
                self.overlay.show_recording(is_command=False)
                print("\n🎙️  Listening (Dictation Mode)...")
            elif self.state == RuntimeState.RECORDING_DICTATION:
                self.state = RuntimeState.PROCESSING
                self.overlay.show_processing()
                threading.Thread(
                    target=self._finish_recording, daemon=True, name="finish-dictation"
                ).start()

    def toggle_command(self) -> None:
        """Toggle voice-control command recording state on hotkey press."""
        with self._state_lock:
            if self.state == RuntimeState.IDLE:
                self.state = RuntimeState.RECORDING_COMMAND
                self.recorder.start_recording()
                self.overlay.show_recording(is_command=True)
                print("\n⚡ Listening (Command Mode)...")
            elif self.state == RuntimeState.RECORDING_COMMAND:
                self.state = RuntimeState.PROCESSING
                self.overlay.show_processing()
                threading.Thread(
                    target=self._finish_recording, daemon=True, name="finish-command"
                ).start()

    def stop_and_process(self) -> None:
        """Stop any active recording and process audio."""
        with self._state_lock:
            if self.state in (RuntimeState.RECORDING_DICTATION, RuntimeState.RECORDING_COMMAND):
                self.state = RuntimeState.PROCESSING
                threading.Thread(
                    target=self._finish_recording, daemon=True, name="finish-recording"
                ).start()

    def _finish_recording(self) -> None:
        audio_data = self.recorder.stop_recording()
        self._process_audio(audio_data)

    def _process_audio(self, audio_data: np.ndarray | None) -> None:
        try:
            if audio_data is None or len(audio_data) == 0:
                print("   ✗ No audio data captured.")
                return

            prior_state = self.state
            print("⏳ Transcribing on GPU...")
            text = self.engine.transcribe_audio(audio_data)
            if not text:
                return

            if prior_state == RuntimeState.RECORDING_COMMAND:
                print(f"👉 Command: '{text}'")
                res = self.executor.execute(text)
                status_icon = "✓" if res.success else "✗"
                print(f"   {status_icon} {res.feedback}")
                if res.success:
                    self.overlay.flash_success(res.feedback[:40])
                else:
                    self.overlay.flash_error(res.feedback[:40])
            else:
                print(f"✍️  Typed: '{text}'")
                insert_text_at_caret(text)
                self.overlay.flash_success("Typed")

        finally:
            with self._state_lock:
                self.state = RuntimeState.IDLE

    def start_hotkeys(self) -> bool:
        """Register global Windows hotkeys."""
        try:
            import global_hotkeys

            dict_key = self.hotkey_cfg.get("recording_hotkey", "ctrl+space")
            cmd_key = self.hotkey_cfg.get("command_hotkey", "ctrl+shift+space")

            # Parse hotkey strings to global_hotkeys format
            def _to_bindings(hk_str: str):
                return hk_str.lower().split("+")

            bindings = [
                [_to_bindings(dict_key), None, self.toggle_dictation],
                [_to_bindings(cmd_key), None, self.toggle_command],
            ]

            global_hotkeys.register_hotkeys(bindings)
            global_hotkeys.start_checking_hotkeys()
            logger.info("Global hotkeys registered successfully")
            return True
        except Exception as e:
            logger.warning(f"Could not bind global hotkeys: {e}")
            return False

    def run(self) -> None:
        """Run the main daemon loop."""
        self._running = True
        dict_hk = beautify_hotkey(self.hotkey_cfg.get("recording_hotkey", "ctrl+space"))
        cmd_hk = beautify_hotkey(self.hotkey_cfg.get("command_hotkey", "ctrl+shift+space"))

        print("\n=======================================================")
        print(f"   Kural {get_version()} — Ready")
        print("=======================================================")
        print(f"   [{dict_hk}]  Dictation Mode (speech -> active cursor)")
        print(f"   [{cmd_hk}]  Command Mode (voice control)")
        print(f"   Model: {self.whisper_cfg.get('model')} ({self.whisper_cfg.get('device')})")
        print("   Press Ctrl+C to exit.\n")

        self.start_hotkeys()
        self.overlay.start()
        self.tray.start()

        try:
            while self._running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nShutting down Kural...")
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Clean up audio streams, timers, and exit."""
        self._running = False
        with contextlib.suppress(Exception):
            self.overlay.stop()
        with contextlib.suppress(Exception):
            self.tray.stop()
        with contextlib.suppress(Exception):
            self.recorder.shutdown()
        with contextlib.suppress(Exception):
            self.engine._cancel_idle_timer()
        with contextlib.suppress(Exception):
            import global_hotkeys

            global_hotkeys.stop_checking_hotkeys()
