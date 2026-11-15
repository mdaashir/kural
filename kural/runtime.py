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

        from kural.engine.audio_recorder import AudioRecorder

        self.recorder = AudioRecorder(
            on_vad_event=self._on_vad_event,
            max_duration=int(self.config_manager.get_audio_config().get("max_duration", 30)),
            on_max_duration_reached=self._on_max_duration,
            vad_manager=self.vad_manager,
        )

        # Recovery, adaptive learning, and app rules
        from kural.control.app_rules import AppRules
        from kural.engine.adaptive import AdaptiveLearner
        from kural.engine.recovery import LastTake, Ledger
        from kural.engine.utils import get_user_app_data_path

        recovery_cfg = self.config_manager.config.get("recovery") or {}
        max_age_s = float(recovery_cfg.get("max_age_hours", 24)) * 3600
        self.last_take = LastTake(storage_dir=get_user_app_data_path(), max_age_s=max_age_s)
        self.ledger = Ledger()
        self.app_rules = AppRules()
        self.adaptive = AdaptiveLearner()

        # Command execution brain with ledger
        self.executor = CommandExecutor(ledger=self.ledger)

        # Audible feedback cues
        from kural.engine.audio_feedback import AudioFeedback

        audio_fb_cfg = self.config_manager.config.get("audio_feedback") or {}
        self.audio_feedback = AudioFeedback(
            enabled=bool(audio_fb_cfg.get("enabled", True)),
            start_sound=audio_fb_cfg.get("start_sound", ""),
            stop_sound=audio_fb_cfg.get("stop_sound", ""),
            complete_sound=audio_fb_cfg.get("complete_sound", ""),
            error_sound=audio_fb_cfg.get("error_sound", ""),
        )

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
            on_open_history=self.open_history,
            on_open_cheat_sheet=self.open_cheat_sheet,
            on_open_settings=self.open_settings,
            on_exit=self.request_exit,
            enabled=bool(tray_cfg.get("enabled", True)),
        )

    def open_history(self) -> None:
        """Launch the graphical speech & command history window."""
        from kural.ui.history_window import open_history_window

        open_history_window()

    def open_cheat_sheet(self) -> None:
        """Launch the shortcuts and commands cheat sheet reference window."""
        from kural.ui.cheat_sheet import open_cheat_sheet

        open_cheat_sheet(config_manager=self.config_manager)

    def open_settings(self) -> None:
        """Launch the graphical settings window."""
        from kural.ui.settings_window import open_settings_window

        open_settings_window(config_manager=self.config_manager)

    def _current_mic_level(self) -> float:
        """Return the current microphone input level (0.0 - 1.0) for the overlay meter."""
        rec = getattr(self, "recorder", None)
        try:
            return float(rec.get_current_level() if rec else 0.0)
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
                self.audio_feedback.play_start()
                print("\n🎙️  Listening (Dictation Mode)...")
            elif self.state == RuntimeState.RECORDING_DICTATION:
                self.state = RuntimeState.PROCESSING
                self.overlay.show_processing()
                self.audio_feedback.play_stop()
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
                self.audio_feedback.play_start()
                print("\n⚡ Listening (Command Mode)...")
            elif self.state == RuntimeState.RECORDING_COMMAND:
                self.state = RuntimeState.PROCESSING
                self.overlay.show_processing()
                self.audio_feedback.play_stop()
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

            if getattr(self, "last_take", None):
                self.last_take.save(audio_data)

            prior_state = self.state
            print("⏳ Transcribing on GPU...")
            text = self.engine.transcribe_audio(audio_data)
            if not text:
                self.audio_feedback.play_error()
                return

            if prior_state == RuntimeState.RECORDING_COMMAND:
                print(f"👉 Command: '{text}'")
                res = self.executor.execute(text)
                status_icon = "✓" if res.success else "✗"
                print(f"   {status_icon} {res.feedback}")

                from kural.engine.history import HistoryEntry, append_history

                append_history(
                    HistoryEntry(
                        text=text,
                        task="command",
                        audio_s=float(len(audio_data) / 16000.0),
                    )
                )

                if res.action_type == "retry_take" and getattr(self, "last_take", None):
                    cached, _ = self.last_take.load()
                    if cached is not None:
                        self.state = RuntimeState.RECORDING_DICTATION
                        self._process_audio(cached)
                        return
                if res.success:
                    self.overlay.flash_success(res.feedback[:40])
                    self.audio_feedback.play_complete()
                else:
                    self.overlay.flash_error(res.feedback[:40])
                    self.audio_feedback.play_error()
            else:
                from kural.control.app_rules import apply_formatting_style
                from kural.control.windows import get_foreground_window_info
                from kural.engine.history import HistoryEntry, append_history
                from kural.engine.snippets import apply_snippets

                # 1. Match foreground app rule
                fg_info = get_foreground_window_info()
                matched_rule = (
                    self.app_rules.match_rule(
                        exe=fg_info.exe if fg_info else "",
                        title=fg_info.title if fg_info else "",
                    )
                    if fg_info
                    else None
                )

                # 2. Check if delivery is suppressed (e.g. password managers)
                if matched_rule and matched_rule.get("suppress", False):
                    print(f"🔒 Delivery suppressed by app rule ({matched_rule.get('id', 'rule')})")
                    self.overlay.flash_error("Suppressed (Password Field)")
                    self.audio_feedback.play_error()
                    return

                # 3. Apply learned corrections and style formatting
                if getattr(self, "adaptive", None):
                    text = self.adaptive.apply_corrections(text)

                style_name = (matched_rule.get("style") if matched_rule else None) or "formal"
                text = apply_formatting_style(text, style_name)

                # 4. Expand inline text snippets
                snippets_cfg = self.config_manager.get_postprocess_config().get("snippets") or []
                text = apply_snippets(text, snippets_cfg)

                print(f"✍️  Typed ({style_name}): '{text}'")
                insert_text_at_caret(text)

                # 5. Record to ledger, adaptive learner, and history.jsonl
                if getattr(self, "ledger", None):
                    self.ledger.record(text)
                if getattr(self, "adaptive", None):
                    self.adaptive.learn_text(text)

                append_history(
                    HistoryEntry(
                        text=text,
                        task="transcribe",
                        audio_s=float(len(audio_data) / 16000.0),
                        app=fg_info.exe if fg_info else "",
                    )
                )

                self.overlay.flash_success("Typed")
                self.audio_feedback.play_complete()

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
        for c in (
            getattr(self.overlay, "stop", None),
            getattr(self.tray, "stop", None),
            getattr(self.recorder, "shutdown", None),
            getattr(self.engine, "_cancel_idle_timer", None),
        ):
            if c:
                with contextlib.suppress(Exception):
                    c()
        with contextlib.suppress(Exception):
            import global_hotkeys

            global_hotkeys.stop_checking_hotkeys()
