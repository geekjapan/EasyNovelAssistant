import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


APP_SCRIPTS = [
    ROOT / "EasyNovelAssistant" / "setup" / "ActivateVirtualEnvironment.bat",
    ROOT / "EasyNovelAssistant" / "setup" / "Setup-EasyNovelAssistant.bat",
    ROOT / "EasyNovelAssistant" / "setup" / "Install-EasyNovelAssistant.bat",
    ROOT / "Run-EasyNovelAssistant.bat",
]


def read_text(path):
    return path.read_text(encoding="utf-8-sig")


def test_app_scripts_do_not_create_or_activate_virtualenvs():
    forbidden = ["-m venv", "-m virtualenv", "Scripts\\activate.bat", "venv\\Scripts", "venv/bin/activate"]

    for script in APP_SCRIPTS:
        text = read_text(script)
        for marker in forbidden:
            assert marker not in text, f"{script.relative_to(ROOT)} still contains {marker}"


def test_path_points_ffplay_at_downloaded_ffmpeg_bundle():
    from path import Path as AppPath

    assert AppPath.ffplay.endswith("EasyNovelAssistant/setup/lib/ffmpeg-master-latest-win64-gpl/bin/ffplay.exe")


def test_shell_wrappers_are_removed_from_primary_flow():
    removed = [
        ROOT / "EasyNovelAssistant" / "setup" / "Setup-EasyNovelAssistant.sh",
        ROOT / "EasyNovelAssistant" / "setup" / "Install-EasyNovelAssistant.sh",
        ROOT / "Run-EasyNovelAssistant.sh",
        ROOT / "EasyNovelAssistant" / "setup" / "res" / "Server_cpu.bat",
        ROOT / "EasyNovelAssistant" / "setup" / "Setup-Style-Bert-VITS2.bat",
        ROOT / "EasyNovelAssistant" / "setup" / "Run-Style-Bert-VITS2.bat",
        ROOT / "Activate-venv.bat",
        ROOT / "Update-KoboldCpp.bat",
        ROOT / "Update-KoboldCpp_CUDA12.bat",
        ROOT / "KoboldCpp" / "Launch-Ocuteus-v1-Q8_0-C16K-L0.bat",
    ]

    assert all(not path.exists() for path in removed)


def test_readme_uses_uv_wrapper_for_setup_and_launch():
    text = read_text(ROOT / "README.md")

    assert "uv run EasyNovelAssistant/setup/ena.py setup" in text
    assert "uv run EasyNovelAssistant/setup/ena.py run" in text
    assert "sh Run-EasyNovelAssistant.sh" not in text
    assert "Run-Style-Bert-VITS2.bat" not in text


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


def test_ena_python_script_has_pep723_metadata():
    script = ROOT / "EasyNovelAssistant" / "setup" / "ena.py"
    text = read_text(script)

    assert text.startswith("# /// script\n")
    assert "# requires-python = \">=3.10\"" in text
    assert "# dependencies = [" in text


def test_setup_python_script_dependencies_match_requirements():
    scripts = [
        ROOT / "EasyNovelAssistant" / "setup" / "ena.py",
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


def test_setup_python_script_builds_style_bert_uv_command():
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("setup_easy_novel_assistant_style", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    command = module.style_bert_uv_command("server_fastapi.py")

    assert command[:4] == ["uv", "run", "--python", module.sys.executable]
    assert "--with-requirements" in command
    assert command[-1:] == ["server_fastapi.py"]
    assert "--cpu" not in command
    assert "https://download.pytorch.org/whl/cu118" in command


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

    assert "%UV_CMD% run --python %PYTHON_CMD% %~dp0ena.py setup" in setup_text
    assert '"%UV_CMD%" run --python %PYTHON_CMD% EasyNovelAssistant\\setup\\ena.py run' in run_text
