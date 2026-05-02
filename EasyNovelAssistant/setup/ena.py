# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests==2.33.1",
#     "tkinterdnd2==0.4.3",
#     "scipy==1.15.3",
#     "watchdog==6.0.0",
# ]
# ///

import argparse
import runpy
import sys
from pathlib import Path


SETUP_DIR = Path(__file__).resolve().parent
SETUP_SCRIPT = SETUP_DIR / "setup_easy_novel_assistant.py"
RUN_SCRIPT = SETUP_DIR / "run_easy_novel_assistant.py"


def run_script(path):
    runpy.run_path(str(path), run_name="__main__")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ena")
    parser.add_argument("command", choices=["setup", "run"])
    args = parser.parse_args(argv)

    if args.command == "setup":
        run_script(SETUP_SCRIPT)
    elif args.command == "run":
        run_script(RUN_SCRIPT)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        sys.exit(1)
