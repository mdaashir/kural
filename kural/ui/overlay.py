# MIT License — Copyright (c) 2025 drajb & Rohit Burani
# Ported and adapted from drajb/whisper-local/src/whisper_key/level_overlay.py
"""Floating status pill with dynamic fluid waveform animation (Wispr Flow style).

Displays an always-on-top, click-through pill near the screen edge with:
- Multi-bar animated waveform visualizer reacting smoothly to mic levels and voice frequencies.
- Cyan/Emerald animated wave for Dictation, Violet wave for Voice Command mode.
- Pulsing wave shimmer during GPU transcription.
- Smooth flash animations for success and error feedback.
"""

import contextlib
import logging
import math
import queue
import sys
import threading
from collections.abc import Callable

logger = logging.getLogger(__name__)


class LevelOverlay:
    """Floating visual pill rendering live animated soundwave activity."""

    WIDTH = 240
    HEIGHT = 38
    BG_COLOR = "#0d1117"
    BORDER_COLOR = "#30363d"
    TEXT_COLOR = "#f0f6fc"

    # Theme colors
    DICTATION_COLOR = "#2ea043"  # Emerald / Green wave
    DICTATION_GLOW = "#3fb950"
    COMMAND_COLOR = "#a371f7"  # Electric Purple wave
    COMMAND_GLOW = "#bc8cff"
    PROCESSING_COLOR = "#d29922"  # Amber wave
    LEVEL_COLOR = "#3fb950"
    ERROR_COLOR = "#f85149"

    NUM_BARS = 7

    def __init__(
        self,
        level_provider: Callable[[], float] | None = None,
        position: str = "bottom-center",
        click_through: bool = True,
        enabled: bool = True,
    ):
        self.level_provider = level_provider or (lambda: 0.0)
        self.position = position
        self.click_through = click_through
        self.enabled = enabled

        self._thread = None
        self._command_queue = queue.Queue()
        self._root = None
        self._canvas = None
        self._text_item = None
        self._wave_bars: list[int] = []
        self._bar_heights = [4.0] * self.NUM_BARS
        self._phase = 0.0

        self._mode = "hidden"
        self._running = False
        self._available = self._check_tk()

    def _check_tk(self) -> bool:
        if not self.enabled:
            return False
        try:
            import tkinter  # noqa

            return True
        except Exception as e:
            logger.info(f"Tkinter unavailable ({e}); overlay disabled")
            return False

    def is_available(self) -> bool:
        return self._available

    def start(self) -> None:
        """Start the overlay window loop on a dedicated thread."""
        if not self._available or (self._thread and self._thread.is_alive()):
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_tk_thread, daemon=True, name="level-overlay"
        )
        self._thread.start()

    def show_recording(self, is_command: bool = False) -> None:
        """Show the overlay pill in recording mode."""
        mode = "command" if is_command else "dictation"
        self._dispatch(lambda: self._set_mode(mode))

    def show_processing(self) -> None:
        """Show the overlay pill in transcribing/processing mode."""
        self._dispatch(lambda: self._set_mode("processing"))

    def update_partial_text(self, text: str) -> None:
        """Update the pill label with live partial transcription words."""
        if not text:
            return

        def _update():
            if (
                not self._canvas
                or not self._text_item
                or self._mode not in ("dictation", "command")
            ):
                return
            # Truncate text nicely to fit in pill
            display = text.strip()
            if len(display) > 24:
                display = "..." + display[-22:]
            self._canvas.itemconfig(self._text_item, text=display, fill=self.TEXT_COLOR)

        self._dispatch(_update)

    def flash_success(self, message: str = "Done") -> None:
        """Flash green success status and hide."""
        self._dispatch(lambda: self._flash(self.LEVEL_COLOR, f"✓ {message}"))

    def flash_error(self, message: str = "Error") -> None:
        """Flash red error status and hide."""
        self._dispatch(lambda: self._flash(self.ERROR_COLOR, f"✗ {message}"))

    def hide(self) -> None:
        """Hide the overlay pill."""
        self._dispatch(lambda: self._set_mode("hidden"))

    def stop(self) -> None:
        """Stop the overlay and destroy the window."""
        self._running = False
        self._dispatch(self._destroy_root)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

    def _dispatch(self, action: Callable[[], None]) -> None:
        if not self._available or not self._running:
            return
        self._command_queue.put(action)

    def _run_tk_thread(self) -> None:
        try:
            import tkinter as tk

            root = tk.Tk()
            self._root = root
            root.title("Kural Flow")
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.configure(bg=self.BG_COLOR)

            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()

            x = (screen_w - self.WIDTH) // 2
            y = screen_h - self.HEIGHT - 65 if "bottom" in self.position else 45
            root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

            canvas = tk.Canvas(
                root,
                width=self.WIDTH,
                height=self.HEIGHT,
                bg=self.BG_COLOR,
                highlightthickness=1,
                highlightbackground=self.BORDER_COLOR,
            )
            canvas.pack(fill="both", expand=True)
            self._canvas = canvas

            # Status text label
            self._text_item = canvas.create_text(
                self.WIDTH - 75,
                self.HEIGHT // 2,
                text="Dictating...",
                fill=self.TEXT_COLOR,
                font=("Segoe UI", 9, "bold"),
                anchor="e",
            )

            # Create the 7 waveform vertical bars
            self._wave_bars = []
            bar_w = 4
            spacing = 3
            start_x = 22
            cy = self.HEIGHT // 2

            for i in range(self.NUM_BARS):
                bx = start_x + (i * (bar_w + spacing))
                rect = canvas.create_rectangle(
                    bx,
                    cy - 2,
                    bx + bar_w,
                    cy + 2,
                    fill=self.DICTATION_COLOR,
                    outline="",
                )
                self._wave_bars.append(rect)

            if sys.platform == "win32" and self.click_through:
                self._enable_click_through(root)

            root.withdraw()
            self._poll_commands()
            root.mainloop()
        except Exception as e:
            logger.warning(f"Level overlay loop terminated: {e}")
            self._available = False

    def _enable_click_through(self, root) -> None:
        try:
            import ctypes

            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            GWL_EXSTYLE = -20
            styles = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, styles | 0x20 | 0x80000)
        except Exception as e:
            logger.debug(f"Click-through style skipped: {e}")

    def _poll_commands(self) -> None:
        if not self._running or not self._root:
            return

        while not self._command_queue.empty():
            try:
                cmd = self._command_queue.get_nowait()
                cmd()
            except Exception:
                pass

        if self._canvas:
            self._animate_waveform()

        self._root.after(30, self._poll_commands)

    def _animate_waveform(self) -> None:
        """Render fluid, undulating waveform bars reacting to audio volume and animation phase."""
        if not self._canvas or not self._wave_bars:
            return

        cy = self.HEIGHT // 2
        bar_w = 4
        spacing = 3
        start_x = 22

        if self._mode in ("dictation", "command"):
            raw_lvl = min(1.0, max(0.0, self.level_provider() * 25.0))
            color = self.COMMAND_GLOW if self._mode == "command" else self.DICTATION_GLOW
            self._phase += 0.25

            max_h = 24.0
            for i, rect in enumerate(self._wave_bars):
                # Harmonic wave pattern with audio amplitude scaling
                offset = math.sin(self._phase + (i * 0.8)) * 0.35 + 0.65
                target_h = max(4.0, (raw_lvl * max_h * offset) + (2.0 if raw_lvl > 0.05 else 0.0))
                # Smooth decay
                self._bar_heights[i] += (target_h - self._bar_heights[i]) * 0.4

                h = self._bar_heights[i]
                bx = start_x + (i * (bar_w + spacing))
                self._canvas.coords(rect, bx, cy - (h / 2), bx + bar_w, cy + (h / 2))
                self._canvas.itemconfig(rect, fill=color)

        elif self._mode == "processing":
            self._phase += 0.2
            for i, rect in enumerate(self._wave_bars):
                wave_val = (math.sin(self._phase + (i * 0.7)) + 1.0) / 2.0
                h = 4.0 + (wave_val * 14.0)
                bx = start_x + (i * (bar_w + spacing))
                self._canvas.coords(rect, bx, cy - (h / 2), bx + bar_w, cy + (h / 2))
                self._canvas.itemconfig(rect, fill=self.PROCESSING_COLOR)

    def _set_mode(self, mode: str) -> None:
        self._mode = mode
        if not self._root or not self._canvas:
            return

        if mode == "hidden":
            self._root.withdraw()
        elif mode == "dictation":
            self._root.deiconify()
            self._canvas.itemconfig(self._text_item, text="🎙️ Listening...", fill=self.TEXT_COLOR)
        elif mode == "command":
            self._root.deiconify()
            self._canvas.itemconfig(self._text_item, text="⚡ Command...", fill=self.COMMAND_GLOW)
        elif mode == "processing":
            self._root.deiconify()
            self._canvas.itemconfig(
                self._text_item, text="⏳ Flowing...", fill=self.PROCESSING_COLOR
            )

    def _flash(self, color: str, message: str) -> None:
        if not self._root or not self._canvas:
            return
        self._mode = "flash"
        self._root.deiconify()

        # Hide wave bars during message flash
        for rect in self._wave_bars:
            self._canvas.coords(rect, 0, 0, 0, 0)

        self._canvas.itemconfig(self._text_item, text=message, fill=color)
        self._root.after(850, lambda: self._set_mode("hidden"))

    def _destroy_root(self) -> None:
        if self._root:
            with contextlib.suppress(Exception):
                self._root.destroy()
            self._root = None
