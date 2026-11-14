# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported from ROHITCRAFTSYT/WhispLocal/whisp/commands.py
"""Indexes Start Menu shortcuts and Microsoft Store apps for fuzzy voice launching."""

import difflib
import json
import logging
import os
import subprocess
import threading
import urllib.parse
import webbrowser

logger = logging.getLogger(__name__)

CREATE_NO_WINDOW = 0x08000000

# Built-in aliases mapping common spoken names to executable targets
ALIASES = {
    "notepad": "notepad",
    "notes": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "paint": "mspaint",
    "command prompt": "cmd",
    "cmd": "cmd",
    "terminal": "wt",
    "windows terminal": "wt",
    "file explorer": "explorer",
    "explorer": "explorer",
    "files": "explorer",
    "task manager": "taskmgr",
    "control panel": "control",
    "settings": "ms-settings:",
    "recycle bin": "shell:RecycleBinFolder",
    "camera": "microsoft.windows.camera:",
    # Tamil and Tanglish application aliases
    "குரோம்": "chrome",
    "நோட்பேடு": "notepad",
    "கால்குலேட்டர்": "calc",
    "கணக்கி": "calc",
    "டெர்மினல்": "wt",
    "கோப்புகள்": "explorer",
    "எக்ஸ்ப்ளோரர்": "explorer",
    "அமைப்புகள்": "ms-settings:",
    "கேமரா": "microsoft.windows.camera:",
}

# Popular web sites for web fallback
SITES = {
    "youtube": "https://www.youtube.com",
    "youtube music": "https://music.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "whatsapp": "https://web.whatsapp.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "claude": "https://claude.ai",
    "chatgpt": "https://chatgpt.com",
    "gemini": "https://gemini.google.com",
    "perplexity": "https://www.perplexity.ai",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "spotify": "https://open.spotify.com",
    "maps": "https://maps.google.com",
    "netflix": "https://www.netflix.com",
    "reddit": "https://www.reddit.com",
    "linkedin": "https://www.linkedin.com",
    "wikipedia": "https://www.wikipedia.org",
    "stack overflow": "https://stackoverflow.com",
    "drive": "https://drive.google.com",
    "docs": "https://docs.google.com",
    "sheets": "https://sheets.google.com",
    "calendar": "https://calendar.google.com",
    "translate": "https://translate.google.com",
    "outlook": "https://outlook.live.com",
    "teams": "https://teams.microsoft.com",
    "notion": "https://www.notion.so",
    # Tamil site names
    "யூடியூப்": "https://www.youtube.com",
    "கூகிள்": "https://www.google.com",
    "வாட்ஸ்அப்": "https://web.whatsapp.com",
}

_APP_STOP_WORDS = frozenset(("app", "the", "my", "please", "up", "program"))
_SKIP_SHORTCUT_TOKENS = ("uninstall", "help", "readme", "website", "documentation")


class AppIndex:
    """Manages an indexed cache of installed Windows applications and resolves spoken names."""

    def __init__(self, auto_build: bool = True):
        self.app_index: dict[str, str] = {}
        self.index_ready = threading.Event()
        if auto_build:
            threading.Thread(target=self.build_index, daemon=True, name="app-index").start()
        else:
            self.index_ready.set()

    def build_index(self) -> dict[str, str]:
        """Scan Start Menu folders and Store packages to build the app index."""
        index: dict[str, str] = {}

        # 1. Classic Start Menu shortcuts (.lnk / .url)
        roots = [
            os.path.join(
                os.environ.get("PROGRAMDATA", ""),
                r"Microsoft\Windows\Start Menu\Programs",
            ),
            os.path.join(
                os.environ.get("APPDATA", ""),
                r"Microsoft\Windows\Start Menu\Programs",
            ),
        ]
        for root in roots:
            if not os.path.isdir(root):
                continue
            for dirpath, _dirs, files in os.walk(root):
                for f in files:
                    if not f.lower().endswith((".lnk", ".url")):
                        continue
                    name = os.path.splitext(f)[0].lower()
                    if any(s in name for s in _SKIP_SHORTCUT_TOKENS):
                        continue
                    if name not in index:
                        index[name] = os.path.join(dirpath, f)

        # 2. Get-StartApps queries Microsoft Store / UWP apps (Spotify, WhatsApp, etc.)
        if os.name == "nt":
            try:
                out = subprocess.run(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-Command",
                        "Get-StartApps | ConvertTo-Json -Compress",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=CREATE_NO_WINDOW,
                )
                data = json.loads(out.stdout or "[]")
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = (item.get("Name") or "").strip().lower()
                    appid = (item.get("AppID") or "").strip()
                    if not name or not appid or any(s in name for s in _SKIP_SHORTCUT_TOKENS):
                        continue
                    if name not in index:
                        index[name] = appid if os.path.exists(appid) else f"appid:{appid}"
            except Exception as e:
                logger.debug(f"Store app indexing skipped: {e}")

        self.app_index = index
        self.index_ready.set()
        logger.info(f"Indexed {len(index)} application target(s)")
        return index

    def find_app(self, spoken_name: str) -> tuple[str, str] | None:
        """Resolve a spoken app name to a launchable target (executable path, URL, or AppID).

        Returns (target, resolved_name) or None.
        """
        name = spoken_name.strip().lower()
        if not name:
            return None

        # 1. Alias lookup
        if name in ALIASES:
            return ALIASES[name], name

        idx = self.app_index
        if not idx:
            return None

        # 2. Exact match in indexed shortcut names
        if name in idx:
            return idx[name], name

        tokens = {k: k.split() for k in idx}

        # 3. Whole word exact match ("code" -> "visual studio code")
        word_exact = [k for k, ts in tokens.items() if name in ts]
        if word_exact:
            best = min(word_exact, key=len)
            return idx[best], best

        # 4. Starts with prefix ("microsoft ed" -> "microsoft edge")
        starts = [k for k in idx if k.startswith(name)]
        if starts:
            best = min(starts, key=len)
            return idx[best], best

        # 5. Multi-word phrase search
        if " " in name:
            phrase = [k for k in idx if name in k]
            if phrase:
                best = min(phrase, key=len)
                return idx[best], best

            words = [w for w in name.split() if w not in _APP_STOP_WORDS]
            if words:
                allw = [
                    k
                    for k, ts in tokens.items()
                    if all(any(t.startswith(w) for t in ts) for w in words)
                ]
                if allw:
                    best = min(allw, key=len)
                    return idx[best], best
        elif len(name) >= 3:
            # 6. Word prefix ("calc" -> "calculator")
            word_prefix = [k for k, ts in tokens.items() if any(t.startswith(name) for t in ts)]
            if word_prefix:
                best = min(word_prefix, key=len)
                return idx[best], best

        # 7. Conservative fuzzy matching for typos / minor mishearings
        if len(name) >= 5:
            close = difflib.get_close_matches(name, list(idx), n=1, cutoff=0.8)
            if close:
                return idx[close[0]], close[0]

        return None

    def launch(self, target: str) -> bool:
        """Launch an application target, handling file shortcuts, URI schemes, and UWP AppIDs."""
        if not target:
            return False

        try:
            if target.startswith("appid:"):
                # UWP Store app
                subprocess.Popen(
                    ["explorer.exe", f"shell:AppsFolder\\{target[6:]}"],
                    creationflags=CREATE_NO_WINDOW,
                )
                return True
            if target.endswith(":") or target.startswith("ms-"):
                # URI scheme (e.g. ms-settings:)
                os.startfile(target)
                return True
            if os.path.exists(target):
                # Standard executable or .lnk file
                os.startfile(target)
                return True

            # Bare executable name (e.g. notepad, calc, wt)
            subprocess.Popen([target], creationflags=CREATE_NO_WINDOW)
            return True
        except Exception as e:
            logger.error(f"Failed to launch target '{target}': {e}")
            return False

    def open_web(self, query_or_site: str) -> tuple[bool, str]:
        """Open a web destination or fall back to web search."""
        target = query_or_site.strip().lower()
        if target in SITES:
            url = SITES[target]
            webbrowser.open(url)
            return True, f"Opening {target.title()} on the web"

        encoded = urllib.parse.quote_plus(query_or_site)
        webbrowser.open(f"https://www.google.com/search?q={encoded}")
        return True, f"Searching for '{query_or_site}' on the web"
