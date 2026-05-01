#!/bin/sh
set -eu

if ! command -v uv >/dev/null 2>&1; then
    echo "uv command was not found."
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"
uv run ./EasyNovelAssistant/setup/run_easy_novel_assistant.py
