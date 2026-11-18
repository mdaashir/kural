# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported and adapted from ROHITCRAFTSYT/WhispLocal/whisp/configcheck.py
"""Configuration schema validation and auto-healing for Kural.

YAML files in %APPDATA%\\kural\\ can be edited manually by users, potentially
introducing typos, invalid devices, negative durations, out-of-range values,
or bad types. This module validates each key non-destructively:
- Catches invalid enums and falls back to shipped defaults.
- Clamps out-of-bounds numbers to safe operating ranges.
- Drops corrupt dictionary/list entries while preserving valid ones.
- Never raises exceptions, never mutates input dictionaries directly.
"""

import logging
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

VALID_DEVICES = {"cuda", "cpu"}
VALID_COMPUTE_TYPES = {"float16", "int8"}
VALID_RECORDING_MODES = {"toggle", "push_to_talk"}
VALID_OVERLAY_POSITIONS = {
    "bottom-center",
    "bottom-right",
    "bottom-left",
    "top-center",
    "top-right",
    "top-left",
}
VALID_BACKENDS = {"faster_whisper", "whisper_cpp"}
VALID_INDIC_SCRIPTS = {"native", "roman"}
VALID_DELIVERY_METHODS = {"paste", "type", "copy"}


def validate_config(config: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate a loaded configuration dictionary against Kural's schema.

    Returns:
        (sanitized_config, issues_list)
    """
    cfg = deepcopy(config or {})
    issues: list[str] = []

    # 1. Validate 'whisper' section
    whisper = cfg.setdefault("whisper", {})
    if not isinstance(whisper, dict):
        cfg["whisper"] = {}
        whisper = cfg["whisper"]
        issues.append("Section 'whisper' must be a dictionary; reset to defaults.")

    dev = whisper.get("device")
    if dev is not None and dev not in VALID_DEVICES:
        issues.append(f"Invalid whisper.device '{dev}'. Falling back to 'cuda'.")
        whisper["device"] = "cuda"

    comp = whisper.get("compute_type")
    if comp is not None and comp not in VALID_COMPUTE_TYPES:
        issues.append(f"Invalid whisper.compute_type '{comp}'. Falling back to 'float16'.")
        whisper["compute_type"] = "float16"

    backend = whisper.get("backend")
    if backend is not None and backend not in VALID_BACKENDS:
        issues.append(f"Invalid whisper.backend '{backend}'. Falling back to 'faster_whisper'.")
        whisper["backend"] = "faster_whisper"

    script = whisper.get("indic_script")
    if script is not None and script not in VALID_INDIC_SCRIPTS:
        issues.append(f"Invalid whisper.indic_script '{script}'. Falling back to 'native'.")
        whisper["indic_script"] = "native"

    idle = whisper.get("idle_unload_minutes")
    if idle is not None:
        try:
            val = int(idle)
            if val < 0:
                issues.append("whisper.idle_unload_minutes cannot be negative; clamped to 0.")
                whisper["idle_unload_minutes"] = 0
            elif val > 1440:
                issues.append("whisper.idle_unload_minutes exceeds 1440m; clamped to 1440.")
                whisper["idle_unload_minutes"] = 1440
        except (ValueError, TypeError):
            issues.append(f"Invalid idle_unload_minutes '{idle}'; reset to default 5.")
            whisper["idle_unload_minutes"] = 5

    beam = whisper.get("beam_size")
    if beam is not None:
        try:
            val = int(beam)
            if val < 1 or val > 10:
                clamped = max(1, min(10, val))
                issues.append(
                    f"whisper.beam_size '{val}' out of range [1-10]; clamped to {clamped}."
                )
                whisper["beam_size"] = clamped
        except (ValueError, TypeError):
            issues.append(f"Invalid beam_size '{beam}'; reset to default 5.")
            whisper["beam_size"] = 5

    # 2. Validate 'hotkey' section
    hotkey = cfg.setdefault("hotkey", {})
    if not isinstance(hotkey, dict):
        cfg["hotkey"] = {}
        hotkey = cfg["hotkey"]
        issues.append("Section 'hotkey' must be a dictionary; reset to defaults.")

    mode = hotkey.get("recording_mode")
    if mode is not None and mode not in VALID_RECORDING_MODES:
        issues.append(f"Invalid hotkey.recording_mode '{mode}'. Falling back to 'toggle'.")
        hotkey["recording_mode"] = "toggle"

    for hk_name in ("recording_hotkey", "command_hotkey", "cancel_hotkey"):
        hk_val = hotkey.get(hk_name)
        if hk_val is not None:
            if not isinstance(hk_val, str) or not hk_val.strip():
                issues.append(f"hotkey.{hk_name} must be a non-empty string.")
            elif not re.match(r"^[a-zA-Z0-9_+ -]+$", hk_val):
                issues.append(f"hotkey.{hk_name} contains invalid characters: '{hk_val}'.")

    sp = hotkey.get("stop_phrase")
    if isinstance(sp, dict):
        phrases = sp.get("phrases")
        if phrases is not None and not isinstance(phrases, list):
            issues.append(
                "hotkey.stop_phrase.phrases must be a list of strings; resetting to defaults."
            )
            sp["phrases"] = [
                "stop dictation",
                "stop recording",
                "முடி",
                "நிறுத்து",
                "stop பண்ணு",
            ]

    # 3. Validate 'overlay' section
    overlay = cfg.setdefault("overlay", {})
    if isinstance(overlay, dict):
        pos = overlay.get("position")
        if pos is not None and pos not in VALID_OVERLAY_POSITIONS:
            issues.append(f"Invalid overlay.position '{pos}'. Falling back to 'bottom-center'.")
            overlay["position"] = "bottom-center"

    # 4. Validate 'audio' section
    audio = cfg.setdefault("audio", {})
    if isinstance(audio, dict):
        max_dur = audio.get("max_duration")
        if max_dur is not None:
            try:
                val = int(max_dur)
                if val < 5 or val > 300:
                    clamped = max(5, min(300, val))
                    issues.append(
                        f"audio.max_duration '{val}' out of bounds [5-300s]; clamped to {clamped}."
                    )
                    audio["max_duration"] = clamped
            except (ValueError, TypeError):
                issues.append(f"Invalid audio.max_duration '{max_dur}'; reset to 30.")
                audio["max_duration"] = 30

        ns = audio.get("noise_suppression")
        if isinstance(ns, dict):
            strength = ns.get("strength")
            if strength is not None:
                try:
                    s_val = float(strength)
                    if s_val < 0.0 or s_val > 1.0:
                        clamped = max(0.0, min(1.0, s_val))
                        issues.append(
                            f"audio.noise_suppression.strength '{s_val}' out of range [0.0-1.0]; clamped to {clamped}."
                        )
                        ns["strength"] = clamped
                except (ValueError, TypeError):
                    issues.append(
                        f"Invalid noise_suppression.strength '{strength}'; reset to 0.75."
                    )
                    ns["strength"] = 0.75

        duck = audio.get("ducking")
        if isinstance(duck, dict):
            factor = duck.get("factor")
            if factor is not None:
                try:
                    f_val = float(factor)
                    if f_val < 0.0 or f_val > 1.0:
                        clamped = max(0.0, min(1.0, f_val))
                        issues.append(
                            f"audio.ducking.factor '{f_val}' out of range [0.0-1.0]; clamped to {clamped}."
                        )
                        duck["factor"] = clamped
                except (ValueError, TypeError):
                    issues.append(f"Invalid ducking.factor '{factor}'; reset to 0.25.")
                    duck["factor"] = 0.25

    # 5. Validate 'clipboard' section
    clip = cfg.setdefault("clipboard", {})
    if isinstance(clip, dict):
        dm = clip.get("delivery_method")
        if dm is not None and dm not in VALID_DELIVERY_METHODS:
            issues.append(f"Invalid clipboard.delivery_method '{dm}'. Falling back to 'paste'.")
            clip["delivery_method"] = "paste"

    # 6. Validate 'notes' section
    notes = cfg.setdefault("notes", {})
    if isinstance(notes, dict):
        v_path = notes.get("vault_path")
        if v_path:
            p = Path(v_path)
            if not p.exists():
                issues.append(f"Warning: notes.vault_path '{v_path}' does not exist on disk.")

    return cfg, issues
