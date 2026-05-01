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
    ROOT / "EasyNovelAssistant" / "setup" / "Setup-Style-Bert-VITS2.bat",
    ROOT / "EasyNovelAssistant" / "setup" / "Run-Style-Bert-VITS2.bat",
    ROOT / "EasyNovelAssistant" / "setup" / "res" / "Server_cpu.bat",
]


def read_text(path):
    return path.read_text(encoding="utf-8-sig")


def test_app_scripts_do_not_create_or_activate_virtualenvs():
    forbidden = ["-m venv", "-m virtualenv", "Scripts\\activate.bat", "venv\\Scripts", "venv/bin/activate"]

    for script in APP_SCRIPTS:
        text = read_text(script)
        for marker in forbidden:
            assert marker not in text, f"{script.relative_to(ROOT)} still contains {marker}"


def test_style_bert_scripts_run_python_through_uv():
    setup_text = read_text(ROOT / "EasyNovelAssistant" / "setup" / "Setup-Style-Bert-VITS2.bat")
    run_text = read_text(ROOT / "EasyNovelAssistant" / "setup" / "Run-Style-Bert-VITS2.bat")
    server_cpu_text = read_text(ROOT / "EasyNovelAssistant" / "setup" / "res" / "Server_cpu.bat")

    assert '"%UV_CMD%" run --python "%PYTHON_CMD%" %STYLE_BERT_UV_DEPS% initialize.py' in setup_text
    assert '"%UV_CMD%" run --python "%PYTHON_CMD%" %STYLE_BERT_UV_DEPS% server_fastapi.py %*' in run_text
    assert '"%UV_CMD%" run --python "%PYTHON_CMD%" %STYLE_BERT_UV_DEPS% server_fastapi.py --cpu' in server_cpu_text
    assert "pip install" not in setup_text
    assert "python server_fastapi.py" not in run_text


def test_unix_scripts_run_app_through_uv_requirements():
    setup_text = read_text(ROOT / "EasyNovelAssistant" / "setup" / "Setup-EasyNovelAssistant.sh")
    run_text = read_text(ROOT / "Run-EasyNovelAssistant.sh")

    assert "command -v uv" in setup_text
    assert "uv run ./EasyNovelAssistant/setup/setup_easy_novel_assistant.py" in setup_text
    assert "uv run ./EasyNovelAssistant/setup/run_easy_novel_assistant.py" in run_text


def test_readme_uses_uv_for_unix_setup_and_launch():
    text = read_text(ROOT / "README.md")

    assert "uv run EasyNovelAssistant/setup/setup_easy_novel_assistant.py" in text
    assert "uv run EasyNovelAssistant/setup/run_easy_novel_assistant.py" in text
    assert "sh Run-EasyNovelAssistant.sh" not in text


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


def test_run_python_script_has_pep723_metadata():
    script = ROOT / "EasyNovelAssistant" / "setup" / "run_easy_novel_assistant.py"
    text = read_text(script)

    assert text.startswith("# /// script\n")
    assert "# requires-python = \">=3.10\"" in text
    assert "# dependencies = [" in text
    assert '#     "requests==2.33.1",' in text
    assert '#     "tkinterdnd2==0.4.3",' in text
    assert '#     "scipy==1.15.3",' in text
    assert '#     "watchdog==6.0.0",' in text


def test_setup_python_script_dependencies_match_requirements():
    scripts = [
        ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py",
        ROOT / "EasyNovelAssistant" / "setup" / "run_easy_novel_assistant.py",
    ]
    requirements = ROOT / "EasyNovelAssistant" / "setup" / "res" / "requirements.txt"
    required = [line.strip() for line in read_text(requirements).splitlines() if line.strip()]

    for script in scripts:
        script_text = read_text(script)
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


def test_setup_python_script_runs_speech_setup_during_initial_setup(monkeypatch):
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("setup_easy_novel_assistant_speech", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls = []

    monkeypatch.setattr(module, "ensure_app_dependencies", lambda: calls.append("deps"))
    monkeypatch.setattr(module, "ensure_kobold_cpp", lambda: calls.append("kobold") or Path("kobold"))
    monkeypatch.setattr(module, "ensure_default_model", lambda: calls.append("model") or Path("model"))
    monkeypatch.setattr(module, "ensure_speech_engine", lambda: calls.append("speech") or None)
    monkeypatch.setattr(module.os, "chdir", lambda _path: None)

    module.main()

    assert calls == ["deps", "kobold", "model", "speech"]


def test_run_python_script_builds_sample_urls_without_empty_path_segments():
    script = ROOT / "EasyNovelAssistant" / "setup" / "run_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("run_easy_novel_assistant", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.build_sample_url("", "sample.json") == "https://yyy.wpx.jp/EasyNovelAssistant/sample/sample.json"
    assert (
        module.build_sample_url("GoalSeek", "00-企画.txt")
        == "https://yyy.wpx.jp/EasyNovelAssistant/sample/GoalSeek/00-%E4%BC%81%E7%94%BB.txt"
    )


def test_windows_scripts_run_app_through_uv_requirements():
    setup_text = read_text(ROOT / "EasyNovelAssistant" / "setup" / "Setup-EasyNovelAssistant.bat")
    run_text = read_text(ROOT / "Run-EasyNovelAssistant.bat")

    assert "%UV_CMD% run --python %PYTHON_CMD% %~dp0setup_easy_novel_assistant.py" in setup_text
    assert '"%UV_CMD%" run --python %PYTHON_CMD% EasyNovelAssistant\\setup\\run_easy_novel_assistant.py' in run_text
