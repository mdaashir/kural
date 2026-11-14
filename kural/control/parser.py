# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported from ROHITCRAFTSYT/WhispLocal/whisp/commands.py
"""Pure command intent parser with second-pass misheard verb recovery."""

import re
from dataclasses import dataclass

# Polite prefixes and filler phrases commonly prefixed by voice
_FILLER_PREFIX = re.compile(
    r"^(?:please|hey|ok|okay|can you|could you|would you|system|kural)\s+",
    re.IGNORECASE,
)

# Polite trailing phrases
_TRAILER = re.compile(
    r"\s+(?:please|pls|okay|ok|thanks|thank you)\s*$",
    re.IGNORECASE,
)

# Common mishearings for leading command verbs by Whisper
_VERB_REPLACEMENTS = [
    (re.compile(r"^(?:oben|poen|open up)\b", re.I), "open"),
    (re.compile(r"^(?:swich|swtich|change to)\b", re.I), "switch to"),
    (re.compile(r"^(?:clsoe|clsoing)\b", re.I), "close"),
    (re.compile(r"^(?:minmize|minimise)\b", re.I), "minimize"),
    (re.compile(r"^(?:maxmize|maximise)\b", re.I), "maximize"),
]


@dataclass
class CommandIntent:
    """Structured representation of a parsed voice command intent."""

    kind: str  # open_app, switch_app, close_app, media, volume, window_op, web_search, system
    action: str
    target: str = ""
    raw_text: str = ""


def normalize_command_text(text: str) -> str:
    """Clean filler words, punctuation, and politeness artifacts from spoken command."""
    if not text:
        return ""
    t = text.strip().lower()
    t = re.sub(r"[!?,]", " ", t).rstrip(".")
    t = t.replace("you tube", "youtube")
    t = _TRAILER.sub("", t)

    while True:
        t2 = _FILLER_PREFIX.sub("", t)
        if t2 == t:
            break
        t = t2

    # Second-pass leading verb repair for minor mishearings
    for pattern, canonical in _VERB_REPLACEMENTS:
        if pattern.search(t):
            t = pattern.sub(canonical, t, count=1)
            break

    return " ".join(t.split())


def parse_command(phrase: str) -> CommandIntent | None:
    """Parse a spoken phrase into a CommandIntent, or None if not recognized as a voice command."""
    t = normalize_command_text(phrase)
    if not t:
        return None

    # 1. Media transport controls
    if t in ("play", "pause", "play pause", "resume"):
        return CommandIntent(kind="media", action="play_pause", raw_text=phrase)
    if t in ("next song", "next track", "skip", "skip song"):
        return CommandIntent(kind="media", action="next", raw_text=phrase)
    if t in ("previous song", "previous track", "prev song"):
        return CommandIntent(kind="media", action="prev", raw_text=phrase)
    if t in ("mute", "unmute", "mute audio", "silence"):
        return CommandIntent(kind="media", action="mute", raw_text=phrase)

    # 2. Volume adjustments
    if t in ("volume up", "increase volume", "turn it up", "louder"):
        return CommandIntent(kind="volume", action="up", target="10", raw_text=phrase)
    if t in ("volume down", "decrease volume", "turn it down", "softer", "lower volume"):
        return CommandIntent(kind="volume", action="down", target="10", raw_text=phrase)

    m_vol = re.match(r"^(?:set volume to|volume)\s+(\d{1,3})(?:\s*%)?$", t)
    if m_vol:
        return CommandIntent(kind="volume", action="set", target=m_vol.group(1), raw_text=phrase)

    # 3. Window management
    if t in ("minimize", "minimize window", "minimize this"):
        return CommandIntent(kind="window_op", action="minimize", raw_text=phrase)
    if t in ("maximize", "maximize window", "maximize this"):
        return CommandIntent(kind="window_op", action="maximize", raw_text=phrase)
    if t in ("restore window", "restore this"):
        return CommandIntent(kind="window_op", action="restore", raw_text=phrase)
    if t in ("snap left", "snap window left", "snap to left"):
        return CommandIntent(kind="window_op", action="snap_left", raw_text=phrase)
    if t in ("snap right", "snap window right", "snap to right"):
        return CommandIntent(kind="window_op", action="snap_right", raw_text=phrase)
    if t in ("show desktop", "desktop", "go to desktop"):
        return CommandIntent(kind="window_op", action="show_desktop", raw_text=phrase)

    # 4. System power controls
    if t in ("shut down the computer", "shut down", "shutdown", "turn off the computer"):
        return CommandIntent(kind="system", action="shutdown", raw_text=phrase)
    if t in ("restart the computer", "restart computer", "reboot"):
        return CommandIntent(kind="system", action="restart", raw_text=phrase)
    if t in ("cancel shutdown", "abort shutdown", "stop shutdown"):
        return CommandIntent(kind="system", action="cancel_shutdown", raw_text=phrase)

    # 5. YouTube dedicated search
    m_yt = re.match(r"^(?:search|play|find)\s+(.+?)\s+(?:in|on)\s+youtube$", t)
    if m_yt:
        return CommandIntent(
            kind="web_search", action="youtube", target=m_yt.group(1).strip(), raw_text=phrase
        )

    m_yt2 = re.match(r"^open youtube and (?:search for|find|play)\s+(.+)$", t)
    if m_yt2:
        return CommandIntent(
            kind="web_search", action="youtube", target=m_yt2.group(1).strip(), raw_text=phrase
        )

    # 6. Web search
    m_search = re.match(r"^(?:search for|google|search)\s+(.+)$", t)
    if m_search:
        return CommandIntent(
            kind="web_search", action="google", target=m_search.group(1).strip(), raw_text=phrase
        )

    # 7. Window switching ("switch to chrome", "switch window to edge")
    m_switch = re.match(r"^(?:switch to|switch window to|focus|bring up)\s+(.+)$", t)
    if m_switch:
        target = m_switch.group(1).strip()
        return CommandIntent(kind="switch_app", action="switch", target=target, raw_text=phrase)

    # 8. Window / app closing ("close notepad", "exit chrome")
    m_close = re.match(r"^(?:close|exit|quit)\s+(.+)$", t)
    if m_close:
        target = m_close.group(1).strip()
        return CommandIntent(kind="close_app", action="close", target=target, raw_text=phrase)

    # 9. Application launching ("open notepad", "launch chrome")
    m_open = re.match(r"^(?:open|launch|start|run)\s+(.+)$", t)
    if m_open:
        target = m_open.group(1).strip()
        return CommandIntent(kind="open_app", action="open", target=target, raw_text=phrase)

    return None
