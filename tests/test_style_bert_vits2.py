from unittest.mock import Mock
import sys
import json

import style_bert_vits2
from platform_support import PlatformInfo, PlatformSupport
from style_bert_vits2 import StyleBertVits2


def make_style_dir(tmp_path):
    style_dir = tmp_path / "Style-Bert-VITS2"
    style_dir.mkdir()
    (style_dir / "requirements.txt").write_text(
        "torch<2.4\nfaster-whisper==0.10.1\nnumpy\n",
        encoding="utf-8",
    )
    return style_dir


class DummyContext(dict):
    def __init__(self):
        super().__init__(
            style_bert_vits2_host="localhost",
            style_bert_vits2_port=5000,
            style_bert_vits2_command_timeout=0.05,
            speech_enabled=True,
            max_speech_queue=3,
            speech_volume=80,
            speech_speed=1.2,
        )


def test_launch_server_uses_cuda_uv_command_without_cpu_arg(tmp_path, monkeypatch):
    monkeypatch.setenv("UV_CMD", "uv")
    style_dir = make_style_dir(tmp_path)
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))
    support.launch_command = Mock()
    style = StyleBertVits2(DummyContext(), platform_support=support, style_bert_vits2_dir=style_dir)

    style.launch_server()

    command = support.launch_command.call_args.args[0]
    assert command[:5] == ["uv", "run", "--no-project", "--python", sys.executable]
    assert command[-1:] == ["server_fastapi.py"]
    assert "--cpu" not in command
    assert "--with-requirements" in command
    requirements = style_dir / ".easy_novel_assistant" / "requirements-runtime.txt"
    assert str(requirements) in command
    assert "faster-whisper" not in requirements.read_text(encoding="utf-8")
    assert "https://download.pytorch.org/whl/cu118" in command
    support.launch_command.assert_called_once()
    assert support.launch_command.call_args.kwargs == {"cwd": str(style_dir)}


def test_launch_server_on_windows_uses_uv_cmd_not_batch(tmp_path, monkeypatch):
    monkeypatch.setenv("UV_CMD", "C:/Tools/uv.exe")
    style_dir = make_style_dir(tmp_path)
    support = PlatformSupport(PlatformInfo("win32", "AMD64"))
    support.launch_command = Mock()
    style = StyleBertVits2(DummyContext(), platform_support=support, style_bert_vits2_dir=style_dir)

    style.launch_server()

    command = support.launch_command.call_args.args[0]
    assert command[0] == "C:/Tools/uv.exe"
    assert command[-1] == "server_fastapi.py"
    assert "--cpu" not in command


def test_launch_server_on_macos_apple_silicon_skips_cuda_index(tmp_path, monkeypatch):
    monkeypatch.setenv("UV_CMD", "uv")
    style_dir = make_style_dir(tmp_path)
    support = PlatformSupport(PlatformInfo("darwin", "arm64"))
    support.launch_command = Mock()
    style = StyleBertVits2(DummyContext(), platform_support=support, style_bert_vits2_dir=style_dir)

    style.launch_server()

    command = support.launch_command.call_args.args[0]
    assert "torch" in command
    assert "--extra-index-url" not in command
    assert "https://download.pytorch.org/whl/cu118" not in command


def test_play_uses_ffplay_subprocess(monkeypatch):
    popen = Mock(return_value=Mock(wait=Mock()))
    monkeypatch.setattr(style_bert_vits2.subprocess, "Popen", popen)
    style = StyleBertVits2(DummyContext())

    style._play("/tmp/voice.wav")

    popen.assert_called_once_with(
        [
            "ffplay",
            "-volume",
            "80",
            "-af",
            "atempo=1.2",
            "-autoexit",
            "-nodisp",
            "-loglevel",
            "fatal",
            "/tmp/voice.wav",
        ],
        stdout=style_bert_vits2.subprocess.DEVNULL,
    )
    popen.return_value.wait.assert_called_once_with()


def test_play_prefers_bundled_ffplay_when_available(tmp_path, monkeypatch):
    ffplay = tmp_path / "setup" / "lib" / "ffmpeg" / "bin" / "ffplay.exe"
    ffplay.parent.mkdir(parents=True)
    ffplay.write_text("", encoding="utf-8")
    popen = Mock(return_value=Mock(wait=Mock()))
    monkeypatch.setattr(style_bert_vits2.Path, "ffplay", str(ffplay))
    monkeypatch.setattr(style_bert_vits2.subprocess, "Popen", popen)
    style = StyleBertVits2(DummyContext())

    style._play("/tmp/voice.wav")

    assert popen.call_args.args[0][0] == str(ffplay)


def test_generate_returns_false_without_queueing_when_speech_is_disabled():
    ctx = DummyContext()
    ctx["speech_enabled"] = False
    style = StyleBertVits2(ctx)
    style.gen_queue.push = Mock()

    result = style.generate("読み上げない")

    assert result is False
    style.gen_queue.push.assert_not_called()


def test_generate_logs_queue_skip_to_info_log(tmp_path, monkeypatch):
    info_log = tmp_path / "info.log"
    monkeypatch.setattr(style_bert_vits2.app_logger.Path, "info_log", str(info_log))
    style = StyleBertVits2(DummyContext())
    style.gen_queue.len = Mock(return_value=4)
    style.play_queue.len = Mock(return_value=0)
    style.gen_queue.push = Mock()

    result = style.generate("混雑時の行")

    assert result is False
    style.gen_queue.push.assert_not_called()
    logged = json.loads(info_log.read_text(encoding="utf-8-sig").splitlines()[0])
    assert logged["component"] == "speech"
    assert logged["event"] == "speech_queue_skipped"
    assert logged["gen_queue_len"] == 4
    assert logged["play_queue_len"] == 0
    style.gen_queue.len.assert_called_once_with()
    style.play_queue.len.assert_called_once_with()
