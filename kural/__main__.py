"""Entry point for `python -m kural`."""

import argparse
import sys

from kural.engine.utils import get_version


def main() -> None:
    """Start the Kural application or run CLI commands."""
    parser = argparse.ArgumentParser(
        prog="kural",
        description="Local-first voice typing and voice control for Windows. English and Tamil.",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Run environment, hardware, GPU, audio, and configuration diagnostics.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run live end-to-end operational self-test diagnostics (mic, model, inference, clipboard).",
    )
    parser.add_argument(
        "--bundle-logs",
        nargs="?",
        const="",
        metavar="ZIP_PATH",
        help="Create a redacted diagnostic zip archive for bug reports.",
    )
    parser.add_argument(
        "--transcribe",
        type=str,
        metavar="AUDIO_FILE",
        help="Transcribe an audio file offline (WAV, MP3, M4A, FLAC) and print or save the transcript.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "srt", "json"],
        default="text",
        help="Output format for file transcription (default: text).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        metavar="OUTPUT_FILE",
        help="Destination path to write transcript instead of printing to stdout.",
    )
    parser.add_argument(
        "--settings",
        action="store_true",
        help="Open the graphical settings configuration window.",
    )
    parser.add_argument(
        "--dict-list",
        action="store_true",
        help="List all custom dictionary hotwords.",
    )
    parser.add_argument(
        "--dict-add",
        type=str,
        metavar="WORD",
        help="Add a custom word or Tamil proper noun to dictionary hotwords.",
    )
    parser.add_argument(
        "--dict-remove",
        type=str,
        metavar="WORD",
        help="Remove a custom word from dictionary hotwords.",
    )
    parser.add_argument(
        "--history",
        nargs="?",
        const="",
        metavar="QUERY",
        help="Search dictation history (BM25 ranking), or show latest if no query given.",
    )
    parser.add_argument(
        "--history-gui",
        action="store_true",
        help="Open the graphical history browser window.",
    )
    parser.add_argument(
        "--cheat-sheet",
        action="store_true",
        help="Open the hotkeys and voice commands cheat sheet reference card.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display productivity statistics (words, speaking WPM, time saved, streak).",
    )
    parser.add_argument(
        "--autostart-status",
        action="store_true",
        help="Check whether Kural is configured to launch on Windows startup.",
    )
    parser.add_argument(
        "--enable-autostart",
        action="store_true",
        help="Configure Kural to launch automatically on Windows login (windowless).",
    )
    parser.add_argument(
        "--disable-autostart",
        action="store_true",
        help="Remove Kural from Windows startup.",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run local OpenAI-compatible Whisper API server.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address to bind local server to (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7777,
        help="Port to bind local server to (default: 7777).",
    )
    parser.add_argument(
        "--config-check",
        action="store_true",
        help="Audit configuration integrity and check for invalid or out-of-bounds keys.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    parser.add_argument("--packaging-smoke", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.packaging_smoke:
        from importlib import import_module
        from importlib.resources import files

        from kural.config import ConfigManager

        for module in (
            "faster_whisper",
            "ctranslate2",
            "sounddevice",
            "soxr",
            "global_hotkeys",
            "pyperclip",
            "pystray",
            "PIL.Image",
            "tkinter",
            "kural.runtime",
        ):
            import_module(module)
        for asset in ("config.defaults.yaml", "commands.defaults.yaml", "app_rules.defaults.yaml"):
            assert files("kural.config").joinpath(asset).is_file(), asset
        assert ConfigManager(use_user_settings=False, quiet=True).config
        print("Offline desktop packaging smoke passed")
        return

    if args.doctor:
        from kural.doctor import run_doctor

        sys.exit(run_doctor())

    if args.selftest:
        from kural.selftest import run_selftest

        sys.exit(run_selftest())

    if args.bundle_logs is not None:
        from kural.engine.bundle_logs import bundle_logs

        out = args.bundle_logs if args.bundle_logs.strip() else None
        sys.exit(bundle_logs(out))

    if args.transcribe:
        from kural.engine.file_transcriber import transcribe_file

        try:
            transcribe_file(
                file_path=args.transcribe,
                output_format=args.format,
                output_path=args.output,
            )
            return
        except Exception as e:
            print(f"Error transcribing file: {e}", file=sys.stderr)
            sys.exit(1)

    if args.config_check:
        from kural.config import ConfigManager
        from kural.config.configcheck import validate_config

        cm = ConfigManager(quiet=True)
        _, issues = validate_config(cm.config)
        print("Kural Configuration Audit:")
        if not issues:
            print("  ✓ All configuration keys and values are valid.")
        else:
            print(f"  ⚠️  Found {len(issues)} anomaly/anomalies:")
            for issue in issues:
                print(f"    • {issue}")
        return

    if args.settings:
        from kural.ui.settings_window import open_settings_window

        open_settings_window()
        return

    if args.history_gui:
        from kural.ui.history_window import open_history_window

        open_history_window()
        return

    if args.cheat_sheet:
        from kural.ui.cheat_sheet import open_cheat_sheet

        open_cheat_sheet()
        return

    if args.dict_list:
        from kural.engine.dictionary import list_hotwords

        words = list_hotwords()
        print(f"Kural Custom Dictionary ({len(words)} words):")
        for w in words:
            print(f"  • {w}")
        return

    if args.dict_add:
        from kural.engine.dictionary import add_hotword

        if add_hotword(args.dict_add):
            print(f"✓ Added '{args.dict_add}' to dictionary hotwords.")
        else:
            print(f"✗ Word '{args.dict_add}' is already present or empty.")
        return

    if args.dict_remove:
        from kural.engine.dictionary import remove_hotword

        if remove_hotword(args.dict_remove):
            print(f"✓ Removed '{args.dict_remove}' from dictionary hotwords.")
        else:
            print(f"✗ Word '{args.dict_remove}' not found in dictionary.")
        return

    if args.history is not None:
        from kural.engine.history import search_history

        results = search_history(query=args.history, limit=20)
        label = f"Query: '{args.history}'" if args.history else "Recent Entries"
        print(f"Kural Dictation History ({label}):")
        if not results:
            print("  (No matching history entries found)")
        for r in results:
            ts_str = r.get("ts", "")[:19].replace("T", " ")
            task_tag = f"[{r.get('task')}]"
            print(f"  {ts_str} {task_tag:<13} {r.get('text')}")
        return

    if args.stats:
        from kural.engine.history import compute_stats

        s = compute_stats()
        print("Kural Productivity Statistics:")
        print(f"  • Total Dictations:  {s['dictations']}")
        print(f"  • Total Commands:    {s['commands']}")
        print(f"  • Words Dictated:    {s['total_words']:,}")
        print(f"  • Speaking Speed:    {s['wpm']} WPM")
        print(f"  • Time Saved:        ~{s['minutes_saved']} minutes (vs typing)")
        print(f"  • Active Streak:     {s['streak_days']} day(s)")
        if s["top_apps"]:
            app_str = ", ".join(f"{a} ({c})" for a, c in s["top_apps"])
            print(f"  • Top Apps:          {app_str}")
        return

    if args.autostart_status:
        from kural.control.autostart import get_stored_autostart_command, is_autostart_enabled

        if is_autostart_enabled():
            print(f"✓ Kural autostart is ENABLED.\n  Command: {get_stored_autostart_command()}")
        else:
            print("✗ Kural autostart is DISABLED (will not launch on login).")
        return

    if args.enable_autostart:
        from kural.control.autostart import enable_autostart

        if enable_autostart():
            print("✓ Enabled Kural autostart at Windows login (windowless background mode).")
        else:
            print("✗ Failed to enable autostart (check platform and user permissions).")
        return

    if args.disable_autostart:
        from kural.control.autostart import disable_autostart

        if disable_autostart():
            print("✓ Disabled Kural autostart (removed from Windows startup).")
        else:
            print("✗ Failed to disable autostart.")
        return

    if args.serve:
        from kural.engine.server import run_server

        sys.exit(run_server(host=args.host, port=args.port))

    # Configure logging before starting the runtime
    from kural.config import ConfigManager
    from kural.engine.instance_manager import (
        acquire_single_instance_lock,
        release_single_instance_lock,
    )
    from kural.engine.log_setup import setup_logging

    cfg = ConfigManager(quiet=True)
    setup_logging(cfg.config)

    # Acquire single-instance lock before launching background runtime
    lock_ok, lock_handle = acquire_single_instance_lock()
    if not lock_ok:
        sys.exit(1)

    try:
        # Launch live background runtime
        from kural.runtime import KuralRuntime

        runtime = KuralRuntime(config_manager=cfg)
        runtime.run()
    finally:
        release_single_instance_lock(lock_handle)


if __name__ == "__main__":
    main()
