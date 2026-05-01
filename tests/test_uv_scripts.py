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
    assert "uv run --with-requirements ./EasyNovelAssistant/setup/res/requirements.txt" in setup_text
    assert "uv run --with-requirements ./EasyNovelAssistant/setup/res/requirements.txt" in run_text


def test_windows_scripts_run_app_through_uv_requirements():
    setup_text = read_text(ROOT / "EasyNovelAssistant" / "setup" / "Setup-EasyNovelAssistant.bat")
    run_text = read_text(ROOT / "Run-EasyNovelAssistant.bat")

    assert "%UV_CMD% run --with-requirements %~dp0res\\requirements.txt" in setup_text
    assert '"%UV_CMD%" run --with-requirements EasyNovelAssistant\\setup\\res\\requirements.txt' in run_text
