#!/bin/sh
set -eu

if ! command -v uv >/dev/null 2>&1; then
    echo "uv command was not found."
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

download_file() {
    url="$1"
    output="$2"
    tmp="$output.tmp"
    rm -f "$tmp"
    if curl -fL -o "$tmp" "$url"; then
        mv "$tmp" "$output"
    else
        rm -f "$tmp"
        return 1
    fi
}

uv run --with-requirements ./EasyNovelAssistant/setup/res/requirements.txt python -c "import requests, tkinter"

mkdir -p KoboldCpp
cd KoboldCpp

OS_NAME="$(uname -s)"
MACHINE_NAME="$(uname -m)"
KOBOLD_BIN=""

case "$OS_NAME:$MACHINE_NAME" in
    Linux:x86_64|Linux:amd64)
        KOBOLD_BIN="koboldcpp-linux-x64"
        ;;
    Linux:*)
        echo "Unsupported Linux architecture for default KoboldCpp binary: $MACHINE_NAME"
        echo "Install KoboldCpp manually into $(pwd) and configure a custom binary if needed."
        exit 1
        ;;
    Darwin:arm64|Darwin:aarch64)
        KOBOLD_BIN="koboldcpp-mac-arm64"
        ;;
    Darwin:*)
        echo "macOS Intel does not have a default KoboldCpp binary in this setup script."
        echo "Install KoboldCpp manually into $(pwd) and configure a custom binary if needed."
        exit 1
        ;;
    *)
        echo "Unsupported platform: $OS_NAME $MACHINE_NAME"
        exit 1
        ;;
esac

if [ ! -e "$KOBOLD_BIN" ]; then
    download_file "https://github.com/LostRuins/koboldcpp/releases/latest/download/$KOBOLD_BIN" "$KOBOLD_BIN"
    chmod +x "$KOBOLD_BIN"
fi

if [ ! -e "Vecteus-v1-IQ4_XS.gguf" ]; then
    download_file https://huggingface.co/mmnga/Vecteus-v1-gguf/resolve/main/Vecteus-v1-IQ4_XS.gguf Vecteus-v1-IQ4_XS.gguf || \
    download_file https://huggingface.co/mmnga/Vecteus-v1-gguf/resolve/main/Vecteus-v1_IQ4_XS.gguf Vecteus-v1-IQ4_XS.gguf
fi

cd -
