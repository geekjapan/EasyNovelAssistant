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


def test_kobold_cpp_path_joins_binary_name(tmp_path):
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))

    assert support.kobold_cpp_path(tmp_path) == tmp_path / "koboldcpp-linux-x64"


def test_resolve_tool_falls_back_to_path_lookup(tmp_path, monkeypatch):
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))
    monkeypatch.setattr(platform_support.shutil, "which", Mock(return_value="/usr/bin/python"))

    assert support.resolve_tool("python") == "/usr/bin/python"


def test_resolve_tool_returns_tool_name_when_missing(tmp_path, monkeypatch):
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))
    monkeypatch.setattr(platform_support.shutil, "which", Mock(return_value=None))

    assert support.resolve_tool("python") == "python"


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
    popen.assert_called_once_with(
        ["cmd", "/d", "/c", f"call {platform_support.subprocess.list2cmdline([str(script)])} || pause"],
        cwd=tmp_path,
        creationflags=16,
    )


def test_windows_run_script_file_accepts_parentheses_in_path(monkeypatch):
    support = PlatformSupport(PlatformInfo("win32", "AMD64"))
    script = "C:/Users/me/Downloads/EasyNovelAssistant (1)/movie/out.bat"
    popen = Mock(return_value="process")
    monkeypatch.setattr(platform_support.subprocess, "CREATE_NEW_CONSOLE", 16, raising=False)
    monkeypatch.setattr(platform_support.subprocess, "Popen", popen)

    result = support.run_script_file(script)

    assert result == "process"
    popen.assert_called_once_with(
        ["cmd", "/d", "/c", f"call {platform_support.subprocess.list2cmdline([script])} || pause"],
        cwd=None,
        creationflags=16,
    )


def test_windows_run_script_file_passes_args_to_inner_batch(monkeypatch, tmp_path):
    support = PlatformSupport(PlatformInfo("win32", "AMD64"))
    script = tmp_path / "run server.bat"
    popen = Mock(return_value="process")
    monkeypatch.setattr(platform_support.subprocess, "CREATE_NEW_CONSOLE", 16, raising=False)
    monkeypatch.setattr(platform_support.subprocess, "Popen", popen)

    result = support.run_script_file(script, args=["--cpu"], cwd=tmp_path)

    assert result == "process"
    popen.assert_called_once_with(
        ["cmd", "/d", "/c", f"call {platform_support.subprocess.list2cmdline([str(script)])} --cpu || pause"],
        cwd=tmp_path,
        creationflags=16,
    )


@pytest.mark.parametrize("character", ["&", "|", "<", ">", "^"])
def test_windows_run_script_file_rejects_cmd_metacharacters(monkeypatch, character):
    support = PlatformSupport(PlatformInfo("win32", "AMD64"))
    popen = Mock()
    monkeypatch.setattr(platform_support.subprocess, "Popen", popen)

    with pytest.raises(ValueError):
        support.run_script_file(f"C:/bad{character}path/setup.bat")

    popen.assert_not_called()


def test_unix_run_script_file_returns_popen(monkeypatch, tmp_path):
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))
    script = tmp_path / "setup.sh"
    popen = Mock(return_value="process")
    monkeypatch.setattr(platform_support.subprocess, "Popen", popen)

    result = support.run_script_file(script, cwd=tmp_path)

    assert result == "process"
    popen.assert_called_once_with(["/bin/sh", str(script)], cwd=tmp_path)
