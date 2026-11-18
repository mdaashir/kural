# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/platform/windows/mouse.py
"""Mouse button push-to-talk trigger ("Mouse Flow").

Enables holding a mouse thumb button (XButton1/XButton2) or middle click as a
push-to-talk trigger. Uses a Win32 low-level mouse hook (WH_MOUSE_LL) on a
dedicated message-loop thread to both capture button down/up transitions and
swallow the event (preventing browser 'Back' or auto-scroll actions).
"""

import ctypes
import ctypes.wintypes as wintypes
import logging
import sys
import threading
from collections.abc import Callable

logger = logging.getLogger(__name__)

WH_MOUSE_LL = 14
WM_QUIT = 0x0012
WM_MBUTTONDOWN, WM_MBUTTONUP = 0x0207, 0x0208
WM_XBUTTONDOWN, WM_XBUTTONUP = 0x020B, 0x020C
XBUTTON1, XBUTTON2 = 0x0001, 0x0002

BUTTONS: dict[str, tuple[str, ...]] = {
    "middle": ("middle",),
    "x1": ("x1",),
    "x2": ("x2",),
    "both": ("x1", "x2"),
}


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)


def is_supported() -> bool:
    """Return True if mouse hook triggers are supported on this platform."""
    return sys.platform == "win32"


def decode_mouse_event(wparam: int, lparam: int) -> tuple[str | None, bool | None]:
    """Decode a mouse hook message to identify button name and press state.

    Returns (button_name, is_press) or (None, None) for other events (like cursor moves).
    """
    if wparam in (WM_MBUTTONDOWN, WM_MBUTTONUP):
        return "middle", (wparam == WM_MBUTTONDOWN)
    if wparam in (WM_XBUTTONDOWN, WM_XBUTTONUP):
        try:
            info = ctypes.cast(lparam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            which = (info.mouseData >> 16) & 0xFFFF
            name = {XBUTTON1: "x1", XBUTTON2: "x2"}.get(which)
            return name, (wparam == WM_XBUTTONDOWN)
        except Exception:
            return None, None
    return None, None


class MouseButtonTrigger:
    """Calls on_press and on_release when configured mouse button goes down / up.

    Swallows matching events so the button's native action (e.g. browser Back) does
    not fire while dictating. Delegates callbacks to daemon threads so the hook
    returns instantly (<0.1ms), avoiding mouse cursor stutter.
    """

    def __init__(
        self,
        button: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
        is_active: Callable[[], bool] = lambda: True,
    ):
        clean_button = (button or "").strip().lower()
        if clean_button not in BUTTONS:
            raise ValueError(f"Unknown mouse button {button!r}; choose from {', '.join(BUTTONS)}")

        self.buttons = BUTTONS[clean_button]
        self.on_press = on_press
        self.on_release = on_release
        self.is_active = is_active

        self._hook = None
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._ready = threading.Event()
        self._held: set[str] = set()
        self._proc = HOOKPROC(self._hook_proc)

    def _hook_proc(self, n_code: int, wparam: int, lparam: int) -> int:
        if n_code == 0:
            try:
                name, pressed = decode_mouse_event(wparam, lparam)
                if name in self.buttons:
                    if pressed and self.is_active():
                        self._held.add(name)
                        threading.Thread(
                            target=self.on_press, daemon=True, name="mouse-ptt-press"
                        ).start()
                        return 1  # Swallow event from OS
                    if not pressed and name in self._held:
                        self._held.discard(name)
                        threading.Thread(
                            target=self.on_release, daemon=True, name="mouse-ptt-release"
                        ).start()
                        return 1  # Swallow event from OS
            except Exception as e:
                logger.debug(f"Mouse hook procedure error: {e}")

        if sys.platform == "win32":
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            return user32.CallNextHookEx(None, n_code, wparam, lparam)
        return 0

    def _run(self) -> None:
        if sys.platform != "win32":
            return

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        user32.SetWindowsHookExW.argtypes = [
            ctypes.c_int,
            HOOKPROC,
            wintypes.HINSTANCE,
            wintypes.DWORD,
        ]
        user32.SetWindowsHookExW.restype = wintypes.HHOOK
        user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]

        self._thread_id = kernel32.GetCurrentThreadId()
        self._hook = user32.SetWindowsHookExW(
            WH_MOUSE_LL, self._proc, kernel32.GetModuleHandleW(None), 0
        )
        self._ready.set()

        if not self._hook:
            logger.error(f"Could not install mouse hook (error {ctypes.get_last_error()})")
            return

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        user32.UnhookWindowsHookEx(self._hook)
        self._hook = None

    def start(self) -> bool:
        """Start mouse button hook on a background Win32 message-loop thread."""
        if not is_supported():
            return False
        if self._thread and self._thread.is_alive():
            return True

        self._ready.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="mouse-ptt-hook")
        self._thread.start()
        self._ready.wait(timeout=2.0)

        if self._hook:
            logger.info(f"Mouse push-to-talk active on: {'/'.join(self.buttons)}")
        return bool(self._hook)

    def stop(self) -> None:
        """Unhook and terminate the mouse hook thread."""
        if sys.platform == "win32" and self._thread_id and self._thread and self._thread.is_alive():
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            self._thread.join(timeout=2.0)

        self._thread = None
        self._thread_id = None
        self._held.clear()
