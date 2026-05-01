from unittest.mock import Mock

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
            max_speech_queue=3,
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

    support.launch_command.assert_called_once_with(
        [str(style_dir / "venv" / "bin" / "python"), "server_fastapi.py", "--cpu"],
        cwd=str(style_dir),
    )


def test_launch_server_on_windows_runs_script_nonblocking_with_cpu_arg(tmp_path):
    style_dir = tmp_path / "Style-Bert-VITS2"
    support = PlatformSupport(PlatformInfo("win32", "AMD64"))
    support.run_script_file = Mock()
    style = StyleBertVits2(DummyContext(), platform_support=support, style_bert_vits2_dir=style_dir)

    style.launch_server()

    support.run_script_file.assert_called_once_with(str(AppPath.style_bert_vits2_run), args=["--cpu"])
