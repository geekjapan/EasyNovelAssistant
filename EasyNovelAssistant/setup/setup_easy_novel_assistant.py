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
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "EasyNovelAssistant" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from style_bert_runtime import (  # noqa: E402
    PYTORCH_CUDA_INDEX_URL,
    build_style_bert_uv_command,
    style_bert_uv_dependencies as build_style_bert_uv_dependencies,
)

KOBOLD_CPP_DIR = ROOT / "KoboldCpp"
STYLE_BERT_VITS2_DIR = ROOT / "Style-Bert-VITS2"
STYLE_BERT_VITS2_CONFIG = STYLE_BERT_VITS2_DIR / "config.yml"
STYLE_BERT_VITS2_CONFIG_SOURCE = ROOT / "EasyNovelAssistant" / "setup" / "res" / "config.yml"
STYLE_BERT_SETUP_STATE = STYLE_BERT_VITS2_DIR / ".easy_novel_assistant" / "setup-state.json"
SETUP_LIB_DIR = ROOT / "EasyNovelAssistant" / "setup" / "lib"
FFMPEG_DIR = SETUP_LIB_DIR / "ffmpeg-master-latest-win64-gpl"
FFMPEG_ZIP = SETUP_LIB_DIR / "ffmpeg.zip"
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
VECTEUS_FILE_NAME = "Vecteus-v1-IQ4_XS.gguf"
VECTEUS_URLS = [
    "https://huggingface.co/mmnga/Vecteus-v1-gguf/resolve/main/Vecteus-v1-IQ4_XS.gguf",
    "https://huggingface.co/mmnga/Vecteus-v1-gguf/resolve/main/Vecteus-v1_IQ4_XS.gguf",
]
STYLE_BERT_MODELS = [
    ("RinneAi/Rinne_Style-Bert-VITS2", "model_assets/Rinne", "Rinne", "Rinne"),
]
STYLE_BERT_INITIALIZE_MARKERS = [
    "configs/paths.yml",
    "slm/wavlm-base-plus/pytorch_model.bin",
    "pretrained/G_0.safetensors",
    "pretrained/D_0.safetensors",
    "pretrained/DUR_0.safetensors",
    "pretrained_jp_extra/G_0.safetensors",
    "pretrained_jp_extra/D_0.safetensors",
    "pretrained_jp_extra/WD_0.safetensors",
    "model_assets/jvnv-F1-jp/config.json",
    "model_assets/jvnv-F1-jp/jvnv-F1-jp_e160_s14000.safetensors",
    "model_assets/jvnv-F1-jp/style_vectors.npy",
    "model_assets/jvnv-F2-jp/config.json",
    "model_assets/jvnv-F2-jp/jvnv-F2_e166_s20000.safetensors",
    "model_assets/jvnv-F2-jp/style_vectors.npy",
    "model_assets/jvnv-M1-jp/config.json",
    "model_assets/jvnv-M1-jp/jvnv-M1-jp_e158_s14000.safetensors",
    "model_assets/jvnv-M1-jp/style_vectors.npy",
    "model_assets/jvnv-M2-jp/config.json",
    "model_assets/jvnv-M2-jp/jvnv-M2-jp_e159_s17000.safetensors",
    "model_assets/jvnv-M2-jp/style_vectors.npy",
    "model_assets/koharune-ami/config.json",
    "model_assets/koharune-ami/koharune-ami.safetensors",
    "model_assets/koharune-ami/style_vectors.npy",
    "model_assets/amitaro/config.json",
    "model_assets/amitaro/amitaro.safetensors",
    "model_assets/amitaro/style_vectors.npy",
]


def resolve_uv_command():
    return os.environ.get("UV_CMD") or shutil.which("uv") or "uv"


def should_update_style_bert_repo():
    return os.environ.get("ENA_UPDATE_STYLE_BERT", "").lower() in ("1", "true", "yes")


def style_bert_uv_dependencies(system=None):
    system = system or platform.system()
    return build_style_bert_uv_dependencies(is_macos=system == "Darwin")


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


def read_json_file(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return default


def write_json_file(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    try:
        tmp_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        tmp_path.unlink(missing_ok=True)


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


def style_bert_uv_command(script_name, *args):
    is_macos_arm64 = platform.system() == "Darwin" and platform.machine().lower() in ("arm64", "aarch64")
    return build_style_bert_uv_command(
        resolve_uv_command(),
        sys.executable,
        STYLE_BERT_VITS2_DIR,
        script_name,
        args=args,
        is_macos=platform.system() == "Darwin",
        is_macos_arm64=is_macos_arm64,
    )


def ensure_style_bert_repo():
    if STYLE_BERT_VITS2_DIR.exists():
        if not (STYLE_BERT_VITS2_DIR / ".git").exists():
            raise RuntimeError(f"Style-Bert-VITS2 exists but is not a git repository: {STYLE_BERT_VITS2_DIR}")
        if should_update_style_bert_repo():
            subprocess.run(["git", "-C", str(STYLE_BERT_VITS2_DIR), "pull", "--ff-only"], check=True)
        else:
            print(f"Using existing Style-Bert-VITS2: {STYLE_BERT_VITS2_DIR}")
    else:
        subprocess.run(
            ["git", "clone", "https://github.com/litagin02/Style-Bert-VITS2", str(STYLE_BERT_VITS2_DIR)],
            check=True,
        )


def style_bert_repo_head():
    result = subprocess.run(
        ["git", "-C", str(STYLE_BERT_VITS2_DIR), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def style_bert_marker_paths():
    markers = list(STYLE_BERT_INITIALIZE_MARKERS)
    bert_models = read_json_file(STYLE_BERT_VITS2_DIR / "bert" / "bert_models.json", default={})
    for model_name, model in bert_models.items():
        for file_name in model.get("files", []):
            markers.append(str(Path("bert") / model_name / file_name))
    return [STYLE_BERT_VITS2_DIR / marker for marker in markers]


def style_bert_initialize_is_current():
    state = read_json_file(STYLE_BERT_SETUP_STATE, default={}) or {}
    if state.get("style_bert_head") != style_bert_repo_head():
        return False
    return all(path.exists() for path in style_bert_marker_paths())


def record_style_bert_initialize_complete():
    write_json_file(
        STYLE_BERT_SETUP_STATE,
        {
            "style_bert_head": style_bert_repo_head(),
            "initialize_script": "initialize.py",
        },
    )


def ensure_windows_ffmpeg_bundle():
    if platform.system() != "Windows" or FFMPEG_DIR.exists():
        return
    SETUP_LIB_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {FFMPEG_URL}")
    download_file(FFMPEG_URL, FFMPEG_ZIP)
    with zipfile.ZipFile(FFMPEG_ZIP) as archive:
        safe_extract_zip(archive, SETUP_LIB_DIR)
    FFMPEG_ZIP.unlink(missing_ok=True)


def safe_extract_zip(archive, destination):
    destination = Path(destination).resolve()
    for member in archive.infolist():
        target = (destination / member.filename).resolve()
        if target != destination and destination not in target.parents:
            raise RuntimeError(f"Unsafe archive member path: {member.filename}")
    archive.extractall(destination)


def ensure_style_bert_model(repo_id, model_dir, model_name, model_safetensors):
    target_dir = STYLE_BERT_VITS2_DIR / "model_assets" / model_name
    target_dir.mkdir(parents=True, exist_ok=True)
    files = [
        (f"{model_safetensors}.safetensors", f"{model_name}.safetensors"),
        ("config.json", "config.json"),
        ("style_vectors.npy", "style_vectors.npy"),
    ]
    for source_name, target_name in files:
        target_path = target_dir / target_name
        if not target_path.exists():
            url = f"https://huggingface.co/{repo_id}/resolve/main/{model_dir}/{source_name}"
            print(f"Downloading {url}")
            download_file(url, target_path)


def ensure_style_bert_assets():
    ensure_windows_ffmpeg_bundle()
    if style_bert_initialize_is_current():
        print("Style-Bert-VITS2 initialize already complete")
    else:
        subprocess.run(style_bert_uv_command("initialize.py"), cwd=str(STYLE_BERT_VITS2_DIR), check=True)
        record_style_bert_initialize_complete()
    for model in STYLE_BERT_MODELS:
        ensure_style_bert_model(*model)
    if not STYLE_BERT_VITS2_CONFIG.exists():
        shutil.copy2(STYLE_BERT_VITS2_CONFIG_SOURCE, STYLE_BERT_VITS2_CONFIG)


def ensure_speech_engine():
    print("Checking Style-Bert-VITS2 speech engine")
    ensure_style_bert_repo()
    ensure_style_bert_assets()
    print(f"Style-Bert-VITS2 ready: {STYLE_BERT_VITS2_DIR}")


def main():
    os.chdir(ROOT)
    ensure_app_dependencies()
    kobold_binary = ensure_kobold_cpp()
    model_path = ensure_default_model()
    ensure_speech_engine()
    print(f"KoboldCpp ready: {kobold_binary}")
    print(f"Default model ready: {model_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        sys.exit(1)
