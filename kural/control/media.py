# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported from ROHITCRAFTSYT/WhispLocal/whisp/volume.py
"""System audio volume and media transport control for Windows.

Uses the Windows Core Audio API (IAudioEndpointVolume) for accurate master volume
adjustment, and Windows virtual-key events for media playback (play/pause, next, previous).
"""

import ctypes
import logging
import sys
from ctypes import (
    POINTER,
    WINFUNCTYPE,
    Structure,
    byref,
    c_float,
    c_long,
    c_ubyte,
    c_ulong,
    c_ushort,
    c_void_p,
    cast,
)

logger = logging.getLogger(__name__)

# Windows virtual keys for media transport
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002

CLSCTX_ALL = 0x17
ERender, EConsole = 0, 0
HRESULT = c_long


class _GUID(Structure):
    _fields_ = [
        ("Data1", c_ulong),
        ("Data2", c_ushort),
        ("Data3", c_ushort),
        ("Data4", c_ubyte * 8),
    ]


def _guid(d1, d2, d3, d4):
    return _GUID(d1, d2, d3, (c_ubyte * 8)(*d4))


CLSID_MMDEVICE_ENUMERATOR = _guid(
    0xBCDE0395, 0xE52F, 0x467C, (0x8E, 0x3D, 0xC4, 0x57, 0x92, 0x91, 0x69, 0x2E)
)
IID_DEVICE_ENUMERATOR = _guid(
    0xA95664D2, 0x9614, 0x4F35, (0xA7, 0x46, 0xDE, 0x8D, 0xB6, 0x36, 0x17, 0xE6)
)
IID_AUDIO_ENDPOINT_VOLUME = _guid(
    0x5CDF2C82, 0x841E, 0x4546, (0x97, 0x22, 0x0C, 0xF7, 0x40, 0x78, 0x22, 0x9A)
)


def _vtbl(obj):
    return cast(obj, POINTER(POINTER(c_void_p))).contents


def _vmethod(obj, index, restype, *argtypes):
    func = cast(_vtbl(obj)[index], WINFUNCTYPE(restype, c_void_p, *argtypes))
    return func


def _endpoint_volume():
    """Acquire IAudioEndpointVolume interface for default playback device."""
    if sys.platform != "win32":
        return None
    try:
        ole32 = ctypes.windll.ole32
        ole32.CoInitialize(None)
        ole32.CoCreateInstance.argtypes = [
            POINTER(_GUID),
            c_void_p,
            c_ulong,
            POINTER(_GUID),
            POINTER(c_void_p),
        ]
        ole32.CoCreateInstance.restype = HRESULT

        p_enum = c_void_p()
        hr = ole32.CoCreateInstance(
            byref(CLSID_MMDEVICE_ENUMERATOR),
            None,
            CLSCTX_ALL,
            byref(IID_DEVICE_ENUMERATOR),
            byref(p_enum),
        )
        if hr < 0 or not p_enum:
            return None

        p_device = c_void_p()
        get_default = _vmethod(p_enum, 4, HRESULT, ctypes.c_int, ctypes.c_int, POINTER(c_void_p))
        if get_default(p_enum, ERender, EConsole, byref(p_device)) < 0 or not p_device:
            return None

        p_volume = c_void_p()
        activate = _vmethod(
            p_device,
            3,
            HRESULT,
            POINTER(_GUID),
            c_ulong,
            c_void_p,
            POINTER(c_void_p),
        )
        if (
            activate(p_device, byref(IID_AUDIO_ENDPOINT_VOLUME), CLSCTX_ALL, None, byref(p_volume))
            < 0
            or not p_volume
        ):
            return None

        return p_volume
    except Exception as e:
        logger.debug(f"CoreAudio volume endpoint unavailable: {e}")
        return None


def get_volume() -> int | None:
    """Return the current system volume level (0-100), or None if unavailable."""
    p_volume = _endpoint_volume()
    if p_volume is None:
        return None
    try:
        level = c_float()
        get_scalar = _vmethod(p_volume, 9, HRESULT, POINTER(c_float))
        if get_scalar(p_volume, byref(level)) < 0:
            return None
        return int(round(max(0.0, min(1.0, level.value)) * 100))
    except Exception:
        return None


def set_volume(level: int) -> int:
    """Set master system volume to a percentage (0-100). Returns new level."""
    target = max(0, min(100, int(level)))
    p_volume = _endpoint_volume()
    if p_volume is not None:
        lvl = target / 100.0
        set_scalar = _vmethod(p_volume, 7, HRESULT, c_float, c_void_p)
        hr = set_scalar(p_volume, lvl, None)
        if hr < 0:
            logger.warning(f"SetMasterVolumeLevelScalar failed (hr={hr:#x})")
    return target


def change_volume(delta: int) -> int:
    """Adjust system volume by delta percentage. Returns new volume level."""
    curr = get_volume()
    if curr is None:
        curr = 50
    return set_volume(curr + delta)


def _send_vk(vk_code: int) -> None:
    """Simulate a Windows key press and release using keybd_event."""
    if sys.platform != "win32":
        return
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, 0, 0)
        user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
    except Exception as e:
        logger.warning(f"Failed to send VK {vk_code}: {e}")


def toggle_mute() -> None:
    """Toggle system audio mute."""
    _send_vk(VK_VOLUME_MUTE)


def media_play_pause() -> None:
    """Toggle media play / pause."""
    _send_vk(VK_MEDIA_PLAY_PAUSE)


def media_next() -> None:
    """Skip to next media track."""
    _send_vk(VK_MEDIA_NEXT_TRACK)


def media_prev() -> None:
    """Skip to previous media track."""
    _send_vk(VK_MEDIA_PREV_TRACK)
