"""Smoke tests: verify the kural package and all sub-packages import cleanly."""

import importlib


def test_kural_imports() -> None:
    kural = importlib.import_module("kural")
    assert kural.__version__ == "0.1.0"


def test_subpackages_import() -> None:
    for sub in ("kural.engine", "kural.control", "kural.config", "kural.ui"):
        importlib.import_module(sub)


def test_main_module_importable() -> None:
    importlib.import_module("kural.__main__")
