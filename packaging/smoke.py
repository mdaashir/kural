"""Fresh-install and extracted-bundle checks; no devices or model downloads."""

import argparse
import os
import subprocess
import tempfile
import time
from pathlib import Path

CHECK = """
from importlib.metadata import version as distribution_version
from importlib.resources import files
from kural.config import ConfigManager
from kural.control.app_rules import apply_formatting_style
assert distribution_version('cmd-kural') == '0.1.1'
assert files('kural.config').joinpath('config.defaults.yaml').is_file()
assert files('kural.config').joinpath('commands.defaults.yaml').is_file()
assert files('kural.config').joinpath('app_rules.defaults.yaml').is_file()
assert ConfigManager(use_user_settings=False, quiet=True).config
assert apply_formatting_style('hello world', 'formal') == 'Hello world.'
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--installer", type=Path)
    args = parser.parse_args()
    packages = args.packages.resolve() if args.packages else None
    bundle = args.bundle.resolve() if args.bundle else None
    with tempfile.TemporaryDirectory(prefix="kural-smoke-") as directory:
        root = Path(directory)
        env = dict(
            os.environ,
            UV_TOOL_DIR=str(root / "tools"),
            UV_TOOL_BIN_DIR=str(root / "bin"),
            APPDATA=str(root / "appdata"),
            USERPROFILE=str(root),
            HOME=str(root),
            HF_HUB_OFFLINE="1",
        )
        env.pop("PYTHONPATH", None)

        def run(*command: str) -> None:
            subprocess.run(command, cwd=root, env=env, check=True, timeout=300)

        if packages:
            for suffix in ("*.whl", "*.tar.gz"):
                artifacts = list(packages.glob(suffix))
                if len(artifacts) != 1:
                    raise RuntimeError(f"Expected one {suffix}: {artifacts}")
                run("uv", "tool", "install", "--python", "3.12", "--force", str(artifacts[0]))
                run(str(root / "bin" / "kural.exe"), "--version")
                run(str(root / "bin" / "kural.exe"), "--help")
                tool_name = artifacts[0].name.split("-", 1)[0].replace("_", "-")
                run(str(root / "tools" / tool_name / "Scripts" / "python.exe"), "-c", CHECK)
        if args.installer:
            destination = root / "installed"
            run(
                str(args.installer.resolve()),
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
                "/SP-",
                "/NOICONS",
                "/SmokeTest=1",
                f"/AppId=Kural-Smoke-{root.name}",
                f"/DIR={destination}",
            )
            try:
                run(str(destination / "kural.exe"), "--version")
                run(str(destination / "kural.exe"), "--packaging-smoke")
            finally:
                uninstaller = destination / "unins000.exe"
                if uninstaller.exists():
                    run(str(uninstaller), "/VERYSILENT", "/NORESTART", "/SUPPRESSMSGBOXES")
                    for _ in range(50):
                        if not (destination / "kural.exe").exists():
                            break
                        time.sleep(0.2)
            if (destination / "kural.exe").exists():
                raise RuntimeError("Uninstall left the application executable behind")
        if bundle:
            import shutil

            extracted = root / "bundle"
            shutil.unpack_archive(str(bundle), extracted)
            executable = str(extracted / "kural.exe")
            run(executable, "--version")
            run(executable, "--help")
            run(executable, "--packaging-smoke")


if __name__ == "__main__":
    main()
