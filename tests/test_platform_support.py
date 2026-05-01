from pathlib import Path

import pytest

from platform_support import PlatformInfo, PlatformSupport


def test_kobold_binary_names_by_platform():
    assert PlatformSupport(PlatformInfo("win32", "AMD64")).kobold_cpp_binary_name() == "koboldcpp.exe"
    assert PlatformSupport(PlatformInfo("linux", "x86_64")).kobold_cpp_binary_name() == "koboldcpp-linux-x64"
    assert PlatformSupport(PlatformInfo("darwin", "arm64")).kobold_cpp_binary_name() == "koboldcpp-mac-arm64"


def test_macos_intel_has_clear_error():
    support = PlatformSupport(PlatformInfo("darwin", "x86_64"))

    with pytest.raises(RuntimeError, match="macOS Intel"):
        support.kobold_cpp_binary_name()


def test_venv_tool_path_uses_platform_directory(tmp_path):
    win = PlatformSupport(PlatformInfo("win32", "AMD64"))
    unix = PlatformSupport(PlatformInfo("linux", "x86_64"))

    assert win.venv_tool_path(tmp_path, "python").as_posix().endswith("Scripts/python.exe")
    assert unix.venv_tool_path(tmp_path, "python").as_posix().endswith("bin/python")


def test_kobold_cpp_path_joins_binary_name(tmp_path):
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))

    assert support.kobold_cpp_path(tmp_path) == tmp_path / "koboldcpp-linux-x64"
