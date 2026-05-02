import pytest

from style_bert_runtime import build_style_bert_uv_command, write_runtime_requirements


def make_style_dir(tmp_path):
    style_dir = tmp_path / "Style-Bert-VITS2"
    style_dir.mkdir()
    (style_dir / "requirements.txt").write_text(
        "torch<2.4\nfaster-whisper==0.10.1\nnumpy\n",
        encoding="utf-8",
    )
    return style_dir


def test_runtime_requirements_keep_faster_whisper_by_default(tmp_path):
    style_dir = make_style_dir(tmp_path)

    requirements = write_runtime_requirements(style_dir)

    assert "faster-whisper==0.10.1" in requirements.read_text(encoding="utf-8")


def test_runtime_requirements_exclude_faster_whisper_for_macos_arm64(tmp_path):
    style_dir = make_style_dir(tmp_path)

    requirements = write_runtime_requirements(style_dir, exclude_macos_arm64_problem_deps=True)

    text = requirements.read_text(encoding="utf-8")
    assert "faster-whisper" not in text
    assert "torch<2.4" in text
    assert "numpy" in text


def test_runtime_requirements_missing_source_has_clear_error(tmp_path):
    style_dir = tmp_path / "Style-Bert-VITS2"
    style_dir.mkdir()

    with pytest.raises(RuntimeError, match="requirements file not found"):
        write_runtime_requirements(style_dir)


def test_build_command_filters_only_when_macos_arm64_flag_is_set(tmp_path):
    style_dir = make_style_dir(tmp_path)

    command = build_style_bert_uv_command(
        "uv",
        "python",
        style_dir,
        "initialize.py",
        is_macos=True,
        is_macos_arm64=True,
    )

    requirements = style_dir / ".easy_novel_assistant" / "requirements-runtime.txt"
    assert command[:5] == ["uv", "run", "--no-project", "--python", "python"]
    assert str(requirements) in command
    assert "faster-whisper" not in requirements.read_text(encoding="utf-8")
