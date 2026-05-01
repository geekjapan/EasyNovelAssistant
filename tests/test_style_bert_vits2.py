from unittest.mock import Mock
import sys

import style_bert_vits2
from path import Path as AppPath
from platform_support import PlatformInfo, PlatformSupport
from style_bert_vits2 import StyleBertVits2


class DummyContext(dict):
    def __init__(self):
        super().__init__(
            style_bert_vits2_host="localhost",
            style_bert_vits2_port=5000,
            style_bert_vits2_gpu=False,
            style_bert_vits2_command_timeout=0.05,
            speech_enabled=True,
            max_speech_queue=3,
            speech_volume=80,
            speech_speed=1.2,
        )


def test_style_bert_python_path_is_unix_bin_for_linux(tmp_path):
    style_dir = tmp_path / "Style-Bert-VITS2"
    style = StyleBertVits2(
        DummyContext(),
        platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")),
        style_bert_vits2_dir=style_dir,
    )

    path = style.get_python_executable()

    assert path == str(style_dir / "venv" / "bin" / "python")


def test_style_bert_python_path_is_windows_scripts_for_windows(tmp_path):
    style_dir = tmp_path / "Style-Bert-VITS2"
    style = StyleBertVits2(
        DummyContext(),
        platform_support=PlatformSupport(PlatformInfo("win32", "AMD64")),
        style_bert_vits2_dir=style_dir,
    )

    path = style.get_python_executable()

    assert path == str(style_dir / "venv" / "Scripts" / "python.exe")


def test_launch_server_on_unix_uses_platform_launch_command_with_cpu_arg(tmp_path):
    style_dir = tmp_path / "Style-Bert-VITS2"
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))
    support.launch_command = Mock()
    style = StyleBertVits2(DummyContext(), platform_support=support, style_bert_vits2_dir=style_dir)

    style.launch_server()

    command = support.launch_command.call_args.args[0]
    assert command[:4] == ["uv", "run", "--python", sys.executable]
    assert command[-2:] == ["server_fastapi.py", "--cpu"]
    assert "--with-requirements" in command
    support.launch_command.assert_called_once()
    assert support.launch_command.call_args.kwargs == {"cwd": str(style_dir)}


def test_launch_server_on_windows_runs_script_nonblocking_with_cpu_arg(tmp_path):
    style_dir = tmp_path / "Style-Bert-VITS2"
    support = PlatformSupport(PlatformInfo("win32", "AMD64"))
    support.run_script_file = Mock()
    style = StyleBertVits2(DummyContext(), platform_support=support, style_bert_vits2_dir=style_dir)

    style.launch_server()

    support.run_script_file.assert_called_once_with(str(AppPath.style_bert_vits2_run), args=["--cpu"])


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


def test_generate_returns_false_without_queueing_when_speech_is_disabled():
    ctx = DummyContext()
    ctx["speech_enabled"] = False
    style = StyleBertVits2(ctx)
    style.gen_queue.push = Mock()

    result = style.generate("読み上げない")

    assert result is False
    style.gen_queue.push.assert_not_called()
