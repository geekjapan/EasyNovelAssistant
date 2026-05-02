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


def test_windows_run_style_bert_vits2_uses_uv_launcher(monkeypatch):
    platform = Mock()
    platform.is_windows.return_value = True
    platform.resolve_uv.return_value = "uv"
    platform.style_bert_uv_dependencies.return_value = [
        "--with",
        "GPUtil",
        "--with",
        "torch",
        "--extra-index-url",
        "https://download.pytorch.org/whl/cu118",
    ]
    menu = make_tool_menu(platform)
    subprocess_run = Mock()
    monkeypatch.setattr(subprocess, "run", subprocess_run)
    monkeypatch.setattr(tool_menu.Path, "style_bert_vits2", "/style-bert")

    menu._run_style_bert_vits2("app.py")

    command = platform.launch_command.call_args.args[0]
    assert command[:4] == ["uv", "run", "--python", sys.executable]
    assert command[-1:] == ["app.py"]
    assert "https://download.pytorch.org/whl/cu118" in command
    subprocess_run.assert_not_called()


def test_unix_run_style_bert_vits2_uses_resolved_python_and_split_args(monkeypatch):
    platform = Mock()
    platform.is_windows.return_value = False
    platform.resolve_uv.return_value = "uv"
    platform.style_bert_uv_dependencies.return_value = ["--with", "torch"]
    menu = make_tool_menu(platform)
    monkeypatch.setattr(tool_menu.Path, "style_bert_vits2", "/style-bert")

    menu._run_style_bert_vits2("server_editor.py --inbrowser")

    command = platform.launch_command.call_args.args[0]
    assert command[:4] == ["uv", "run", "--python", sys.executable]
    assert command[-2:] == ["server_editor.py", "--inbrowser"]
    assert "--with-requirements" in command
    platform.launch_command.assert_called_once()
    assert platform.launch_command.call_args.kwargs == {"cwd": "/style-bert"}
