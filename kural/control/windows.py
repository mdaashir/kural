# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported from ROHITCRAFTSYT/WhispLocal/whisp/commands.py
"""Windows management for voice control: window enumeration, focus, snap, and graceful close."""

import contextlib
import logging
import os
import sys
from dataclasses import dataclass

logger = logging.getLogger(__name__)

WM_CLOSE = 0x0010
SW_MAXIMIZE = 3
SW_MINIMIZE = 6
SW_RESTORE = 9

VK_LWIN = 0x5B
VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_UP = 0x26
VK_DOWN = 0x28
VK_D = 0x44
KEYEVENTF_KEYUP = 0x0002


@dataclass
class WindowInfo:
    """Represents a visible top-level desktop window."""

    hwnd: int
    title: str
    exe: str


def list_windows() -> list[WindowInfo]:
    """Enumerate all visible top-level windows with non-empty titles."""
    if sys.platform != "win32":
        return []

    import ctypes
    import ctypes.wintypes as wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    results: list[WindowInfo] = []

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def enum_cb(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True

        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value.strip()
        if not title:
            return True

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        exe = ""
        # PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h_proc = kernel32.OpenProcess(0x1000, False, pid.value)
        if h_proc:
            size = wintypes.DWORD(260)
            path_buf = ctypes.create_unicode_buffer(260)
            if kernel32.QueryFullProcessImageNameW(h_proc, 0, path_buf, ctypes.byref(size)):
                exe = os.path.basename(path_buf.value)
            kernel32.CloseHandle(h_proc)

        results.append(WindowInfo(hwnd=hwnd, title=title, exe=exe))
        return True

    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return results


def focus_window(term: str, allow_browser: bool = True) -> str | None:
    """Find a window matching `term` in title or executable name, focus it, and return its title.

    Uses SwitchToThisWindow to reliably bypass the Windows foreground-lock restriction.
    """
    if sys.platform != "win32":
        return None

    import ctypes

    clean_term = (term or "").strip().lower()
    if len(clean_term) < 2:
        return None

    from kural.control.guardrails import default_guardrails

    candidates = []
    for win in list_windows():
        if default_guardrails.is_protected_target(
            win.exe
        ) or default_guardrails.is_protected_target(win.title):
            continue

        tl = win.title.lower()
        el = os.path.splitext(win.exe)[0].lower() if win.exe else ""

        # Avoid grabbing a browser tab if term is not a browser
        browser_exes = ("chrome", "msedge", "firefox", "brave", "opera", "vivaldi")
        if not allow_browser and el in browser_exes and clean_term not in el:
            continue

        if clean_term in tl or clean_term == el:
            candidates.append(win)

    if not candidates:
        return None

    # Pick the most specific (shortest) matching title
    best = min(candidates, key=lambda w: len(w.title))

    user32 = ctypes.windll.user32
    if user32.IsIconic(best.hwnd):
        user32.ShowWindow(best.hwnd, SW_RESTORE)
    user32.SwitchToThisWindow(best.hwnd, True)

    return best.title


def close_window(term: str) -> tuple[bool, str]:
    """Gracefully close a window matching `term` by posting a WM_CLOSE message.

    Never force-kills; allows the target application to prompt for unsaved changes.
    """
    if sys.platform != "win32":
        return False, "Window closing is only available on Windows"

    import ctypes

    clean_term = (term or "").strip().lower()
    if not clean_term:
        return False, "No window name specified"

    from kural.control.guardrails import default_guardrails

    if default_guardrails.is_protected_target(clean_term):
        return (
            False,
            f"Target '{clean_term}' is protected system infrastructure and cannot be closed.",
        )

    target_win = None
    for win in list_windows():
        if default_guardrails.is_protected_target(win.exe):
            continue
        tl = win.title.lower()
        el = os.path.splitext(win.exe)[0].lower() if win.exe else ""
        if clean_term in tl or clean_term == el:
            target_win = win
            break

    if not target_win:
        return False, f"No open window matching '{term}' found"

    # Post WM_CLOSE message
    user32 = ctypes.windll.user32
    user32.PostMessageW(target_win.hwnd, WM_CLOSE, 0, 0)
    logger.info(f"Posted WM_CLOSE to '{target_win.title}' (HWND: {target_win.hwnd:#x})")
    return True, f"Closing {target_win.title}"


def set_window_state(action: str) -> tuple[bool, str]:
    """Modify the state of the active foreground window (minimize, maximize, snap left/right, show desktop)."""
    if sys.platform != "win32":
        return False, "Window state operations are only available on Windows"

    import ctypes

    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd and action != "show_desktop":
        return False, "No active foreground window found"

    act = action.strip().lower()

    if act == "minimize":
        user32.ShowWindow(hwnd, SW_MINIMIZE)
        return True, "Minimized window"

    if act == "maximize":
        user32.ShowWindow(hwnd, SW_MAXIMIZE)
        return True, "Maximized window"

    if act == "restore":
        user32.ShowWindow(hwnd, SW_RESTORE)
        return True, "Restored window"

    # Key combination simulation for snap operations
    def _press_keys(*keys):
        for k in keys:
            user32.keybd_event(k, 0, 0, 0)
        for k in reversed(keys):
            user32.keybd_event(k, 0, KEYEVENTF_KEYUP, 0)

    if act in ("snap_left", "snap left"):
        _press_keys(VK_LWIN, VK_LEFT)
        return True, "Snapped window left"

    if act in ("snap_right", "snap right"):
        _press_keys(VK_LWIN, VK_RIGHT)
        return True, "Snapped window right"

    if act in ("show_desktop", "desktop"):
        _press_keys(VK_LWIN, VK_D)
        return True, "Showing desktop"

    return False, f"Unknown window action: {action}"


def is_window_elevated(hwnd: int) -> bool:
    """Check whether the process owning `hwnd` is running with elevated (Administrator) privileges.

    Under Windows UIPI, standard-privilege applications cannot send synthetic input
    (SendInput, keybd_event, WM_CLOSE) to elevated windows.
    """
    if sys.platform != "win32" or not hwnd:
        return False

    import ctypes
    import ctypes.wintypes as wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    advapi32 = ctypes.windll.advapi32

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return False

    # PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    h_proc = kernel32.OpenProcess(0x1000, False, pid.value)
    if not h_proc:
        return False

    h_token = wintypes.HANDLE()
    # TOKEN_QUERY = 0x0008
    elevated = False
    if advapi32.OpenProcessToken(h_proc, 0x0008, ctypes.byref(h_token)):
        # TokenElevation = 20
        elevation = wintypes.DWORD()
        ret_len = wintypes.DWORD()
        if advapi32.GetTokenInformation(
            h_token, 20, ctypes.byref(elevation), ctypes.sizeof(elevation), ctypes.byref(ret_len)
        ):
            elevated = bool(elevation.value)
        kernel32.CloseHandle(h_token)
    kernel32.CloseHandle(h_proc)

    return elevated


def get_foreground_window_info() -> WindowInfo | None:
    """Get the title and executable name of the current foreground window."""
    if sys.platform != "win32":
        return None

    import ctypes
    import ctypes.wintypes as wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None

    length = user32.GetWindowTextLengthW(hwnd)
    title = ""
    if length > 0:
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value.strip()

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    exe = ""
    if pid.value:
        h_proc = kernel32.OpenProcess(0x1000, False, pid.value)
        if h_proc:
            size = wintypes.DWORD(260)
            path_buf = ctypes.create_unicode_buffer(260)
            if kernel32.QueryFullProcessImageNameW(h_proc, 0, path_buf, ctypes.byref(size)):
                exe = os.path.basename(path_buf.value)
            kernel32.CloseHandle(h_proc)

    return WindowInfo(hwnd=hwnd, title=title, exe=exe)


def check_foreground_elevation() -> tuple[bool, str]:
    """Check if the current foreground window is elevated, returning (is_elevated, warning_message)."""
    if sys.platform != "win32":
        return False, ""

    import ctypes

    hwnd = ctypes.windll.user32.GetForegroundWindow()
    if not hwnd:
        return False, ""

    if is_window_elevated(hwnd):
        msg = (
            "The active window is running as Administrator. Windows UIPI blocks "
            "synthetic keystrokes to elevated windows unless Kural is also launched as Administrator."
        )
        logger.warning(msg)
        return True, msg

    return False, ""


def insert_text_at_caret(text: str, restore_clipboard_delay: float = 0.05) -> bool:
    """Insert text at the current cursor position by pasting (Ctrl+V) via clipboard.

    Preserves existing clipboard contents and checks for elevated windows before pasting.
    """
    if not text:
        return False

    is_elev, warn_msg = check_foreground_elevation()
    if is_elev:
        print(f"⚠️  {warn_msg}")

    if sys.platform != "win32":
        return False

    import ctypes
    import time

    # Optional pyperclip for Unicode clipboard handling
    saved_clipboard = None
    try:
        import pyperclip

        try:
            saved_clipboard = pyperclip.paste()
        except Exception:
            saved_clipboard = None

        pyperclip.copy(text)
    except ImportError:
        # Minimal ctypes clipboard fallback
        pass

    # Simulate Ctrl+V keypress
    user32 = ctypes.windll.user32
    VK_CONTROL = 0x11
    VK_V = 0x56

    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_V, 0, 0, 0)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    # Restore prior clipboard content if pyperclip was available
    if saved_clipboard is not None:

        def _restore():
            time.sleep(restore_clipboard_delay)
            try:
                import pyperclip

                pyperclip.copy(saved_clipboard)
            except Exception:
                pass

        import threading

        threading.Thread(target=_restore, daemon=True, name="clipboard-restore").start()

    return True


def get_selected_text(timeout: float = 0.1) -> str:
    """Capture currently selected/highlighted text across any Windows application.

    Simulates Ctrl+C and reads clipboard, gracefully restoring the clipboard
    after extraction.
    """
    if sys.platform != "win32":
        return ""

    import ctypes
    import time

    saved = None
    try:
        import pyperclip

        with contextlib.suppress(Exception):
            saved = pyperclip.paste()
        pyperclip.copy("")
    except ImportError:
        pass

    user32 = ctypes.windll.user32
    VK_CONTROL = 0x11
    VK_C = 0x43
    KEYEVENTF_KEYUP = 0x0002

    # Simulate Ctrl+C
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_C, 0, 0, 0)
    user32.keybd_event(VK_C, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    time.sleep(timeout)

    captured = ""
    try:
        import pyperclip

        with contextlib.suppress(Exception):
            captured = pyperclip.paste() or ""
        # Restore prior clipboard if we changed it
        if saved is not None:
            with contextlib.suppress(Exception):
                pyperclip.copy(saved)
    except ImportError:
        pass

    return captured.strip()
