# MIT License — Copyright (c) 2025 drajb & Rohit Burani
# Ported and adapted for Kural
"""Windows system tray icon with status indicator and context menu.

Gracefully degrades to a no-op if pystray or Pillow are not installed, allowing
Kural to run in lightweight console mode without forcing UI dependencies.
"""

import contextlib
import logging
import threading
from collections.abc import Callable

logger = logging.getLogger(__name__)


class SystemTray:
    """System tray controller displaying status and providing quick actions."""

    def __init__(
        self,
        on_toggle_dictation: Callable[[], None] | None = None,
        on_toggle_command: Callable[[], None] | None = None,
        on_toggle_incognito: Callable[[], None] | None = None,
        is_incognito: Callable[[], bool] | None = None,
        on_open_history: Callable[[], None] | None = None,
        on_open_cheat_sheet: Callable[[], None] | None = None,
        on_open_settings: Callable[[], None] | None = None,
        on_exit: Callable[[], None] | None = None,
        enabled: bool = True,
    ):
        self.on_toggle_dictation = on_toggle_dictation
        self.on_toggle_command = on_toggle_command
        self.on_toggle_incognito = on_toggle_incognito
        self.is_incognito = is_incognito or (lambda: False)
        self.on_open_history = on_open_history
        self.on_open_cheat_sheet = on_open_cheat_sheet
        self.on_open_settings = on_open_settings
        self.on_exit = on_exit
        self.enabled = enabled

        self._icon = None
        self._thread = None
        self._running = False
        self._available = self._check_tray_available()

    def update_menu(self) -> None:
        """Refresh tray menu to update checkmark states."""
        if self._icon and self._running:
            with contextlib.suppress(Exception):
                self._icon.update_menu()

    def _check_tray_available(self) -> bool:
        if not self.enabled:
            return False
        try:
            import PIL.Image  # noqa
            import pystray  # noqa

            return True
        except ImportError:
            logger.info("pystray or Pillow not installed; system tray disabled")
            return False

    def is_available(self) -> bool:
        return self._available

    def start(self) -> None:
        """Launch the system tray icon on a background thread."""
        if not self._available or self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_tray_loop, daemon=True, name="system-tray")
        self._thread.start()

    def stop(self) -> None:
        """Stop and remove the system tray icon."""
        self._running = False
        if self._icon:
            with contextlib.suppress(Exception):
                self._icon.stop()
            self._icon = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

    def _create_icon_image(self, color=(63, 185, 80)):
        """Generate a clean 16x16 icon bitmap."""
        from PIL import Image, ImageDraw

        image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((1, 1, 14, 14), fill=color, outline=(255, 255, 255, 180))
        return image

    def _run_tray_loop(self) -> None:
        try:
            import pystray

            image = self._create_icon_image()

            menu = pystray.Menu(
                pystray.MenuItem("Kural — Voice Typing", lambda: None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "Dictate (Ctrl+Space)",
                    lambda icon, item: (
                        self.on_toggle_dictation() if self.on_toggle_dictation else None
                    ),
                ),
                pystray.MenuItem(
                    "Voice Command (Ctrl+Shift+Space)",
                    lambda icon, item: self.on_toggle_command() if self.on_toggle_command else None,
                ),
                pystray.MenuItem(
                    "Incognito (save nothing)",
                    lambda icon, item: (
                        self.on_toggle_incognito() if self.on_toggle_incognito else None
                    ),
                    checked=lambda item: self.is_incognito(),
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "History...",
                    lambda icon, item: self.on_open_history() if self.on_open_history else None,
                ),
                pystray.MenuItem(
                    "Cheat Sheet...",
                    lambda icon, item: (
                        self.on_open_cheat_sheet() if self.on_open_cheat_sheet else None
                    ),
                ),
                pystray.MenuItem(
                    "Settings...",
                    lambda icon, item: self.on_open_settings() if self.on_open_settings else None,
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "Exit", lambda icon, item: self.on_exit() if self.on_exit else self.stop()
                ),
            )

            self._icon = pystray.Icon("kural", image, "Kural — Speech Recognition", menu)
            self._icon.run()
        except Exception as e:
            logger.warning(f"System tray run failed: {e}")
            self._available = False
