"""Tests for kural.control.app_index — verifying shortcut indexing, aliases, and fuzzy matching."""

from unittest.mock import patch

from kural.control.app_index import SITES, AppIndex


class TestAppIndexMatching:
    def setup_method(self):
        # Don't auto-build the index from disk in tests
        self.indexer = AppIndex(auto_build=False)
        self.indexer.app_index = {
            "google chrome": "C:\\Program Files\\Chrome\\chrome.exe",
            "visual studio code": "C:\\Program Files\\VSCode\\Code.exe",
            "microsoft edge": "C:\\Program Files\\Edge\\edge.exe",
            "discord": "C:\\Users\\user\\AppData\\Local\\Discord\\app.exe",
            "vlc media player": "C:\\Program Files\\VLC\\vlc.exe",
            "spotify": "appid:SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify",
        }

    def test_alias_resolution(self):
        # Notepad is in built-in ALIASES
        result = self.indexer.find_app("notepad")
        assert result is not None
        assert result[0] == "notepad"

        calc = self.indexer.find_app("calculator")
        assert calc is not None
        assert calc[0] == "calc"

    def test_exact_indexed_name(self):
        result = self.indexer.find_app("google chrome")
        assert result is not None
        assert "chrome.exe" in result[0]

    def test_whole_word_match(self):
        # "code" matches "visual studio code"
        result = self.indexer.find_app("code")
        assert result is not None
        assert "Code.exe" in result[0]

    def test_prefix_match(self):
        # "microsoft ed" matches "microsoft edge"
        result = self.indexer.find_app("microsoft ed")
        assert result is not None
        assert "edge.exe" in result[0]

    def test_fuzzy_match(self):
        # "discrd" matches "discord" with high cutoff
        result = self.indexer.find_app("discrd")
        assert result is not None
        assert "Discord" in result[0]

    def test_unknown_app_returns_none(self):
        assert self.indexer.find_app("nonexistent_random_program_xyz") is None

    def test_empty_string_returns_none(self):
        assert self.indexer.find_app("") is None
        assert self.indexer.find_app("   ") is None


class TestWebFallback:
    def setup_method(self):
        self.indexer = AppIndex(auto_build=False)

    def test_known_site_opens_url(self):
        with patch("webbrowser.open") as mock_open:
            ok, msg = self.indexer.open_web("youtube")
            assert ok is True
            assert "Youtube" in msg
            mock_open.assert_called_once_with(SITES["youtube"])

    def test_unknown_query_opens_google_search(self):
        with patch("webbrowser.open") as mock_open:
            ok, msg = self.indexer.open_web("learn rust programming")
            assert ok is True
            assert "learn rust programming" in msg
            mock_open.assert_called_once()
            url = mock_open.call_args[0][0]
            assert "google.com/search?q=" in url


class TestLaunch:
    def setup_method(self):
        self.indexer = AppIndex(auto_build=False)

    def test_launch_uwp_appid(self):
        with patch("subprocess.Popen") as mock_popen:
            ok = self.indexer.launch("appid:SpotifyAB_zpdnekdrzrea0!App")
            assert ok is True
            mock_popen.assert_called_once()
            assert "shell:AppsFolder" in mock_popen.call_args[0][0][1]

    def test_launch_bare_executable(self):
        with patch("subprocess.Popen") as mock_popen:
            ok = self.indexer.launch("notepad")
            assert ok is True
            mock_popen.assert_called_once_with(["notepad"], creationflags=0x08000000)
