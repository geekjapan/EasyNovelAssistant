from unittest.mock import Mock

import pytest

import platform_support
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


def test_resolve_tool_prefers_venv_tool_when_present(tmp_path, monkeypatch):
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))
    tool_path = tmp_path / "bin" / "python"
    tool_path.parent.mkdir()
    tool_path.touch()
    which = Mock(return_value="/usr/bin/python")
    monkeypatch.setattr(platform_support.shutil, "which", which)

    assert support.resolve_tool(tmp_path, "python") == str(tool_path)
    which.assert_not_called()


def test_resolve_tool_falls_back_to_path_lookup(tmp_path, monkeypatch):
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))
    monkeypatch.setattr(platform_support.shutil, "which", Mock(return_value="/usr/bin/python"))

    assert support.resolve_tool(tmp_path, "python") == "/usr/bin/python"


def test_resolve_tool_returns_venv_path_when_tool_missing(tmp_path, monkeypatch):
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))
    monkeypatch.setattr(platform_support.shutil, "which", Mock(return_value=None))

    assert support.resolve_tool(tmp_path, "python") == str(tmp_path / "bin" / "python")


def test_windows_launch_command_uses_argument_list_without_shell(monkeypatch, tmp_path):
    support = PlatformSupport(PlatformInfo("win32", "AMD64"))
    popen = Mock(return_value="process")
    monkeypatch.setattr(platform_support.subprocess, "CREATE_NEW_CONSOLE", 16, raising=False)
    monkeypatch.setattr(platform_support.subprocess, "Popen", popen)

    result = support.launch_command(["C:/Tools/run.exe", "name & value"], cwd=tmp_path)

    assert result == "process"
    popen.assert_called_once_with(
        ["C:/Tools/run.exe", "name & value"],
        cwd=tmp_path,
        creationflags=16,
    )


def test_windows_launch_command_rejects_batch_scripts(monkeypatch):
    support = PlatformSupport(PlatformInfo("win32", "AMD64"))
    popen = Mock()
    monkeypatch.setattr(platform_support.subprocess, "Popen", popen)

    with pytest.raises(ValueError, match="batch scripts"):
        support.launch_command(["C:/Tools/run.bat"])

    popen.assert_not_called()


def test_unix_launch_command_uses_direct_argument_list(monkeypatch, tmp_path):
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))
    popen = Mock(return_value="process")
    monkeypatch.setattr(platform_support.subprocess, "Popen", popen)

    result = support.launch_command(["/opt/tool", "--name", "value"], cwd=tmp_path)

    assert result == "process"
    popen.assert_called_once_with(["/opt/tool", "--name", "value"], cwd=tmp_path)


def test_windows_run_script_file_returns_popen(monkeypatch, tmp_path):
    support = PlatformSupport(PlatformInfo("win32", "AMD64"))
    script = tmp_path / "setup.bat"
    popen = Mock(return_value="process")
    monkeypatch.setattr(platform_support.subprocess, "CREATE_NEW_CONSOLE", 16, raising=False)
    monkeypatch.setattr(platform_support.subprocess, "Popen", popen)

    result = support.run_script_file(script, cwd=tmp_path)

    assert result == "process"
    popen.assert_called_once_with([str(script)], cwd=tmp_path, creationflags=16)


def test_windows_run_script_file_rejects_cmd_metacharacters(monkeypatch):
    support = PlatformSupport(PlatformInfo("win32", "AMD64"))
    popen = Mock()
    monkeypatch.setattr(platform_support.subprocess, "Popen", popen)

    with pytest.raises(ValueError):
        support.run_script_file("C:/bad&path/setup.bat")

    popen.assert_not_called()


def test_unix_run_script_file_returns_popen(monkeypatch, tmp_path):
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))
    script = tmp_path / "setup.sh"
    popen = Mock(return_value="process")
    monkeypatch.setattr(platform_support.subprocess, "Popen", popen)

    result = support.run_script_file(script, cwd=tmp_path)

    assert result == "process"
    popen.assert_called_once_with(["/bin/sh", str(script)], cwd=tmp_path)
