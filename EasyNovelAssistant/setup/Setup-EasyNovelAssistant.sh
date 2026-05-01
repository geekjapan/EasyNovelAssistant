#!/bin/sh
set -eu

if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
else
    PYTHON=python
fi

if [ ! -d "venv" ]; then
    "$PYTHON" -m venv venv
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

. venv/bin/activate
python -m pip install --upgrade pip
pip install -r ./EasyNovelAssistant/setup/res/requirements.txt

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
    download_file https://huggingface.co/mmnga/Vecteus-v1-gguf/resolve/main/Vecteus-v1_IQ4_XS.gguf Vecteus-v1_IQ4_XS.gguf || \
    download_file https://huggingface.co/mmnga/Vecteus-v1-gguf/resolve/main/Vecteus-v1-IQ4_XS.gguf Vecteus-v1_IQ4_XS.gguf
fi

cd -
