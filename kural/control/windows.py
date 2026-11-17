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


def type_text_at_caret(text: str) -> bool:
    """Type text directly as OS-level Unicode key events using SendInput.

    Bypasses the Windows clipboard entirely. Works in apps where Ctrl+V is
    blocked or when the clipboard is locked by another process. Properly
    encodes multi-byte Unicode (including Tamil glyphs) and newlines.
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
    from ctypes import wintypes

    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004
    VK_RETURN = 0x0D

    class _KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_size_t),
        ]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [("ki", _KEYBDINPUT)]

    class _INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]

    def _build_events(ch: str):
        events = []
        if ch == "\n":
            events.append((VK_RETURN, 0, 0))
            events.append((VK_RETURN, 0, KEYEVENTF_KEYUP))
        else:
            utf16_units = [
                int.from_bytes(ch.encode("utf-16-le")[i : i + 2], "little")
                for i in range(0, len(ch.encode("utf-16-le")), 2)
            ]
            for u in utf16_units:
                events.append((0, u, KEYEVENTF_UNICODE))
                events.append((0, u, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))
        return events

    user32 = ctypes.windll.user32
    for char in text.replace("\r\n", "\n"):
        char_events = _build_events(char)
        arr = (_INPUT * len(char_events))()
        for idx, (vk, scan, flags) in enumerate(char_events):
            arr[idx].type = INPUT_KEYBOARD
            arr[idx].u.ki = _KEYBDINPUT(vk, scan, flags, 0, 0)
        user32.SendInput(len(char_events), arr, ctypes.sizeof(_INPUT))
        time.sleep(0.015)

    return True


def insert_text_at_caret(
    text: str,
    delivery_method: str = "paste",
    restore_clipboard_delay: float = 0.05,
) -> bool:
    """Insert text at the current cursor position.

    Strategies:
    - 'paste' (default): places text on clipboard and sends Ctrl+V, then restores
      the user's prior clipboard. Falls back to 'type' if clipboard access fails.
    - 'type': sends keystrokes directly via SendInput KEYEVENTF_UNICODE without
      touching the clipboard buffer.
    """
    if not text:
        return False

    if delivery_method == "type":
        return type_text_at_caret(text)

    is_elev, warn_msg = check_foreground_elevation()
    if is_elev:
        print(f"⚠️  {warn_msg}")

    if sys.platform != "win32":
        return False

    import ctypes
    import time

    saved_clipboard = None
    clipboard_succeeded = False

    try:
        import pyperclip

        try:
            saved_clipboard = pyperclip.paste()
        except Exception:
            saved_clipboard = None

        pyperclip.copy(text)
        clipboard_succeeded = True
    except Exception as e:
        logger.debug(f"Clipboard access failed, falling back to direct typing: {e}")

    # If clipboard copy failed (e.g. locked by another app), fall back to typing
    if not clipboard_succeeded:
        return type_text_at_caret(text)

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


def get_text_before_caret(max_chars: int = 120) -> str | None:
    """Read the text immediately to the left of the active caret in the foreground control.

    Uses Win32 GUI thread info and standard Edit/RichEdit messages (WM_GETTEXT, EM_GETSEL).
    Returns None if the control is not an accessible text field or if in a password field.
    Never raises an exception.
    """
    if sys.platform != "win32":
        return None

    try:
        import ctypes
        import ctypes.wintypes as wintypes

        class _RECT(ctypes.Structure):
            _fields_ = [
                ("left", wintypes.LONG),
                ("top", wintypes.LONG),
                ("right", wintypes.LONG),
                ("bottom", wintypes.LONG),
            ]

        class _GUITHREADINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("hwndActive", wintypes.HWND),
                ("hwndFocus", wintypes.HWND),
                ("hwndCapture", wintypes.HWND),
                ("hwndMenuOwner", wintypes.HWND),
                ("hwndMoveSize", wintypes.HWND),
                ("hwndCaret", wintypes.HWND),
                ("rcCaret", _RECT),
            ]

        user32 = ctypes.windll.user32
        hwnd_fg = user32.GetForegroundWindow()
        if not hwnd_fg:
            return None

        # Resolve focused child control
        tid = user32.GetWindowThreadProcessId(hwnd_fg, None)
        gui_info = _GUITHREADINFO(cbSize=ctypes.sizeof(_GUITHREADINFO))
        target_hwnd = hwnd_fg
        if user32.GetGUIThreadInfo(tid, ctypes.byref(gui_info)) and gui_info.hwndFocus:
            target_hwnd = gui_info.hwndFocus

        # Never inspect password fields (GWL_STYLE & ES_PASSWORD)
        GWL_STYLE = -16
        ES_PASSWORD = 0x0020
        style = user32.GetWindowLongW(target_hwnd, GWL_STYLE)
        if style & ES_PASSWORD:
            return None

        # Query text length with timeout
        WM_GETTEXTLENGTH = 0x000E
        WM_GETTEXT = 0x000D
        EM_GETSEL = 0x00B0
        SMTO_ABORTIFHUNG = 0x0002

        res_len = ctypes.c_size_t()
        if not user32.SendMessageTimeoutW(
            target_hwnd, WM_GETTEXTLENGTH, 0, 0, SMTO_ABORTIFHUNG, 100, ctypes.byref(res_len)
        ):
            return None

        length = res_len.value
        if length == 0:
            return ""

        buf = ctypes.create_unicode_buffer(length + 1)
        res_text = ctypes.c_size_t()
        if not user32.SendMessageTimeoutW(
            target_hwnd,
            WM_GETTEXT,
            length + 1,
            ctypes.addressof(buf),
            SMTO_ABORTIFHUNG,
            100,
            ctypes.byref(res_text),
        ):
            return None

        full_text = buf.value

        # Query caret selection start position
        res_sel = ctypes.c_size_t()
        if not user32.SendMessageTimeoutW(
            target_hwnd, EM_GETSEL, 0, 0, SMTO_ABORTIFHUNG, 100, ctypes.byref(res_sel)
        ):
            return None

        start_pos = res_sel.value & 0xFFFF
        if start_pos > length:
            start_pos = length

        return full_text[max(0, start_pos - max_chars) : start_pos]
    except Exception as e:
        logger.debug(f"Could not read text before caret: {e}")
        return None
