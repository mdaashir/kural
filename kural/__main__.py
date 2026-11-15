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
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    args = parser.parse_args()

    if args.doctor:
        from kural.doctor import run_doctor

        sys.exit(run_doctor())

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

    # Launch live background runtime
    from kural.runtime import KuralRuntime

    runtime = KuralRuntime()
    runtime.run()


if __name__ == "__main__":
    main()
