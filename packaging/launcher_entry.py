"""Choose the installed GUI or CLI entrypoint by executable filename."""

import sys
from pathlib import Path


def main() -> None:
    """Dispatch the PyInstaller executable to its intended entrypoint."""
    if Path(sys.executable).stem.casefold() == "kural":
        from kural.__main__ import windowed_main

        windowed_main()
    else:
        from kural.__main__ import console_main

        console_main()


if __name__ == "__main__":
    main()
