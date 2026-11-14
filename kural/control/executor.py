# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported from ROHITCRAFTSYT/WhispLocal/whisp/commands.py
"""Central command executor implementing the Kural voice-control resolution hierarchy."""

import logging
import subprocess
import urllib.parse
import webbrowser
from dataclasses import dataclass
from pathlib import Path

from kural.config.defaults_merge import load_layered
from kural.control.app_index import AppIndex
from kural.control.guardrails import Guardrails, default_guardrails
from kural.control.llm_fallback import LocalLLMFallback
from kural.control.media import (
    change_volume,
    media_next,
    media_play_pause,
    media_prev,
    set_volume,
    toggle_mute,
)
from kural.control.parser import CommandIntent, parse_command
from kural.control.windows import close_window, focus_window, set_window_state
from kural.engine.utils import get_user_app_data_path

logger = logging.getLogger(__name__)

CREATE_NO_WINDOW = 0x08000000


@dataclass
class CommandResult:
    """The result of executing a voice command."""

    success: bool
    feedback: str
    action_type: str = "none"


class CommandExecutor:
    """Coordinates command resolution and execution across all voice-control subsystems."""

    def __init__(
        self,
        app_index: AppIndex | None = None,
        guardrails: Guardrails | None = None,
        commands_yaml_path: Path | str | None = None,
        llm_fallback: LocalLLMFallback | None = None,
    ):
        self.app_index = app_index or AppIndex(auto_build=True)
        self.guardrails = guardrails or default_guardrails
        self.llm_fallback = llm_fallback or LocalLLMFallback()

        if commands_yaml_path is None:
            self.commands_yaml_path = Path(get_user_app_data_path()) / "commands.yaml"
        else:
            self.commands_yaml_path = Path(commands_yaml_path)

        self._user_commands = self._load_user_commands()

    def _load_user_commands(self) -> list[dict]:
        """Load user-defined and default commands from commands.yaml."""
        try:
            merged, _ = load_layered(
                defaults_filename="commands.defaults.yaml",
                user_path=self.commands_yaml_path,
                section="commands",
                header="# Kural Voice Commands\n",
                id_key="trigger",
            )
            # Sort longest triggers first for priority matching
            return sorted(
                [c for c in merged if isinstance(c, dict) and "trigger" in c],
                key=lambda x: len(str(x.get("trigger", ""))),
                reverse=True,
            )
        except Exception as e:
            logger.warning(f"Could not load commands.yaml: {e}")
            return []

    def execute(self, phrase: str) -> CommandResult:
        """Resolve and execute a spoken command following the resolution hierarchy:

        1. User commands.yaml exact trigger match
        2. Guardrails validation
        3. Built-in intent parser
        4. App index fuzzy match
        5. Not understood feedback
        """
        clean = (phrase or "").strip()
        if not clean:
            return CommandResult(success=False, feedback="Empty command phrase", action_type="none")

        # Tier 1: User commands.yaml exact substring match
        p_lower = clean.lower()
        for cmd in self._user_commands:
            trigger = str(cmd.get("trigger", "")).strip().lower()
            if trigger and trigger in p_lower:
                return self._execute_yaml_command(cmd, clean)

        # Tier 2: Safety guardrails validation
        safe, block_reason = self.guardrails.check_command_safety(clean)
        if not safe:
            return CommandResult(success=False, feedback=block_reason, action_type="blocked")

        # Tier 3: Built-in intent parser
        intent = parse_command(clean)
        if intent:
            return self._execute_intent(intent)

        # Tier 4: Direct app name match in app_index (e.g. user just said "calculator")
        app_match = self.app_index.find_app(clean)
        if app_match:
            target, name = app_match
            # If already open, switch to it
            focused_title = focus_window(name)
            if focused_title:
                return CommandResult(
                    success=True, feedback=f"Switched to {focused_title}", action_type="switch_app"
                )
            launched = self.app_index.launch(target)
            return CommandResult(
                success=launched,
                feedback=f"Opening {name.title()}" if launched else f"Failed to launch {name}",
                action_type="open_app",
            )

        # Tier 5: Optional Local-LLM fallback (if enabled and configured)
        if self.llm_fallback.is_available():
            canonical = self.llm_fallback.resolve_command(clean)
            if canonical:
                safe, reason = self.guardrails.check_command_safety(canonical)
                if safe:
                    intent = parse_command(canonical)
                    if intent:
                        logger.info(f"Local LLM resolved '{clean}' -> '{canonical}'")
                        return self._execute_intent(intent)

        # Tier 6: Fallback — not understood
        return CommandResult(
            success=False,
            feedback=f"Command not understood: '{clean}'",
            action_type="unrecognized",
        )

    def _execute_yaml_command(self, cmd: dict, raw_text: str) -> CommandResult:
        """Execute a matched command from commands.yaml."""
        trigger = cmd.get("trigger", "")

        # Shell run command
        if "run" in cmd:
            run_cmd = cmd["run"]
            # Guardrails check on the target shell command
            safe, reason = self.guardrails.check_command_safety(run_cmd)
            if not safe:
                return CommandResult(success=False, feedback=reason, action_type="blocked")

            try:
                subprocess.Popen(run_cmd, shell=True, creationflags=CREATE_NO_WINDOW)
                return CommandResult(
                    success=True, feedback=f"Running: {trigger}", action_type="yaml_run"
                )
            except Exception as e:
                return CommandResult(
                    success=False, feedback=f"Failed to run: {e}", action_type="yaml_run"
                )

        # Hotkey simulation command
        if "hotkey" in cmd:
            return CommandResult(
                success=True, feedback=f"Shortcut: {cmd['hotkey']}", action_type="yaml_hotkey"
            )

        # Type text command
        if "type" in cmd:
            return CommandResult(
                success=True, feedback=f"Typed: {cmd['type']}", action_type="yaml_type"
            )

        return CommandResult(
            success=False,
            feedback=f"No action defined for trigger '{trigger}'",
            action_type="yaml_none",
        )

    def _execute_intent(self, intent: CommandIntent) -> CommandResult:
        """Execute a parsed CommandIntent."""
        # Media controls
        if intent.kind == "media":
            if intent.action == "play_pause":
                media_play_pause()
                return CommandResult(success=True, feedback="Play / Pause", action_type="media")
            if intent.action == "next":
                media_next()
                return CommandResult(success=True, feedback="Next track", action_type="media")
            if intent.action == "prev":
                media_prev()
                return CommandResult(success=True, feedback="Previous track", action_type="media")
            if intent.action == "mute":
                toggle_mute()
                return CommandResult(success=True, feedback="Mute toggled", action_type="media")

        # Volume controls
        if intent.kind == "volume":
            if intent.action == "up":
                lvl = change_volume(10)
                return CommandResult(
                    success=True, feedback=f"Volume set to {lvl}%", action_type="volume"
                )
            if intent.action == "down":
                lvl = change_volume(-10)
                return CommandResult(
                    success=True, feedback=f"Volume set to {lvl}%", action_type="volume"
                )
            if intent.action == "set":
                lvl = set_volume(int(intent.target))
                return CommandResult(
                    success=True, feedback=f"Volume set to {lvl}%", action_type="volume"
                )

        # Window operations
        if intent.kind == "window_op":
            ok, msg = set_window_state(intent.action)
            return CommandResult(success=ok, feedback=msg, action_type="window_op")

        # Window switching
        if intent.kind == "switch_app":
            title = focus_window(intent.target)
            if title:
                return CommandResult(
                    success=True, feedback=f"Switched to {title}", action_type="switch_app"
                )
            return CommandResult(
                success=False,
                feedback=f"No open window matching '{intent.target}'",
                action_type="switch_app",
            )

        # Window closing
        if intent.kind == "close_app":
            ok, msg = close_window(intent.target)
            return CommandResult(success=ok, feedback=msg, action_type="close_app")

        # App opening
        if intent.kind == "open_app":
            # If already open, switch to it
            focused = focus_window(intent.target)
            if focused:
                return CommandResult(
                    success=True, feedback=f"Switched to {focused}", action_type="open_app"
                )

            match = self.app_index.find_app(intent.target)
            if match:
                target, resolved_name = match
                launched = self.app_index.launch(target)
                return CommandResult(
                    success=launched,
                    feedback=f"Opening {resolved_name.title()}",
                    action_type="open_app",
                )
            # Fall back to web search
            ok, msg = self.app_index.open_web(intent.target)
            return CommandResult(success=ok, feedback=msg, action_type="web_fallback")

        # Web search
        if intent.kind == "web_search":
            if intent.action == "youtube":
                q = urllib.parse.quote_plus(intent.target)
                webbrowser.open(f"https://www.youtube.com/results?search_query={q}")
                return CommandResult(
                    success=True,
                    feedback=f"Searching YouTube for '{intent.target}'",
                    action_type="web_search",
                )
            q = urllib.parse.quote_plus(intent.target)
            webbrowser.open(f"https://www.google.com/search?q={q}")
            return CommandResult(
                success=True, feedback=f"Searching for '{intent.target}'", action_type="web_search"
            )

        # System power
        if intent.kind == "system":
            if intent.action == "shutdown":
                ok, msg = self.guardrails.schedule_shutdown(restart=False)
                return CommandResult(success=ok, feedback=msg, action_type="system")
            if intent.action == "restart":
                ok, msg = self.guardrails.schedule_shutdown(restart=True)
                return CommandResult(success=ok, feedback=msg, action_type="system")
            if intent.action == "cancel_shutdown":
                ok, msg = self.guardrails.cancel_shutdown()
                return CommandResult(success=ok, feedback=msg, action_type="system")

        return CommandResult(
            success=False, feedback=f"Unhandled action: {intent.action}", action_type="unhandled"
        )
