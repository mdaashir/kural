# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/fallback_window.py
"""Safety net window for dictation with nowhere to go.

When no text field is focused, or when target applications block synthetic input,
auto-paste or direct typing would drop the transcript. Instead, it appears in a
compact, dark-themed window, pre-selected with one-click copy, ensuring the user
never loses dictated speech. Runs its own Tk event loop on a daemon thread.
"""

import contextlib
import logging
import threading

logger = logging.getLogger(__name__)

WIDTH = 520
MIN_HEIGHT = 180
MAX_HEIGHT = 480

BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
TEXT = "#c9d1d9"
DIM = "#7d8590"
ACCENT = "#3fb950"
ACCENT_HOVER = "#46c155"


class FallbackWindow:
    """Displays un-deliverable dictation text in a pre-selected modal dialog."""

    def __init__(self):
        self._available = self._check_tk()
        self._lock = threading.Lock()
        self._open = False

    def _check_tk(self) -> bool:
        try:
            import tkinter  # noqa: F401

            return True
        except ImportError:
            return False

    @property
    def is_available(self) -> bool:
        return self._available

    @property
    def is_open(self) -> bool:
        with self._lock:
            return self._open

    def show(
        self,
        transcript: str,
        reason: str | None = None,
        allow_clipboard: bool = True,
    ) -> None:
        """Present the fallback window on a background thread.

        Args:
            transcript: Transcribed speech text to preserve.
            reason: Explanation shown to the user of why direct delivery failed.
            allow_clipboard: Whether to place text on the clipboard automatically.
        """
        if not self._available or not transcript or not transcript.strip():
            return

        resolved_reason = reason or "No text field was focused — your dictation is safe here."

        with self._lock:
            if self._open:
                logger.info("Fallback window is already open; skipping duplicate dialog.")
                return
            self._open = True

        thread = threading.Thread(
            target=self._run_window,
            args=(transcript, resolved_reason, allow_clipboard),
            daemon=True,
            name="fallback-window",
        )
        thread.start()

    def _run_window(self, transcript: str, reason: str, allow_clipboard: bool = True) -> None:
        try:
            import tkinter as tk

            root = tk.Tk()
            root.title("Kural — Dictation Captured")
            root.configure(bg=BG)

            with contextlib.suppress(Exception):
                root.attributes("-topmost", True)

            line_count = max(3, min(transcript.count("\n") + 1 + len(transcript) // 60, 18))
            height = min(MAX_HEIGHT, max(MIN_HEIGHT, 110 + line_count * 18))

            try:
                root.update_idletasks()
                sw = root.winfo_screenwidth()
                sh = root.winfo_screenheight()
                x = max(0, (sw - WIDTH) // 2)
                y = max(0, (sh - height) // 2)
                root.geometry(f"{WIDTH}x{height}+{x}+{y}")
            except Exception:
                root.geometry(f"{WIDTH}x{height}")

            outer = tk.Frame(root, bg=BG, bd=0, highlightthickness=0)
            outer.pack(fill="both", expand=True, padx=14, pady=12)

            tk.Label(
                outer,
                text="📋  Dictation captured",
                bg=BG,
                fg=ACCENT,
                font=("Segoe UI Semibold", 11),
                anchor="w",
            ).pack(fill="x")

            tk.Label(
                outer,
                text=reason,
                bg=BG,
                fg=DIM,
                font=("Segoe UI", 9),
                anchor="w",
                wraplength=WIDTH - 30,
                justify="left",
            ).pack(fill="x", pady=(2, 8))

            text_frame = tk.Frame(outer, bg=BORDER, bd=0, highlightthickness=0)
            text_frame.pack(fill="both", expand=True, pady=(0, 10))

            text_widget = tk.Text(
                text_frame,
                wrap="word",
                bg=PANEL,
                fg=TEXT,
                insertbackground=TEXT,
                bd=0,
                highlightthickness=0,
                padx=10,
                pady=8,
                font=("Segoe UI", 10),
                relief="flat",
            )
            text_widget.pack(fill="both", expand=True, padx=1, pady=1)
            text_widget.insert("1.0", transcript)
            text_widget.tag_add("sel", "1.0", "end-1c")

            button_row = tk.Frame(outer, bg=BG)
            button_row.pack(fill="x")

            status_var = tk.StringVar(
                master=root,
                value=(
                    "Already on your clipboard — paste anywhere with Ctrl+V."
                    if allow_clipboard
                    else "Press Copy to copy text to your clipboard."
                ),
            )
            status = tk.Label(
                button_row,
                textvariable=status_var,
                bg=BG,
                fg=DIM,
                font=("Segoe UI", 9),
            )
            status.pack(side="left")

            def _copy_again(_=None):
                try:
                    import pyperclip

                    pyperclip.copy(transcript)
                    status_var.set("✓ Copied to clipboard! Paste with Ctrl+V.")
                    btn_copy.configure(text="✓ Copied")
                    root.after(1200, lambda: btn_copy.configure(text="Copy"))
                except Exception as e:
                    status_var.set(f"Copy failed: {e}")

            def _dismiss(_=None):
                with contextlib.suppress(Exception):
                    root.destroy()

            btn_close = tk.Button(
                button_row,
                text="Close",
                command=_dismiss,
                bg=PANEL,
                fg=TEXT,
                activebackground=BORDER,
                activeforeground=TEXT,
                bd=0,
                relief="flat",
                padx=14,
                pady=6,
                font=("Segoe UI", 9),
                cursor="hand2",
            )
            btn_close.pack(side="right", padx=(8, 0))

            btn_copy = tk.Button(
                button_row,
                text="Copy",
                command=_copy_again,
                bg=ACCENT,
                fg="#0d1117",
                activebackground=ACCENT_HOVER,
                activeforeground="#0d1117",
                bd=0,
                relief="flat",
                padx=14,
                pady=6,
                font=("Segoe UI Semibold", 9),
                cursor="hand2",
            )
            btn_copy.pack(side="right")

            root.bind("<Escape>", _dismiss)
            root.bind("<Control-c>", _copy_again)
            text_widget.focus_set()

            if allow_clipboard:
                try:
                    import pyperclip

                    pyperclip.copy(transcript)
                except Exception:
                    pass

            root.mainloop()
        except Exception as e:
            logger.warning(f"Fallback window error: {e}")
        finally:
            with self._lock:
                self._open = False
