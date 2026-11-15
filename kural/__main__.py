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
        "--stats",
        action="store_true",
        help="Display productivity statistics (words, speaking WPM, time saved, streak).",
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

    # Launch live background runtime
    from kural.runtime import KuralRuntime

    runtime = KuralRuntime()
    runtime.run()


if __name__ == "__main__":
    main()
