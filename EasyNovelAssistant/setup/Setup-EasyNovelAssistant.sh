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

. venv/bin/activate
python -m pip install --upgrade pip
pip install -r ./EasyNovelAssistant/setup/res/requirements.txt

mkdir -p KoboldCpp
cd KoboldCpp

OS_NAME="$(uname -s)"
MACHINE_NAME="$(uname -m)"
KOBOLD_BIN=""

case "$OS_NAME:$MACHINE_NAME" in
    Linux:*)
        KOBOLD_BIN="koboldcpp-linux-x64"
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
    curl -fLO "https://github.com/LostRuins/koboldcpp/releases/latest/download/$KOBOLD_BIN"
    chmod +x "$KOBOLD_BIN"
fi

if [ ! -e "Vecteus-v1-IQ4_XS.gguf" ]; then
    curl -fLO https://huggingface.co/mmnga/Vecteus-v1-gguf/resolve/main/Vecteus-v1_IQ4_XS.gguf || {
        rm -f Vecteus-v1_IQ4_XS.gguf
        curl -fLO https://huggingface.co/mmnga/Vecteus-v1-gguf/resolve/main/Vecteus-v1-IQ4_XS.gguf
    }
fi

cd -
