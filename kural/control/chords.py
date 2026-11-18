# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported and adapted from ROHITCRAFTSYT/WhispLocal/whisp/chords.py
"""Multi-key hold-to-talk chords such as "ctrl+windows" or "ctrl+alt".

Standard keyboard listeners typically only watch single keys. A chord needs
every key down simultaneously, and recording must stop the moment any single
key is released. ChordMatcher tracks pressed keys from raw event streams and
reports transitions:

    feed("down", "ctrl")     -> None
    feed("down", "windows")  -> "press"    (all keys now held)
    feed("up", "ctrl")       -> "release"  (chord broken)

Generic modifier names match either side: "ctrl" matches left or right Ctrl,
"windows" matches either Windows key. "right ctrl" matches only the right one.
"""

ALIASES = {
    "control": "ctrl",
    "win": "windows",
    "cmd": "windows",
    "super": "windows",
    "option": "alt",
    "altgr": "right alt",
    "alt gr": "right alt",
    "return": "enter",
    "esc": "escape",
}

_SIDED = {"ctrl", "alt", "shift", "windows"}


def normalize(name: str) -> str:
    """Normalize key name alias into canonical form."""
    name = (name or "").strip().lower()
    return ALIASES.get(name, name)


def generic(name: str) -> str:
    """Strip 'left ' or 'right ' prefix from sided modifier: 'left windows' -> 'windows'."""
    name = normalize(name)
    for side in ("left ", "right "):
        if name.startswith(side) and name[len(side) :] in _SIDED:
            return name[len(side) :]
    return name


def is_chord(spec: str) -> bool:
    """Return True if spec defines a multi-key combination (contains '+')."""
    return "+" in (spec or "").strip("+")


def parse_chord(spec: str) -> list[str]:
    """Parse a chord spec string like 'ctrl+windows' into canonical key tokens."""
    return [normalize(p) for p in (spec or "").split("+") if p.strip()]


class ChordMatcher:
    """Tracks state of raw keyboard events to detect chord press and release transitions."""

    def __init__(self, spec: str):
        self.keys = parse_chord(spec)
        self.down: set[str] = set()
        self.active: bool = False

    def _held(self, want: str) -> bool:
        if want in _SIDED:  # generic modifier: either left or right counts
            return any(generic(k) == want for k in self.down)
        return want in self.down

    def feed(self, event_type: str, name: str) -> str | None:
        """Feed one keyboard event. Returns 'press', 'release', or None."""
        name = normalize(name)
        if event_type == "down":
            self.down.add(name)
        elif name in self.down:
            self.down.discard(name)
        else:
            # Some Windows keyboard drivers report a sided name on key down and the generic
            # one on key up (or vice-versa): drop the matching key.
            self.down = {k for k in self.down if generic(k) != generic(name)}

        complete = bool(self.keys) and all(self._held(k) for k in self.keys)
        if complete and not self.active:
            self.active = True
            return "press"
        if not complete and self.active:
            self.active = False
            return "release"
        return None
