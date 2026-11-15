# MIT License — Copyright (c) 2025 drajb & Rohit Burani
# Ported and adapted from drajb/whisper-local/src/whisper_key/settings_ui.py and whisp/settings.py
"""Desktop Settings dialog (Tkinter) for Kural.

Allows users to configure Whisper engine settings, language selection, idle VRAM timeout,
hotkeys, visual overlay position, and voice-control preferences without manually editing YAML.
"""

import logging
import os
import subprocess
import sys
import threading
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

MODELS = ["large-v3-turbo", "distil-large-v3.5", "large-v3", "small", "base", "tiny"]
DEVICES = ["cuda", "cpu"]
COMPUTE_TYPES = ["float16", "int8"]
LANGUAGES = ["en", "ta", "auto"]
POSITIONS = ["bottom-center", "top-center", "bottom-right", "top-right"]


def open_folder(path: str) -> None:
    """Open a folder in Windows File Explorer or the default OS file manager."""
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


class SettingsWindow:
    """Tkinter-based configuration dialog for Kural."""

    WIDTH = 520
    HEIGHT = 440

    def __init__(self, config_manager=None, on_save: Callable[[], None] | None = None):
        from kural.config import ConfigManager

        self.config_manager = config_manager or ConfigManager(quiet=True)
        self.on_save = on_save
        self.root = None

        # State fields loaded from config
        self.whisper_cfg = self.config_manager.get_whisper_config()
        self.hotkey_cfg = self.config_manager.get_hotkey_config()
        self.overlay_cfg = self.config_manager.config.get("overlay") or {}
        self.vc_cfg = self.config_manager.config.get("voice_commands") or {}

        # Tkinter variables
        self.var_model = None
        self.var_device = None
        self.var_compute = None
        self.var_lang = None
        self.var_idle_vram = None
        self.var_dict_hk = None
        self.var_cmd_hk = None
        self.var_overlay_enabled = None
        self.var_overlay_pos = None
        self.var_click_through = None
        self.var_fuzzy = None

    def show(self) -> None:
        """Construct and display the settings window (blocks until closed)."""
        import tkinter as tk
        from tkinter import messagebox, ttk

        root = tk.Tk()
        self.root = root
        root.title("Kural Settings")
        root.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        root.minsize(480, 400)

        # Center on screen
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = max(0, (sw - self.WIDTH) // 2)
        y = max(0, (sh - self.HEIGHT) // 2)
        root.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        self._init_variables(tk)

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=12, pady=(12, 6))

        tab_engine = ttk.Frame(notebook, padding=12)
        tab_hotkeys = ttk.Frame(notebook, padding=12)
        tab_ui = ttk.Frame(notebook, padding=12)

        notebook.add(tab_engine, text="Speech Engine")
        notebook.add(tab_hotkeys, text="Hotkeys")
        notebook.add(tab_ui, text="Overlay & Control")

        self._build_engine_tab(tab_engine, ttk)
        self._build_hotkeys_tab(tab_hotkeys, ttk)
        self._build_ui_tab(tab_ui, ttk)

        # Bottom action bar
        btn_bar = ttk.Frame(root, padding=(12, 6, 12, 12))
        btn_bar.pack(fill="x", side="bottom")

        btn_open = ttk.Button(btn_bar, text="Open Config Folder", command=self._on_open_folder)
        btn_open.pack(side="left")

        btn_cancel = ttk.Button(btn_bar, text="Cancel", command=root.destroy)
        btn_cancel.pack(side="right", padx=(6, 0))

        btn_save = ttk.Button(
            btn_bar, text="Save Settings", command=lambda: self._on_save(messagebox)
        )
        btn_save.pack(side="right")

        root.mainloop()

    def _init_variables(self, tk) -> None:
        self.var_model = tk.StringVar(value=self.whisper_cfg.get("model", "large-v3-turbo"))
        self.var_device = tk.StringVar(value=self.whisper_cfg.get("device", "cuda"))
        self.var_compute = tk.StringVar(value=self.whisper_cfg.get("compute_type", "float16"))
        self.var_lang = tk.StringVar(value=self.whisper_cfg.get("language", "en"))
        self.var_idle_vram = tk.IntVar(value=int(self.whisper_cfg.get("idle_unload_minutes", 5)))

        self.var_dict_hk = tk.StringVar(value=self.hotkey_cfg.get("recording_hotkey", "ctrl+space"))
        self.var_cmd_hk = tk.StringVar(
            value=self.hotkey_cfg.get("command_hotkey", "ctrl+shift+space")
        )

        self.var_overlay_enabled = tk.BooleanVar(value=bool(self.overlay_cfg.get("enabled", True)))
        self.var_overlay_pos = tk.StringVar(value=self.overlay_cfg.get("position", "bottom-center"))
        self.var_click_through = tk.BooleanVar(
            value=bool(self.overlay_cfg.get("click_through", True))
        )

        self.var_fuzzy = tk.BooleanVar(value=bool(self.vc_cfg.get("fuzzy_match", True)))

    def _build_engine_tab(self, parent, ttk) -> None:
        row = 0

        def _add_combo(label_text, var, values):
            nonlocal row
            ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", pady=6)
            cb = ttk.Combobox(parent, textvariable=var, values=values, state="readonly", width=22)
            cb.grid(row=row, column=1, sticky="w", padx=12, pady=6)
            row += 1

        _add_combo("Whisper Model:", self.var_model, MODELS)
        _add_combo("Inference Device:", self.var_device, DEVICES)
        _add_combo("Compute Precision:", self.var_compute, COMPUTE_TYPES)
        _add_combo("Default Language:", self.var_lang, LANGUAGES)

        ttk.Label(parent, text="Idle VRAM Unload (min):").grid(
            row=row, column=0, sticky="w", pady=6
        )
        spin = ttk.Spinbox(parent, from_=0, to=120, textvariable=self.var_idle_vram, width=10)
        spin.grid(row=row, column=1, sticky="w", padx=12, pady=6)
        ttk.Label(parent, text="(0 = never unload, frees ~1.5 GB on RTX 3050)", font=("", 8)).grid(
            row=row + 1, column=1, sticky="w", padx=12, pady=(0, 6)
        )

    def _build_hotkeys_tab(self, parent, ttk) -> None:
        ttk.Label(parent, text="Dictation Mode:").grid(row=0, column=0, sticky="w", pady=8)
        e1 = ttk.Entry(parent, textvariable=self.var_dict_hk, width=24)
        e1.grid(row=0, column=1, sticky="w", padx=12, pady=8)
        ttk.Label(
            parent, text="Hold or toggle to dictate speech into active window cursor", font=("", 8)
        ).grid(row=1, column=1, sticky="w", padx=12, pady=(0, 10))

        ttk.Label(parent, text="Command Mode:").grid(row=2, column=0, sticky="w", pady=8)
        e2 = ttk.Entry(parent, textvariable=self.var_cmd_hk, width=24)
        e2.grid(row=2, column=1, sticky="w", padx=12, pady=8)
        ttk.Label(
            parent, text="Voice control (open/close apps, volume, snap windows)", font=("", 8)
        ).grid(row=3, column=1, sticky="w", padx=12, pady=(0, 10))

    def _build_ui_tab(self, parent, ttk) -> None:
        c1 = ttk.Checkbutton(
            parent, text="Enable Floating Status Pill", variable=self.var_overlay_enabled
        )
        c1.grid(row=0, column=0, columnspan=2, sticky="w", pady=6)

        ttk.Label(parent, text="Overlay Position:").grid(row=1, column=0, sticky="w", pady=6)
        cb = ttk.Combobox(
            parent, textvariable=self.var_overlay_pos, values=POSITIONS, state="readonly", width=20
        )
        cb.grid(row=1, column=1, sticky="w", padx=12, pady=6)

        c2 = ttk.Checkbutton(
            parent,
            text="Click-Through (transparent to mouse clicks)",
            variable=self.var_click_through,
        )
        c2.grid(row=2, column=0, columnspan=2, sticky="w", pady=6)

        c3 = ttk.Checkbutton(parent, text="Fuzzy Voice Command Matching", variable=self.var_fuzzy)
        c3.grid(row=3, column=0, columnspan=2, sticky="w", pady=6)

    def _on_open_folder(self) -> None:
        from kural.engine.utils import get_user_app_data_path

        path = get_user_app_data_path()
        open_folder(path)

    def collect_settings(self) -> dict[str, Any]:
        """Collect the current settings state into a dictionary matching config schema."""
        return {
            "whisper": {
                "model": self.var_model.get() if self.var_model else "large-v3-turbo",
                "device": self.var_device.get() if self.var_device else "cuda",
                "compute_type": self.var_compute.get() if self.var_compute else "float16",
                "language": self.var_lang.get() if self.var_lang else "en",
                "idle_unload_minutes": int(self.var_idle_vram.get()) if self.var_idle_vram else 5,
            },
            "hotkey": {
                "recording_hotkey": self.var_dict_hk.get().strip().lower()
                if self.var_dict_hk
                else "ctrl+space",
                "command_hotkey": self.var_cmd_hk.get().strip().lower()
                if self.var_cmd_hk
                else "ctrl+shift+space",
            },
            "overlay": {
                "enabled": bool(self.var_overlay_enabled.get())
                if self.var_overlay_enabled
                else True,
                "position": self.var_overlay_pos.get() if self.var_overlay_pos else "bottom-center",
                "click_through": bool(self.var_click_through.get())
                if self.var_click_through
                else True,
            },
            "voice_commands": {
                "fuzzy_match": bool(self.var_fuzzy.get()) if self.var_fuzzy else True,
            },
        }

    def _on_save(self, messagebox) -> None:
        settings = self.collect_settings()
        try:
            for section, values in settings.items():
                for key, val in values.items():
                    self.config_manager.set_user_setting(f"{section}.{key}", val)

            messagebox.showinfo(
                "Kural",
                "Settings saved successfully!\nChanges will take effect immediately or on next recording.",
            )
            if self.on_save:
                self.on_save()
            if self.root:
                self.root.destroy()
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")


def open_settings_window(config_manager=None, on_save: Callable[[], None] | None = None) -> None:
    """Launch the settings window on a background thread if already in an event loop, or directly."""
    win = SettingsWindow(config_manager=config_manager, on_save=on_save)

    # If Tkinter is already running on the main thread, run inside it; else start thread
    if threading.current_thread() is threading.main_thread():
        win.show()
    else:
        t = threading.Thread(target=win.show, daemon=True, name="settings-ui")
        t.start()
