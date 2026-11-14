"""Tests for pure Tamil and Tanglish voice command parsing in kural.control.parser."""

from kural.control.parser import CommandIntent, parse_command


class TestTamilAppCommands:
    def test_open_svo_pure_tamil(self):
        # SVO: திற <app>
        cmd = parse_command("திற chrome")
        assert cmd == CommandIntent(
            kind="open_app", action="open", target="chrome", raw_text="திற chrome"
        )

        cmd = parse_command("ஓபன் notepad")
        assert cmd == CommandIntent(
            kind="open_app", action="open", target="notepad", raw_text="ஓபன் notepad"
        )

    def test_open_sov_pure_tamil(self):
        # SOV: <app> திற
        cmd = parse_command("chrome திற")
        assert cmd == CommandIntent(
            kind="open_app", action="open", target="chrome", raw_text="chrome திற"
        )

    def test_open_tanglish(self):
        # Tanglish: <app> open பண்ணு / open pannu
        cmd = parse_command("chrome open பண்ணு")
        assert cmd == CommandIntent(
            kind="open_app", action="open", target="chrome", raw_text="chrome open பண்ணு"
        )

        cmd = parse_command("calculator open pannu")
        assert cmd == CommandIntent(
            kind="open_app", action="open", target="calculator", raw_text="calculator open pannu"
        )

        cmd = parse_command("notepad ஓபன் பண்ணு")
        assert cmd == CommandIntent(
            kind="open_app", action="open", target="notepad", raw_text="notepad ஓபன் பண்ணு"
        )

    def test_close_svo_pure_tamil(self):
        # SVO: மூடு <app>
        cmd = parse_command("மூடு notepad")
        assert cmd == CommandIntent(
            kind="close_app", action="close", target="notepad", raw_text="மூடு notepad"
        )

    def test_close_sov_pure_tamil(self):
        # SOV: <app> மூடு
        cmd = parse_command("notepad மூடு")
        assert cmd == CommandIntent(
            kind="close_app", action="close", target="notepad", raw_text="notepad மூடு"
        )

    def test_close_tanglish(self):
        # Tanglish: <app> close பண்ணு / close pannu
        cmd = parse_command("chrome close பண்ணு")
        assert cmd == CommandIntent(
            kind="close_app", action="close", target="chrome", raw_text="chrome close பண்ணு"
        )

        cmd = parse_command("vlc close pannu")
        assert cmd == CommandIntent(
            kind="close_app", action="close", target="vlc", raw_text="vlc close pannu"
        )

    def test_switch_window_tamil(self):
        # <app>-க்கு போ / <app>-க்கு மாற்று
        cmd = parse_command("chrome-க்கு போ")
        assert cmd == CommandIntent(
            kind="switch_app", action="switch", target="chrome", raw_text="chrome-க்கு போ"
        )

        cmd = parse_command("edge-க்கு மாற்று")
        assert cmd == CommandIntent(
            kind="switch_app", action="switch", target="edge", raw_text="edge-க்கு மாற்று"
        )


class TestTamilVolumeAndMedia:
    def test_volume_up_pure_and_tanglish(self):
        assert parse_command("சத்தம் ஏற்று").action == "up"
        assert parse_command("சத்தத்தை கூட்டு").action == "up"
        assert parse_command("வால்யூம் ஏத்து").action == "up"
        assert parse_command("sound ஏத்து").action == "up"
        assert parse_command("sound aethu").action == "up"

    def test_volume_down_pure_and_tanglish(self):
        assert parse_command("சத்தம் குறை").action == "down"
        assert parse_command("சத்தத்தை குறை").action == "down"
        assert parse_command("வால்யூம் குறை").action == "down"
        assert parse_command("sound குறை").action == "down"
        assert parse_command("sound kura").action == "down"

    def test_media_playback_tamil(self):
        assert parse_command("இசை இயக்கு").action == "play_pause"
        assert parse_command("பாடலை இயக்கு").action == "play_pause"
        assert parse_command("பாடல் நிறுத்து").action == "play_pause"
        assert parse_command("ப்ளே பண்ணு").action == "play_pause"
        assert parse_command("play pannu").action == "play_pause"

    def test_media_tracks_tamil(self):
        assert parse_command("அடுத்த பாடல்").action == "next"
        assert parse_command("அடுத்த பாட்டு").action == "next"
        assert parse_command("next பாட்டு").action == "next"
        assert parse_command("முந்தைய பாடல்").action == "prev"
        assert parse_command("முந்தைய பாட்டு").action == "prev"

    def test_mute_tamil(self):
        assert parse_command("ஒலியை நிறுத்து").action == "mute"
        assert parse_command("சத்தத்தை நிறுத்து").action == "mute"
        assert parse_command("மியூட் பண்ணு").action == "mute"


class TestTamilWindowStateAndSystem:
    def test_window_operations_tamil(self):
        assert parse_command("சிறிதாக்கு").action == "minimize"
        assert parse_command("மினிமைஸ் பண்ணு").action == "minimize"
        assert parse_command("பெரிதாக்கு").action == "maximize"
        assert parse_command("மேக்சிமைஸ் பண்ணு").action == "maximize"
        assert parse_command("டெஸ்க்டாப் காட்டு").action == "show_desktop"
        assert parse_command("desktop காட்டு").action == "show_desktop"

    def test_system_power_tamil(self):
        assert parse_command("கணினியை அணை").action == "shutdown"
        assert parse_command("கம்ப்யூட்டரை ஆஃப் பண்ணு").action == "shutdown"
        assert parse_command("மறுதொடக்கம் செய்").action == "restart"
        assert parse_command("ரீஸ்டார்ட் பண்ணு").action == "restart"
        assert parse_command("அணைப்பதை நிறுத்து").action == "cancel_shutdown"


class TestTamilSearch:
    def test_youtube_search_tamil(self):
        cmd = parse_command("ரஜினி பாடல்கள் யூடியூபில் தேடு")
        assert cmd.kind == "web_search"
        assert cmd.action == "youtube"
        assert cmd.target == "ரஜினி பாடல்கள்"

    def test_web_search_tamil(self):
        cmd = parse_command("சென்னை வானிலை பற்றி தேடு")
        assert cmd.kind == "web_search"
        assert cmd.action == "google"
        assert cmd.target == "சென்னை வானிலை"
