# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests==2.33.1",
#     "tkinterdnd2==0.4.3",
#     "scipy==1.15.3",
#     "watchdog==6.0.0",
# ]
# ///

import os
import runpy
import shutil
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_ENTRYPOINT = ROOT / "EasyNovelAssistant" / "src" / "easy_novel_assistant.py"
SAMPLE_BASE_URL = "https://yyy.wpx.jp/EasyNovelAssistant/sample"
ROOT_SAMPLES = ["special.json", "template.json", "sample.json", "nsfw.json", "speech.json"]
GOAL_SEEK_SAMPLES = [
    "00-企画.txt",
    "01-執筆.txt",
    "10-序章.txt",
    "20-第一章.txt",
    "30-第二章.txt",
    "40-第三章.txt",
    "50-終章.txt",
]


def download_file(url, output_path):
    output_path = Path(output_path)
    tmp_path = output_path.with_name(f"{output_path.name}.tmp")
    tmp_path.unlink(missing_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "EasyNovelAssistant-run"})
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(request) as response, tmp_path.open("wb") as output:
            shutil.copyfileobj(response, output)
        os.replace(tmp_path, output_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def build_sample_url(remote_dir, file_name):
    quoted_name = urllib.request.pathname2url(file_name)
    if remote_dir:
        return f"{SAMPLE_BASE_URL}/{remote_dir}/{quoted_name}"
    return f"{SAMPLE_BASE_URL}/{quoted_name}"


def ensure_sample(target_dir, remote_dir, file_name):
    output_path = ROOT / target_dir / file_name
    if output_path.exists():
        return output_path
    url = build_sample_url(remote_dir, file_name)
    download_file(url, output_path)
    return output_path


def ensure_samples():
    for file_name in ROOT_SAMPLES:
        ensure_sample(Path("sample"), "", file_name)
    for file_name in GOAL_SEEK_SAMPLES:
        ensure_sample(Path("sample") / "GoalSeek", "GoalSeek", file_name)


def launch_app():
    os.chdir(ROOT)
    src_path = str(APP_ENTRYPOINT.parent)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    runpy.run_path(str(APP_ENTRYPOINT), run_name="__main__")


def main():
    ensure_samples()
    launch_app()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        sys.exit(1)
