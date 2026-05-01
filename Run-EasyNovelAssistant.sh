#!/bin/sh
set -eu

download_sample() {
    target_dir="$1"
    remote_dir="$2"
    file_name="$3"
    mkdir -p "$target_dir"
    if [ ! -e "$target_dir/$file_name" ]; then
        curl -fsSLo "$target_dir/$file_name" "https://yyy.wpx.jp/EasyNovelAssistant/sample/$remote_dir/$file_name"
    fi
}

download_root_sample() {
    file_name="$1"
    mkdir -p sample
    if [ ! -e "sample/$file_name" ]; then
        curl -fsSLo "sample/$file_name" "https://yyy.wpx.jp/EasyNovelAssistant/sample/$file_name"
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

. ./venv/bin/activate
python ./EasyNovelAssistant/src/easy_novel_assistant.py
