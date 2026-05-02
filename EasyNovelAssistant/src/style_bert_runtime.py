import re
from pathlib import Path


PYTORCH_CUDA_INDEX_URL = "https://download.pytorch.org/whl/cu118"
MACOS_ARM64_EXCLUDED_REQUIREMENT_NAMES = {"faster-whisper"}
RUNTIME_REQUIREMENTS_DIR = ".easy_novel_assistant"
RUNTIME_REQUIREMENTS_FILE = "requirements-runtime.txt"


def requirement_name(requirement_line):
    value = requirement_line.strip()
    if not value or value.startswith("#") or value.startswith("-"):
        return None
    value = value.split("#", 1)[0].strip()
    match = re.match(r"([A-Za-z0-9_.-]+)", value)
    if match is None:
        return None
    return match.group(1).lower().replace("_", "-")


def write_runtime_requirements(style_bert_dir, exclude_macos_arm64_problem_deps=False):
    style_bert_dir = Path(style_bert_dir)
    source = style_bert_dir / "requirements.txt"
    output = style_bert_dir / RUNTIME_REQUIREMENTS_DIR / RUNTIME_REQUIREMENTS_FILE

    if not source.exists():
        raise RuntimeError(f"Style-Bert-VITS2 requirements file not found: {source}")

    excluded_names = MACOS_ARM64_EXCLUDED_REQUIREMENT_NAMES if exclude_macos_arm64_problem_deps else set()
    filtered_lines = []
    for line in source.read_text(encoding="utf-8").splitlines():
        # faster-whisper pulls PyAV 10, which requires FFmpeg dev libraries on macOS arm64.
        if requirement_name(line) in excluded_names:
            continue
        filtered_lines.append(line)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(filtered_lines) + "\n", encoding="utf-8")
    return output


def style_bert_uv_dependencies(is_macos=False):
    args = [
        "--with",
        "GPUtil",
        "--with",
        "torch",
        "--with",
        "torchvision",
        "--with",
        "torchaudio",
    ]
    if not is_macos:
        args.extend(["--extra-index-url", PYTORCH_CUDA_INDEX_URL, "--index-strategy", "unsafe-best-match"])
    return args


def build_style_bert_uv_command(
    uv_command,
    python_executable,
    style_bert_dir,
    script_name,
    args=None,
    is_macos=False,
    is_macos_arm64=False,
):
    requirements = write_runtime_requirements(
        style_bert_dir,
        exclude_macos_arm64_problem_deps=is_macos_arm64,
    )
    command = [
        uv_command,
        "run",
        "--no-project",
        "--python",
        python_executable,
        "--with-requirements",
        str(requirements),
    ]
    command.extend(style_bert_uv_dependencies(is_macos=is_macos))
    command.append(script_name)
    command.extend(args or [])
    return command
