import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

sys.modules.setdefault(
    "tkinter",
    SimpleNamespace(Menu=Mock(), BooleanVar=Mock(), END="end"),
)

import menu.tool_menu as tool_menu
from menu.tool_menu import ToolMenu


def make_tool_menu(platform):
    menu = ToolMenu.__new__(ToolMenu)
    menu.platform = platform
    return menu


def make_style_dir(tmp_path):
    style_dir = tmp_path / "style-bert"
    style_dir.mkdir()
    (style_dir / "requirements.txt").write_text(
        "torch<2.4\nfaster-whisper==0.10.1\nnumpy\n",
        encoding="utf-8",
    )
    return str(style_dir)


def test_init_accepts_platform_support():
    platform = Mock()
    form = SimpleNamespace(win=object(), menu_bar=Mock())

    menu = ToolMenu(form, Mock(), platform_support=platform)

    assert menu.platform is platform


def test_run_kobold_cpp_uses_platform_launcher(monkeypatch):
    platform = Mock()
    platform.kobold_cpp_path.return_value = "/tools/kobold/koboldcpp-linux-x64"
    menu = make_tool_menu(platform)
    monkeypatch.setattr(tool_menu.Path, "kobold_cpp", "/tools/kobold")

    menu._run_kobold_cpp()

    platform.kobold_cpp_path.assert_called_once_with("/tools/kobold")
    platform.launch_command.assert_called_once_with(
        ["/tools/kobold/koboldcpp-linux-x64"],
        cwd="/tools/kobold",
    )


def test_windows_run_style_bert_vits2_uses_uv_launcher(tmp_path, monkeypatch):
    platform = Mock()
    platform.is_windows.return_value = True
    platform.is_macos.return_value = False
    platform.resolve_uv.return_value = "uv"
    menu = make_tool_menu(platform)
    subprocess_run = Mock()
    monkeypatch.setattr(subprocess, "run", subprocess_run)
    monkeypatch.setattr(tool_menu.Path, "style_bert_vits2", make_style_dir(tmp_path))

    menu._run_style_bert_vits2("app.py")

    command = platform.launch_command.call_args.args[0]
    assert command[:5] == ["uv", "run", "--no-project", "--python", sys.executable]
    assert command[-1:] == ["app.py"]
    assert "https://download.pytorch.org/whl/cu118" in command
    subprocess_run.assert_not_called()


def test_unix_run_style_bert_vits2_uses_resolved_python_and_split_args(tmp_path, monkeypatch):
    platform = Mock()
    platform.is_windows.return_value = False
    platform.is_macos.return_value = False
    platform.resolve_uv.return_value = "uv"
    menu = make_tool_menu(platform)
    style_dir = make_style_dir(tmp_path)
    monkeypatch.setattr(tool_menu.Path, "style_bert_vits2", style_dir)

    menu._run_style_bert_vits2("server_editor.py --inbrowser")

    command = platform.launch_command.call_args.args[0]
    assert command[:5] == ["uv", "run", "--no-project", "--python", sys.executable]
    assert command[-2:] == ["server_editor.py", "--inbrowser"]
    assert "--with-requirements" in command
    requirements = tmp_path / "style-bert" / ".easy_novel_assistant" / "requirements-runtime.txt"
    assert str(requirements) in command
    assert "faster-whisper" not in requirements.read_text(encoding="utf-8")
    platform.launch_command.assert_called_once()
    assert platform.launch_command.call_args.kwargs == {"cwd": style_dir}
