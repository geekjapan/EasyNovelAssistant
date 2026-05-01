from pathlib import Path

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


def test_style_bert_python_path_is_unix_bin_for_linux(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    style = StyleBertVits2(DummyContext(), platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")))

    path = style.get_python_executable()

    assert path.endswith("Style-Bert-VITS2/venv/bin/python")


def test_style_bert_python_path_is_windows_scripts_for_windows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    style = StyleBertVits2(DummyContext(), platform_support=PlatformSupport(PlatformInfo("win32", "AMD64")))

    path = style.get_python_executable()

    assert path.endswith("Style-Bert-VITS2/venv/Scripts/python.exe")
