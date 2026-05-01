#!/bin/sh
set -eu

download_file() {
    url="$1"
    output="$2"
    tmp="$output.tmp"
    rm -f "$tmp"
    if curl -fsSL -o "$tmp" "$url"; then
        mv "$tmp" "$output"
    else
        rm -f "$tmp"
        return 1
    fi
}

download_sample() {
    target_dir="$1"
    remote_dir="$2"
    file_name="$3"
    mkdir -p "$target_dir"
    if [ ! -e "$target_dir/$file_name" ]; then
        download_file "https://yyy.wpx.jp/EasyNovelAssistant/sample/$remote_dir/$file_name" "$target_dir/$file_name"
    fi
}

download_root_sample() {
    file_name="$1"
    mkdir -p sample
    if [ ! -e "sample/$file_name" ]; then
        download_file "https://yyy.wpx.jp/EasyNovelAssistant/sample/$file_name" "sample/$file_name"
    fi
}

download_root_sample special.json
download_root_sample template.json
download_root_sample sample.json
download_root_sample nsfw.json
download_root_sample speech.json

download_sample sample/GoalSeek GoalSeek "00-企画.txt"
download_sample sample/GoalSeek GoalSeek "01-執筆.txt"
download_sample sample/GoalSeek GoalSeek "10-序章.txt"
download_sample sample/GoalSeek GoalSeek "20-第一章.txt"
download_sample sample/GoalSeek GoalSeek "30-第二章.txt"
download_sample sample/GoalSeek GoalSeek "40-第三章.txt"
download_sample sample/GoalSeek GoalSeek "50-終章.txt"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv command was not found."
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

uv run --with-requirements ./EasyNovelAssistant/setup/res/requirements.txt python ./EasyNovelAssistant/src/easy_novel_assistant.py
