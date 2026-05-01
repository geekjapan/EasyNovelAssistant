# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests==2.33.1",
#     "tkinterdnd2==0.4.3",
#     "scipy==1.15.3",
#     "watchdog==6.0.0",
# ]
# ///

import importlib
import os
import platform
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
KOBOLD_CPP_DIR = ROOT / "KoboldCpp"
VECTEUS_FILE_NAME = "Vecteus-v1-IQ4_XS.gguf"
VECTEUS_URLS = [
    "https://huggingface.co/mmnga/Vecteus-v1-gguf/resolve/main/Vecteus-v1-IQ4_XS.gguf",
    "https://huggingface.co/mmnga/Vecteus-v1-gguf/resolve/main/Vecteus-v1_IQ4_XS.gguf",
]


def select_kobold_binary(system=None, machine=None):
    system = system or platform.system()
    machine = (machine or platform.machine()).lower()
    if system == "Windows":
        return "koboldcpp.exe"
    if system == "Linux" and machine in ("x86_64", "amd64"):
        return "koboldcpp-linux-x64"
    if system == "Linux":
        raise RuntimeError(f"Unsupported Linux architecture for default KoboldCpp binary: {machine}")
    if system == "Darwin" and machine in ("arm64", "aarch64"):
        return "koboldcpp-mac-arm64"
    if system == "Darwin":
        raise RuntimeError("macOS Intel does not have a default KoboldCpp binary in this setup script.")
    raise RuntimeError(f"Unsupported platform: {system} {machine}")


def download_file(url, output_path):
    output_path = Path(output_path)
    tmp_path = output_path.with_name(f"{output_path.name}.tmp")
    tmp_path.unlink(missing_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "EasyNovelAssistant-setup"})
    try:
        with urllib.request.urlopen(request) as response, tmp_path.open("wb") as output:
            shutil.copyfileobj(response, output)
        os.replace(tmp_path, output_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def download_first_available(urls, output_path):
    last_error = None
    for url in urls:
        try:
            download_file(url, output_path)
            return
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code != 404:
                raise
    if last_error is not None:
        raise last_error


def ensure_app_dependencies():
    missing = []
    for module_name in ("requests", "tkinter"):
        try:
            importlib.import_module(module_name)
        except Exception:
            missing.append(module_name)
    if missing:
        modules = ", ".join(missing)
        raise RuntimeError(f"Required Python modules are unavailable: {modules}")


def ensure_kobold_cpp():
    KOBOLD_CPP_DIR.mkdir(exist_ok=True)
    binary_name = select_kobold_binary()
    binary_path = KOBOLD_CPP_DIR / binary_name
    if not binary_path.exists():
        url = f"https://github.com/LostRuins/koboldcpp/releases/latest/download/{binary_name}"
        print(f"Downloading {url}")
        download_file(url, binary_path)
    if platform.system() != "Windows":
        binary_path.chmod(binary_path.stat().st_mode | 0o755)
    return binary_path


def ensure_default_model():
    model_path = KOBOLD_CPP_DIR / VECTEUS_FILE_NAME
    if not model_path.exists():
        print(f"Downloading {VECTEUS_FILE_NAME}")
        download_first_available(VECTEUS_URLS, model_path)
    return model_path


def main():
    os.chdir(ROOT)
    ensure_app_dependencies()
    kobold_binary = ensure_kobold_cpp()
    model_path = ensure_default_model()
    print(f"KoboldCpp ready: {kobold_binary}")
    print(f"Default model ready: {model_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        sys.exit(1)
