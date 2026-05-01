import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


APP_SCRIPTS = [
    ROOT / "Activate-venv.bat",
    ROOT / "EasyNovelAssistant" / "setup" / "ActivateVirtualEnvironment.bat",
    ROOT / "EasyNovelAssistant" / "setup" / "Setup-EasyNovelAssistant.bat",
    ROOT / "EasyNovelAssistant" / "setup" / "Setup-EasyNovelAssistant.sh",
    ROOT / "EasyNovelAssistant" / "setup" / "Install-EasyNovelAssistant.bat",
    ROOT / "EasyNovelAssistant" / "setup" / "Install-EasyNovelAssistant.sh",
    ROOT / "Run-EasyNovelAssistant.bat",
    ROOT / "Run-EasyNovelAssistant.sh",
]


def read_text(path):
    return path.read_text(encoding="utf-8-sig")


def test_app_scripts_do_not_create_or_activate_virtualenvs():
    forbidden = ["-m venv", "-m virtualenv", "Scripts\\activate.bat", "venv/bin/activate"]

    for script in APP_SCRIPTS:
        text = read_text(script)
        for marker in forbidden:
            assert marker not in text, f"{script.relative_to(ROOT)} still contains {marker}"


def test_unix_scripts_run_app_through_uv_requirements():
    setup_text = read_text(ROOT / "EasyNovelAssistant" / "setup" / "Setup-EasyNovelAssistant.sh")
    run_text = read_text(ROOT / "Run-EasyNovelAssistant.sh")

    assert "command -v uv" in setup_text
    assert "uv run ./EasyNovelAssistant/setup/setup_easy_novel_assistant.py" in setup_text
    assert "uv run --with-requirements ./EasyNovelAssistant/setup/res/requirements.txt" in run_text


def test_setup_python_script_has_pep723_metadata():
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    text = read_text(script)

    assert text.startswith("# /// script\n")
    assert "# requires-python = \">=3.10\"" in text
    assert "# dependencies = [" in text
    assert '#     "requests==2.33.1",' in text
    assert '#     "tkinterdnd2==0.4.3",' in text
    assert '#     "scipy==1.15.3",' in text
    assert '#     "watchdog==6.0.0",' in text


def test_setup_python_script_dependencies_match_requirements():
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    requirements = ROOT / "EasyNovelAssistant" / "setup" / "res" / "requirements.txt"
    script_text = read_text(script)
    required = [line.strip() for line in read_text(requirements).splitlines() if line.strip()]

    for requirement in required:
        assert f'#     "{requirement}",' in script_text


def test_setup_python_script_selects_supported_kobold_binaries():
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("setup_easy_novel_assistant", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.select_kobold_binary("Windows", "AMD64") == "koboldcpp.exe"
    assert module.select_kobold_binary("Linux", "x86_64") == "koboldcpp-linux-x64"
    assert module.select_kobold_binary("Darwin", "arm64") == "koboldcpp-mac-arm64"


def test_windows_scripts_run_app_through_uv_requirements():
    setup_text = read_text(ROOT / "EasyNovelAssistant" / "setup" / "Setup-EasyNovelAssistant.bat")
    run_text = read_text(ROOT / "Run-EasyNovelAssistant.bat")

    assert "%UV_CMD% run --python %PYTHON_CMD% %~dp0setup_easy_novel_assistant.py" in setup_text
    assert '"%UV_CMD%" run --with-requirements EasyNovelAssistant\\setup\\res\\requirements.txt' in run_text
