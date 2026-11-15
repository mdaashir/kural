# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported from ROHITCRAFTSYT/WhispLocal/whisp/commands.py
"""Pure command intent parser with second-pass misheard verb recovery."""

import re
from dataclasses import dataclass

# Polite prefixes and filler phrases commonly prefixed by voice (English + Tamil)
_FILLER_PREFIX = re.compile(
    r"^(?:please|hey|ok|okay|can you|could you|would you|system|kural|தயவுசெய்து|கொஞ்சம்|ப்ளீஸ்)\s+",
    re.IGNORECASE,
)

# Polite trailing phrases (English + Tamil)
_TRAILER = re.compile(
    r"\s+(?:please|pls|okay|ok|thanks|thank you|நன்றி)\s*$",
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

    # 1. Media transport controls (English + Tamil + Tanglish)
    if t in (
        "play",
        "pause",
        "play pause",
        "resume",
        "பாடலை இயக்கு",
        "பாடல் இயக்கு",
        "இசை இயக்கு",
        "பாடலை நிறுத்து",
        "பாடல் நிறுத்து",
        "இசை நிறுத்து",
        "பாட்டை நிறுத்து",
        "ப்ளே பண்ணு",
        "play பண்ணு",
        "நிறுத்து",
        "பாஸ் பண்ணு",
        "pause பண்ணு",
        "play pannu",
        "pause pannu",
    ):
        return CommandIntent(kind="media", action="play_pause", raw_text=phrase)
    if t in (
        "next song",
        "next track",
        "skip",
        "skip song",
        "அடுத்த பாடல்",
        "அடுத்த பாட்டு",
        "next பாட்டு",
        "next பாடல்",
        "next paattu",
    ):
        return CommandIntent(kind="media", action="next", raw_text=phrase)
    if t in (
        "previous song",
        "previous track",
        "prev song",
        "முந்தைய பாடல்",
        "முந்தைய பாட்டு",
        "previous பாட்டு",
        "prev பாடல்",
    ):
        return CommandIntent(kind="media", action="prev", raw_text=phrase)
    if t in (
        "mute",
        "unmute",
        "mute audio",
        "silence",
        "ஒலியை நிறுத்து",
        "சத்தத்தை நிறுத்து",
        "மியூட் பண்ணு",
        "mute பண்ணு",
        "mute pannu",
    ):
        return CommandIntent(kind="media", action="mute", raw_text=phrase)

    # 2. Volume adjustments (English + Tamil + Tanglish)
    if t in (
        "volume up",
        "increase volume",
        "turn it up",
        "louder",
        "சத்தம் ஏற்று",
        "சத்தத்தை ஏற்று",
        "சத்தம் கூட்டு",
        "சத்தத்தை கூட்டு",
        "வால்யூம் ஏத்து",
        "வால்யூம் கூட்டு",
        "சவுண்ட் ஏத்து",
        "sound ஏத்து",
        "sound aethu",
        "volume aethu",
    ):
        return CommandIntent(kind="volume", action="up", target="10", raw_text=phrase)

    # 3. Smart voice transforms / text rewrites (Wispr Flow style)
    m_transform = re.match(
        r"^(?:make\s+(?:that|this)\s+(?:a\s+)?|transform\s+(?:that|this)\s+(?:to\s+)?|rephrase\s+(?:that|this)\s+(?:to\s+)?)(.+)$",
        t,
    )
    if m_transform:
        return CommandIntent(
            kind="transform", action="rewrite", target=m_transform.group(1).strip(), raw_text=phrase
        )

    if t in (
        "bullet that",
        "make bullets",
        "make that bullets",
        "bulletize",
        "bullet list",
        "வரிசைப்படுத்து",
    ):
        return CommandIntent(kind="transform", action="rewrite", target="bullets", raw_text=phrase)

    if t in ("title case that", "make title case", "தலைப்பாக்கு"):
        return CommandIntent(
            kind="transform", action="rewrite", target="title_case", raw_text=phrase
        )

    if t in ("uppercase that", "make uppercase", "பெரிய எழுத்தாக்கு"):
        return CommandIntent(
            kind="transform", action="rewrite", target="uppercase", raw_text=phrase
        )

    if t in ("lowercase that", "make lowercase", "சிறிய எழுத்தாக்கு"):
        return CommandIntent(
            kind="transform", action="rewrite", target="lowercase", raw_text=phrase
        )
    if t in (
        "volume down",
        "decrease volume",
        "turn it down",
        "softer",
        "lower volume",
        "சத்தம் குறை",
        "சத்தத்தை குறை",
        "வால்யூம் குறை",
        "சவுண்ட் குறை",
        "sound குறை",
        "sound kura",
        "volume kura",
    ):
        return CommandIntent(kind="volume", action="down", target="10", raw_text=phrase)

    m_vol = re.match(r"^(?:set volume to|volume|வால்யூம்|சத்தம்)\s+(\d{1,3})(?:\s*%)?$", t)
    if m_vol:
        return CommandIntent(kind="volume", action="set", target=m_vol.group(1), raw_text=phrase)

    # 3. Window management (English + Tamil + Tanglish)
    if t in (
        "minimize",
        "minimize window",
        "minimize this",
        "மினிமைஸ் பண்ணு",
        "சிறிதாக்கு",
        "minimize பண்ணு",
        "minimize pannu",
    ):
        return CommandIntent(kind="window_op", action="minimize", raw_text=phrase)
    if t in (
        "maximize",
        "maximize window",
        "maximize this",
        "பெரிதாக்கு",
        "மேக்சிமைஸ் பண்ணு",
        "maximize பண்ணு",
        "maximize pannu",
    ):
        return CommandIntent(kind="window_op", action="maximize", raw_text=phrase)
    if t in ("restore window", "restore this", "மீட்டமை"):
        return CommandIntent(kind="window_op", action="restore", raw_text=phrase)
    if t in (
        "snap left",
        "snap window left",
        "snap to left",
        "இடதுபக்கம் மாற்று",
        "இடது பக்கம் வை",
        "snap left பண்ணு",
    ):
        return CommandIntent(kind="window_op", action="snap_left", raw_text=phrase)
    if t in (
        "snap right",
        "snap window right",
        "snap to right",
        "வலதுபக்கம் மாற்று",
        "வலது பக்கம் வை",
        "snap right பண்ணு",
    ):
        return CommandIntent(kind="window_op", action="snap_right", raw_text=phrase)
    if t in (
        "show desktop",
        "desktop",
        "go to desktop",
        "டெஸ்க்டாப் காட்டு",
        "desktop காட்டு",
        "desktop kaatu",
    ):
        return CommandIntent(kind="window_op", action="show_desktop", raw_text=phrase)

    # 4. Never-lose-a-dictation recovery & recall
    if t in (
        "paste last dictation",
        "paste that again",
        "paste last",
        "paste previous",
        "கடைசி உரையை தட்டச்சு செய்",
        "மீண்டும் தட்டச்சு செய்",
        "மறுபடியும் தட்டச்சு செய்",
    ):
        return CommandIntent(kind="system", action="paste_last", raw_text=phrase)
    if t in (
        "retry last take",
        "retry last dictation",
        "retry last",
        "கடைசி பதிவை மீண்டும் செய்",
    ):
        return CommandIntent(kind="system", action="retry_last", raw_text=phrase)

    # 5. System power controls (English + Tamil + Tanglish)
    if t in (
        "shut down the computer",
        "shut down",
        "shutdown",
        "turn off the computer",
        "கணினியை அணை",
        "கம்ப்யூட்டரை ஆஃப் பண்ணு",
        "shutdown பண்ணு",
    ):
        return CommandIntent(kind="system", action="shutdown", raw_text=phrase)
    if t in (
        "restart the computer",
        "restart computer",
        "reboot",
        "மறுதொடக்கம் செய்",
        "ரீஸ்டார்ட் பண்ணு",
        "restart பண்ணு",
    ):
        return CommandIntent(kind="system", action="restart", raw_text=phrase)
    if t in (
        "cancel shutdown",
        "abort shutdown",
        "stop shutdown",
        "அணைப்பதை நிறுத்து",
        "cancel பண்ணு",
    ):
        return CommandIntent(kind="system", action="cancel_shutdown", raw_text=phrase)

    # 5. YouTube dedicated search (English + Tamil)
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

    m_yt_ta = re.match(r"^(.+?)\s+(?:பற்றி\s+)?யூடியூபில்\s+தேடு$", t)
    if m_yt_ta:
        return CommandIntent(
            kind="web_search", action="youtube", target=m_yt_ta.group(1).strip(), raw_text=phrase
        )

    # 6. Web search (English + Tamil)
    m_search_ta = re.match(r"^(.+?)\s+(?:பற்றி\s+)?தேடு$", t)
    if m_search_ta:
        return CommandIntent(
            kind="web_search", action="google", target=m_search_ta.group(1).strip(), raw_text=phrase
        )

    m_search = re.match(r"^(?:search for|google|search|தேடு)\s+(.+)$", t)
    if m_search:
        return CommandIntent(
            kind="web_search", action="google", target=m_search.group(1).strip(), raw_text=phrase
        )

    # 7. Window switching (English + Tamil)
    m_switch_ta = re.match(r"^(.+?)(?:-?க்கு\s+மாற்று|-?க்கு\s+போ|க்கு\s+மாற்று|க்கு\s+போ)$", t)
    if m_switch_ta:
        target = m_switch_ta.group(1).strip()
        return CommandIntent(kind="switch_app", action="switch", target=target, raw_text=phrase)

    m_switch = re.match(r"^(?:switch to|switch window to|focus|bring up)\s+(.+)$", t)
    if m_switch:
        target = m_switch.group(1).strip()
        return CommandIntent(kind="switch_app", action="switch", target=target, raw_text=phrase)

    # 8. Window / app closing (SOV & SVO, English + Tamil + Tanglish)
    # SVO (Prefix): "close notepad", "மூடு notepad", "க்ளோஸ் பண்ணு chrome"
    m_close = re.match(r"^(?:close|exit|quit|மூடு|க்ளோஸ்\s+பண்ணு|க்ளோஸ்)\s+(.+)$", t)
    if m_close:
        target = m_close.group(1).strip()
        return CommandIntent(kind="close_app", action="close", target=target, raw_text=phrase)

    # SOV (Postfix): "notepad மூடு", "chrome close பண்ணு", "notepad-ஐ மூடு", "notepad close pannu"
    m_close_sov = re.match(
        r"^(.+?)(?:-?ஐ|-?யை)?\s+(?:மூடு|க்ளோஸ்\s+பண்ணு|close\s+பண்ணு|மூடி\s+விடு|close\s+pannu)$",
        t,
    )
    if m_close_sov:
        target = m_close_sov.group(1).strip()
        return CommandIntent(kind="close_app", action="close", target=target, raw_text=phrase)

    # 9. Application launching (SOV & SVO, English + Tamil + Tanglish)
    # SVO (Prefix): "open notepad", "திற chrome", "ஓபன் பண்ணு calc"
    m_open = re.match(r"^(?:open|launch|start|run|திற|ஓபன்\s+பண்ணு|ஓபன்)\s+(.+)$", t)
    if m_open:
        target = m_open.group(1).strip()
        return CommandIntent(kind="open_app", action="open", target=target, raw_text=phrase)

    # SOV (Postfix): "chrome திற", "notepad open பண்ணு", "chrome open pannu", "calc திறந்து விடு"
    m_open_sov = re.match(
        r"^(.+?)(?:-?ஐ|-?யை)?\s+(?:திற|ஓபன்\s+பண்ணு|open\s+பண்ணு|திறந்து\s+விடு|open\s+pannu)$",
        t,
    )
    if m_open_sov:
        target = m_open_sov.group(1).strip()
        return CommandIntent(kind="open_app", action="open", target=target, raw_text=phrase)

    return None
