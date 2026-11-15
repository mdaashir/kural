# MIT License — Copyright (c) 2025 drajb & Rohit Burani
# Ported and adapted from drajb/whisper-local/src/whisper_key/history_window.py
"""Searchable history browser window (Tkinter) for Kural.

Allows users to visually search, browse, and copy past dictations and voice commands.
Features live search-as-you-type with BM25 full-text ranking, app context tags,
and one-click clipboard copying.
"""

import contextlib
import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_instance: Any = None


class HistoryWindow:
    """Tkinter-based searchable history viewer."""

    WIDTH = 700
    HEIGHT = 520

    def __init__(
        self, storage_dir: str | Path | None = None, on_copy: Callable[[str], None] | None = None
    ):
        self.storage_dir = storage_dir
        self.on_copy = on_copy
        self.root = None
        self.tree = None
        self.status_label = None
        self.search_var = None
        self._entries: list[dict] = []

    def show(self) -> None:
        """Construct and run the history window."""
        global _instance
        import tkinter as tk
        from tkinter import ttk

        with _lock:
            try:
                if _instance and _instance.winfo_exists():
                    _instance.lift()
                    _instance.focus_force()
                    return
            except Exception:
                pass

        root = tk.Tk()
        with _lock:
            _instance = root

        def _clear_ref():
            global _instance
            with _lock:
                _instance = None
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", _clear_ref)
        root.title("Kural — Speech & Command History")
        root.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        root.minsize(550, 380)
        root.configure(bg="#0d1117")

        self.root = root

        # Top search frame
        top_frame = tk.Frame(root, bg="#0d1117", padx=16, pady=12)
        top_frame.pack(fill=tk.X)

        lbl = tk.Label(
            top_frame,
            text="Search:",
            bg="#0d1117",
            fg="#f0f6fc",
            font=("Segoe UI", 10, "bold"),
        )
        lbl.pack(side=tk.LEFT, padx=(0, 8))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._on_search_changed())

        search_entry = tk.Entry(
            top_frame,
            textvariable=self.search_var,
            bg="#161b22",
            fg="#f0f6fc",
            insertbackground="#f0f6fc",
            relief=tk.FLAT,
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground="#30363d",
            highlightcolor="#58a6ff",
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        search_entry.focus_set()

        copy_btn = tk.Button(
            top_frame,
            text="Copy Selected",
            bg="#21262d",
            fg="#f0f6fc",
            activebackground="#30363d",
            activeforeground="#f0f6fc",
            relief=tk.FLAT,
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=3,
            cursor="hand2",
            command=self._copy_selected,
        )
        copy_btn.pack(side=tk.RIGHT)

        # Treeview / table for entries
        tree_frame = tk.Frame(root, bg="#0d1117", padx=16, pady=(0, 8))
        tree_frame.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(
            "History.Treeview",
            background="#161b22",
            foreground="#f0f6fc",
            fieldbackground="#161b22",
            rowheight=26,
            font=("Segoe UI", 9),
            borderwidth=0,
        )
        style.configure(
            "History.Treeview.Heading",
            background="#21262d",
            foreground="#f0f6fc",
            relief=tk.FLAT,
            font=("Segoe UI", 9, "bold"),
        )
        style.map(
            "History.Treeview",
            background=[("selected", "#1f6feb")],
            foreground=[("selected", "#ffffff")],
        )

        columns = ("time", "task", "app", "text")
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="History.Treeview",
            selectmode="browse",
        )

        tree.heading("time", text="Time")
        tree.heading("task", text="Task")
        tree.heading("app", text="App")
        tree.heading("text", text="Spoken Text")

        tree.column("time", width=130, minwidth=110, stretch=False)
        tree.column("task", width=80, minwidth=70, stretch=False)
        tree.column("app", width=110, minwidth=90, stretch=False)
        tree.column("text", width=360, minwidth=200, stretch=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree.bind("<Double-1>", lambda _: self._copy_selected())
        self.tree = tree

        # Bottom status bar
        status_frame = tk.Frame(root, bg="#161b22", padx=16, pady=6)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(
            status_frame,
            text="",
            bg="#161b22",
            fg="#8b949e",
            font=("Segoe UI", 9),
        )
        self.status_label.pack(side=tk.LEFT)

        # Initial data load
        self._refresh_entries()

        try:
            root.mainloop()
        finally:
            with _lock:
                _instance = None

    def _refresh_entries(self) -> None:
        """Fetch matching entries from storage and populate the treeview."""
        from kural.engine.history import search_history

        query = self.search_var.get() if self.search_var else ""
        self._entries = search_history(query=query, limit=100, storage_dir=self.storage_dir)

        if not self.tree:
            return

        for row in self.tree.get_children():
            self.tree.delete(row)

        for idx, entry in enumerate(self._entries):
            ts = entry.get("ts", "")[:19].replace("T", " ")
            task = entry.get("task", "transcribe")
            app = entry.get("app", "") or "-"
            text = entry.get("text", "")
            self.tree.insert("", "end", iid=str(idx), values=(ts, task, app, text))

        count = len(self._entries)
        if self.status_label:
            info = f"{count} entries found • Double-click or select and click 'Copy Selected'"
            self.status_label.config(text=info)

    def _on_search_changed(self) -> None:
        self._refresh_entries()

    def _copy_to_clipboard(self, text: str) -> bool:
        """Copy text to clipboard via pyperclip or Tk root."""
        with contextlib.suppress(Exception):
            import pyperclip

            pyperclip.copy(text)
            return True

        if self.root:
            with contextlib.suppress(Exception):
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                return True
        return False

    def _copy_selected(self) -> None:
        """Copy selected row's text to the clipboard."""
        if not self.tree:
            return
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        if idx >= len(self._entries):
            return

        text = self._entries[idx].get("text", "")
        if not text:
            return

        self._copy_to_clipboard(text)

        if self.on_copy:
            with contextlib.suppress(Exception):
                self.on_copy(text)

        if self.status_label:
            preview = text[:30] + ("..." if len(text) > 30 else "")
            self.status_label.config(text=f'✓ Copied to clipboard: "{preview}"')


def open_history_window(
    storage_dir: str | Path | None = None,
    on_copy: Callable[[str], None] | None = None,
) -> None:
    """Launch the history window on a background daemon thread, or directly if on main."""
    win = HistoryWindow(storage_dir=storage_dir, on_copy=on_copy)
    if threading.current_thread() is threading.main_thread():
        win.show()
    else:
        t = threading.Thread(target=win.show, daemon=True, name="history-ui")
        t.start()
