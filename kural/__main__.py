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
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    args = parser.parse_args()

    if args.doctor:
        from kural.doctor import run_doctor

        sys.exit(run_doctor())

    print(f"Kural {get_version()} — use '--doctor' to run diagnostics.")


if __name__ == "__main__":
    main()
