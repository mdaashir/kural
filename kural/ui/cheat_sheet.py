# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/cheat_sheet.py
"""Hotkeys and voice-commands cheat sheet dialog (Tkinter) for Kural.

Provides a clean quick-reference card displaying the user's active hotkeys,
voice command trigger patterns (English and Tamil), and inline snippet expansions.
Dynamically reads the live configuration.
"""

import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)

_thread_lock = threading.Lock()
_current_root: Any = None


class CheatSheetWindow:
    """Tkinter-based quick-reference cheat sheet."""

    WIDTH = 680
    HEIGHT = 560

    def __init__(self, config_manager: Any = None):
        self.config_manager = config_manager
        self.root: Any = None

    def _get_hotkey_items(self) -> list[tuple[str, str, str]]:
        if self.config_manager is None:
            try:
                from kural.config import ConfigManager

                self.config_manager = ConfigManager(quiet=True)
            except Exception:
                pass

        hk = (
            self.config_manager.get_hotkey_config()
            if self.config_manager
            else {
                "recording_hotkey": "ctrl+space",
                "command_hotkey": "ctrl+shift+space",
            }
        )

        return [
            (
                "Dictation Mode",
                hk.get("recording_hotkey", "ctrl+space").upper(),
                "Press to start speaking; press again to finish and type at cursor.",
            ),
            (
                "Voice Command Mode",
                hk.get("command_hotkey", "ctrl+shift+space").upper(),
                "Speak an app or control command (English or Tamil).",
            ),
        ]

    def _get_voice_commands(self) -> list[tuple[str, str, str]]:
        return [
            ("Open / Switch App", "open chrome  •  திற chrome", "Launch or focus an application"),
            (
                "Close Application",
                "close notepad  •  notepad மூடு",
                "Gracefully terminate application",
            ),
            (
                "Volume & Media",
                "volume up  •  play / pause",
                "Control system master volume & media playback",
            ),
            (
                "Window Management",
                "minimize  •  maximize  •  snap left",
                "Reposition or size active window",
            ),
            (
                "Take Recovery",
                "paste last  •  retry last take",
                "Re-paste previous take or re-transcribe",
            ),
        ]

    def _get_snippets(self) -> list[tuple[str, str, str]]:
        return [
            ("Date Stamp", "today's date", "Inserts current YYYY-MM-DD"),
            ("Time Stamp", "current time", "Inserts current HH:MM"),
            (
                "Clipboard Paste",
                "insert clipboard",
                "Pastes active clipboard text inside dictation",
            ),
        ]

    def show(self) -> None:
        """Build and run the cheat sheet window."""
        global _current_root
        import tkinter as tk
        from tkinter import ttk

        with _thread_lock:
            try:
                if _current_root and _current_root.winfo_exists():
                    _current_root.lift()
                    _current_root.focus_force()
                    return
            except Exception:
                pass

        root = tk.Tk()
        with _thread_lock:
            _current_root = root

        def _clear_ref():
            global _current_root
            with _thread_lock:
                _current_root = None
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", _clear_ref)
        root.title("Kural — Shortcuts & Commands Reference")
        root.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        root.minsize(580, 480)
        root.configure(bg="#0d1117")
        self.root = root

        # Outer canvas with scrollbar for clean layout
        canvas = tk.Canvas(root, bg="#0d1117", highlightthickness=0)
        scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#0d1117", padx=24, pady=16)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Header
        header = tk.Frame(scroll_frame, bg="#0d1117")
        header.pack(fill=tk.X, pady=(0, 16))
        tk.Label(
            header,
            text="🎯 Kural Reference & Cheat Sheet",
            bg="#0d1117",
            fg="#f0f6fc",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Active shortcuts and sample commands from your local configuration.",
            bg="#0d1117",
            fg="#8b949e",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(2, 0))

        # Helper to render a section
        def _render_section(title: str, items: list[tuple[str, str, str]]):
            sec_frame = tk.LabelFrame(
                scroll_frame,
                text=f"  {title}  ",
                bg="#161b22",
                fg="#58a6ff",
                font=("Segoe UI", 10, "bold"),
                relief=tk.FLAT,
                bd=1,
                padx=12,
                pady=10,
            )
            sec_frame.pack(fill=tk.X, pady=(0, 14))

            for _row_idx, (action, badge, desc) in enumerate(items):
                row = tk.Frame(sec_frame, bg="#161b22")
                row.pack(fill=tk.X, pady=4)

                # Badge (hotkey or trigger)
                badge_lbl = tk.Label(
                    row,
                    text=f" {badge} ",
                    bg="#21262d",
                    fg="#f0f6fc",
                    font=("Consolas", 9, "bold"),
                    relief=tk.SOLID,
                    bd=1,
                    padx=6,
                    pady=2,
                )
                badge_lbl.pack(side=tk.LEFT, anchor="w")

                # Action name
                name_lbl = tk.Label(
                    row,
                    text=f"•  {action}",
                    bg="#161b22",
                    fg="#c9d1d9",
                    font=("Segoe UI", 9, "bold"),
                    width=22,
                    anchor="w",
                )
                name_lbl.pack(side=tk.LEFT, padx=(10, 8))

                # Description
                desc_lbl = tk.Label(
                    row,
                    text=desc,
                    bg="#161b22",
                    fg="#8b949e",
                    font=("Segoe UI", 9),
                    anchor="w",
                )
                desc_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        _render_section("Global Hotkeys", self._get_hotkey_items())
        _render_section("Voice Control Triggers (EN & Tamil)", self._get_voice_commands())
        _render_section("Inline Voice Snippets", self._get_snippets())

        try:
            root.mainloop()
        finally:
            with _thread_lock:
                _current_root = None


def open_cheat_sheet(
    config_manager: Any = None,
    blocking: bool = False,
) -> None:
    """Launch the cheat sheet window on a background thread, or directly if blocking."""
    win = CheatSheetWindow(config_manager=config_manager)

    if blocking or (threading.current_thread() is threading.main_thread()):
        win.show()
    else:
        t = threading.Thread(target=win.show, daemon=True, name="cheat-sheet-ui")
        t.start()
