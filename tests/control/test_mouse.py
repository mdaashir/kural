"""Tests for kural.control.mouse — Win32 mouse button push-to-talk trigger."""

import ctypes
import time
from unittest.mock import MagicMock, patch

import pytest

from kural.control.mouse import (
    BUTTONS,
    MSLLHOOKSTRUCT,
    WM_MBUTTONDOWN,
    WM_MBUTTONUP,
    WM_XBUTTONDOWN,
    WM_XBUTTONUP,
    XBUTTON1,
    XBUTTON2,
    MouseButtonTrigger,
    decode_mouse_event,
)


class TestMouseEventDecoding:
    def test_decode_middle_button(self):
        btn, pressed = decode_mouse_event(WM_MBUTTONDOWN, 0)
        assert btn == "middle"
        assert pressed is True

        btn, pressed = decode_mouse_event(WM_MBUTTONUP, 0)
        assert btn == "middle"
        assert pressed is False

    def test_decode_xbuttons(self):
        hook_info = MSLLHOOKSTRUCT()
        hook_info.mouseData = XBUTTON1 << 16
        ptr = ctypes.pointer(hook_info)
        lparam = ctypes.cast(ptr, ctypes.c_void_p).value

        btn, pressed = decode_mouse_event(WM_XBUTTONDOWN, lparam)
        assert btn == "x1"
        assert pressed is True

        hook_info.mouseData = XBUTTON2 << 16
        btn, pressed = decode_mouse_event(WM_XBUTTONUP, lparam)
        assert btn == "x2"
        assert pressed is False

    def test_decode_unrelated_message_returns_none(self):
        btn, pressed = decode_mouse_event(0x0200, 0)  # WM_MOUSEMOVE
        assert btn is None
        assert pressed is None


class TestMouseButtonTriggerHook:
    def test_invalid_button_raises(self):
        with pytest.raises(ValueError, match="Unknown mouse button"):
            MouseButtonTrigger("invalid_btn", lambda: None, lambda: None)

    def test_valid_buttons_mapped(self):
        for name in BUTTONS:
            trigger = MouseButtonTrigger(name, lambda: None, lambda: None)
            assert trigger.buttons == BUTTONS[name]

    def test_hook_proc_swallows_event_and_calls_press_release(self):
        on_press = MagicMock()
        on_release = MagicMock()
        trigger = MouseButtonTrigger("x1", on_press, on_release)

        with patch("kural.control.mouse.decode_mouse_event", return_value=("x1", True)):
            res = trigger._hook_proc(0, WM_XBUTTONDOWN, 0)
            assert res == 1  # Swallowed!
            time.sleep(0.05)
            on_press.assert_called_once()
            assert "x1" in trigger._held

        with patch("kural.control.mouse.decode_mouse_event", return_value=("x1", False)):
            res = trigger._hook_proc(0, WM_XBUTTONUP, 0)
            assert res == 1  # Swallowed!
            time.sleep(0.05)
            on_release.assert_called_once()
            assert "x1" not in trigger._held

    def test_hook_proc_ignores_unconfigured_button(self):
        trigger = MouseButtonTrigger("x1", lambda: None, lambda: None)

        with (
            patch("kural.control.mouse.decode_mouse_event", return_value=("middle", True)),
            patch("ctypes.WinDLL") as mock_dll,
        ):
            mock_user32 = MagicMock()
            mock_user32.CallNextHookEx.return_value = 0
            mock_dll.return_value = mock_user32

            res = trigger._hook_proc(0, WM_MBUTTONDOWN, 0)
            assert res == 0  # Passed through to CallNextHookEx
