# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported from drajb/whisper-local/src/whisper_key/level_overlay.py
"""Small, always-on-top visual status pill near the screen edge.

Displays live microphone input level while recording, spinner/status while processing,
and success/failure flashes upon completion. On Windows, click-through styling is enabled
so mouse clicks pass directly through to windows below.
"""

import contextlib
import logging
import queue
import sys
import threading
from collections.abc import Callable

logger = logging.getLogger(__name__)


class LevelOverlay:
    """Floating visual pill rendering recording state and microphone activity."""

    WIDTH = 280
    HEIGHT = 32
    BG_COLOR = "#0d1117"
    BORDER_COLOR = "#30363d"
    TEXT_COLOR = "#c9d1d9"
    LEVEL_COLOR = "#3fb950"  # Green
    COMMAND_COLOR = "#58a6ff"  # Blue
    ERROR_COLOR = "#f85149"  # Red

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
        self._bar_item = None
        self._status_text = "Ready"
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

    def flash_success(self, message: str = "Done") -> None:
        """Flash green success status and hide."""
        self._dispatch(lambda: self._flash(self.LEVEL_COLOR, message))

    def flash_error(self, message: str = "Error") -> None:
        """Flash red error status and hide."""
        self._dispatch(lambda: self._flash(self.ERROR_COLOR, message))

    def hide(self) -> None:
        """Hide the overlay pill."""
        self._dispatch(lambda: self._set_mode("hidden"))

    def stop(self) -> None:
        """Terminate the overlay thread."""
        self._running = False
        self._dispatch(lambda: self._destroy_root())
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
            root.title("Kural Status")
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.configure(bg=self.BG_COLOR)

            # Position window on screen
            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()

            x = (screen_w - self.WIDTH) // 2
            y = screen_h - self.HEIGHT - 60 if "bottom" in self.position else 40
            root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

            # Canvas for drawing pill border and audio bar
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

            self._bar_item = canvas.create_rectangle(
                6, 6, 6, self.HEIGHT - 6, fill=self.LEVEL_COLOR, width=0
            )
            self._text_item = canvas.create_text(
                self.WIDTH // 2,
                self.HEIGHT // 2,
                text="Kural",
                fill=self.TEXT_COLOR,
                font=("Segoe UI", 10, "bold"),
            )

            # Windows click-through transparent style
            if sys.platform == "win32" and self.click_through:
                self._enable_click_through(root)

            # Initial state is hidden
            root.withdraw()

            # Background pump loop
            self._poll_commands()
            root.mainloop()
        except Exception as e:
            logger.warning(f"Level overlay loop terminated: {e}")
            self._available = False

    def _enable_click_through(self, root) -> None:
        try:
            import ctypes

            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            # WS_EX_TRANSPARENT = 0x20, WS_EX_LAYERED = 0x80000
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

        # If currently recording, animate live mic level
        if self._mode in ("dictation", "command") and self._canvas:
            level = min(1.0, max(0.0, self.level_provider() * 20.0))
            max_w = self.WIDTH - 12
            bar_w = int(6 + (max_w * level))
            color = self.COMMAND_COLOR if self._mode == "command" else self.LEVEL_COLOR
            self._canvas.coords(self._bar_item, 6, 6, bar_w, self.HEIGHT - 6)
            self._canvas.itemconfig(self._bar_item, fill=color)

        self._root.after(30, self._poll_commands)

    def _set_mode(self, mode: str) -> None:
        self._mode = mode
        if not self._root or not self._canvas:
            return

        if mode == "hidden":
            self._root.withdraw()
        elif mode == "dictation":
            self._root.deiconify()
            self._canvas.itemconfig(self._text_item, text="🎙️ Dictating...", fill=self.TEXT_COLOR)
        elif mode == "command":
            self._root.deiconify()
            self._canvas.itemconfig(self._text_item, text="⚡ Command...", fill=self.TEXT_COLOR)
        elif mode == "processing":
            self._root.deiconify()
            self._canvas.coords(self._bar_item, 6, 6, 6, self.HEIGHT - 6)
            self._canvas.itemconfig(self._text_item, text="⏳ Transcribing...", fill="#d29922")

    def _flash(self, color: str, message: str) -> None:
        if not self._root or not self._canvas:
            return
        self._mode = "flash"
        self._root.deiconify()
        self._canvas.coords(self._bar_item, 6, 6, self.WIDTH - 6, self.HEIGHT - 6)
        self._canvas.itemconfig(self._bar_item, fill=color)
        self._canvas.itemconfig(self._text_item, text=message, fill="#ffffff")

        # Automatically hide after 800ms
        self._root.after(800, lambda: self._set_mode("hidden"))

    def _destroy_root(self) -> None:
        if self._root:
            with contextlib.suppress(Exception):
                self._root.destroy()
            self._root = None
