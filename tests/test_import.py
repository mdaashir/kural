"""Smoke tests: verify the kural package and all sub-packages import cleanly."""

import importlib


def test_kural_imports() -> None:
    from importlib.metadata import PackageNotFoundError, version

    kural = importlib.import_module("kural")
    try:
        expected = version("cmd-kural")
    except PackageNotFoundError:
        expected = "0+unknown"
    assert kural.__version__ == expected


def test_subpackages_import() -> None:
    for sub in ("kural.engine", "kural.control", "kural.config", "kural.ui"):
        importlib.import_module(sub)


def test_main_module_importable() -> None:
    importlib.import_module("kural.__main__")
