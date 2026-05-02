import importlib.util
import io
from pathlib import Path
import zipfile

import pytest


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


def test_setup_python_script_builds_style_bert_uv_command(tmp_path, monkeypatch):
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("setup_easy_novel_assistant_style", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv("UV_CMD", "uv")
    monkeypatch.setattr(module.platform, "system", lambda: "Windows")
    monkeypatch.setattr(module.platform, "machine", lambda: "AMD64")
    style_dir = tmp_path / "Style-Bert-VITS2"
    style_dir.mkdir()
    (style_dir / "requirements.txt").write_text(
        "torch<2.4\nfaster-whisper==0.10.1\nnumpy\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "STYLE_BERT_VITS2_DIR", style_dir)

    command = module.style_bert_uv_command("server_fastapi.py")

    assert command[:5] == ["uv", "run", "--no-project", "--python", module.sys.executable]
    assert "--with-requirements" in command
    requirements = style_dir / ".easy_novel_assistant" / "requirements-runtime.txt"
    assert str(requirements) in command
    assert "faster-whisper==0.10.1" in requirements.read_text(encoding="utf-8")
    assert command[-1:] == ["server_fastapi.py"]
    assert "--cpu" not in command
    assert "--extra-index-url" in command
    assert "https://download.pytorch.org/whl/cu118" in command


def test_setup_python_script_reuses_existing_style_bert_repo_without_pull(tmp_path, monkeypatch):
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("setup_easy_novel_assistant_repo", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    style_dir = tmp_path / "Style-Bert-VITS2"
    (style_dir / ".git").mkdir(parents=True)
    calls = []
    monkeypatch.delenv("ENA_UPDATE_STYLE_BERT", raising=False)
    monkeypatch.setattr(module, "STYLE_BERT_VITS2_DIR", style_dir)
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    module.ensure_style_bert_repo()

    assert calls == []


def test_setup_python_script_updates_existing_style_bert_repo_only_when_requested(tmp_path, monkeypatch):
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("setup_easy_novel_assistant_repo_update", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    style_dir = tmp_path / "Style-Bert-VITS2"
    (style_dir / ".git").mkdir(parents=True)
    calls = []
    monkeypatch.setenv("ENA_UPDATE_STYLE_BERT", "1")
    monkeypatch.setattr(module, "STYLE_BERT_VITS2_DIR", style_dir)
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    module.ensure_style_bert_repo()

    assert calls[0][0][0] == ["git", "-C", str(style_dir), "pull", "--ff-only"]
    assert calls[0][1] == {"check": True}


def test_setup_python_script_rejects_non_git_style_bert_dir(tmp_path, monkeypatch):
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("setup_easy_novel_assistant_repo_bad", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    style_dir = tmp_path / "Style-Bert-VITS2"
    style_dir.mkdir()
    monkeypatch.setattr(module, "STYLE_BERT_VITS2_DIR", style_dir)

    with pytest.raises(RuntimeError, match="not a git repository"):
        module.ensure_style_bert_repo()


def test_setup_python_script_style_bert_initialize_current_checks_state_and_markers(tmp_path, monkeypatch):
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("setup_easy_novel_assistant_init_current", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    style_dir = tmp_path / "Style-Bert-VITS2"
    (style_dir / "bert" / "ja").mkdir(parents=True)
    (style_dir / "bert" / "bert_models.json").write_text(
        '{"ja": {"files": ["model.bin"]}}',
        encoding="utf-8",
    )
    (style_dir / "marker.bin").write_text("", encoding="utf-8")
    (style_dir / "bert" / "ja" / "model.bin").write_text("", encoding="utf-8")
    state = tmp_path / "setup-state.json"
    monkeypatch.setattr(module, "STYLE_BERT_VITS2_DIR", style_dir)
    monkeypatch.setattr(module, "STYLE_BERT_SETUP_STATE", state)
    monkeypatch.setattr(module, "STYLE_BERT_INITIALIZE_MARKERS", ["marker.bin"])
    monkeypatch.setattr(module, "style_bert_repo_head", lambda: "abc123")
    module.write_json_file(state, {"style_bert_head": "abc123"})

    assert module.style_bert_initialize_is_current() is True
    (style_dir / "marker.bin").unlink()
    assert module.style_bert_initialize_is_current() is False


def test_setup_python_script_read_json_file_returns_default_for_corrupt_json(tmp_path):
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("setup_easy_novel_assistant_json_read", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    state = tmp_path / "setup-state.json"
    state.write_text("{broken", encoding="utf-8")

    assert module.read_json_file(state, default={"style_bert_head": None}) == {"style_bert_head": None}


def test_setup_python_script_write_json_file_replaces_state_atomically(tmp_path, monkeypatch):
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("setup_easy_novel_assistant_json_write", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    state = tmp_path / "setup-state.json"
    state.write_text('{"style_bert_head": "old"}\n', encoding="utf-8")
    replace_calls = []
    real_replace = module.os.replace

    def replace(tmp_path, final_path):
        replace_calls.append((tmp_path, final_path))
        real_replace(tmp_path, final_path)

    monkeypatch.setattr(module.os, "replace", replace)

    module.write_json_file(state, {"style_bert_head": "new"})

    assert replace_calls == [(state.with_name("setup-state.json.tmp"), state)]
    assert module.read_json_file(state) == {"style_bert_head": "new"}
    assert not state.with_name("setup-state.json.tmp").exists()


def test_setup_python_script_skips_style_bert_initialize_when_current(tmp_path, monkeypatch):
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("setup_easy_novel_assistant_init_skip", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = tmp_path / "config.yml"
    config_source = tmp_path / "source_config.yml"
    config_source.write_text("server:\n", encoding="utf-8")
    calls = []
    monkeypatch.setattr(module, "STYLE_BERT_MODELS", [])
    monkeypatch.setattr(module, "STYLE_BERT_VITS2_CONFIG", config)
    monkeypatch.setattr(module, "STYLE_BERT_VITS2_CONFIG_SOURCE", config_source)
    monkeypatch.setattr(module, "ensure_windows_ffmpeg_bundle", lambda: None)
    monkeypatch.setattr(module, "style_bert_initialize_is_current", lambda: True)
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    module.ensure_style_bert_assets()

    assert calls == []
    assert config.exists()


def test_setup_python_script_default_style_bert_models_are_currently_available():
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("setup_easy_novel_assistant_models", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    repos = {repo_id for repo_id, _model_dir, _model_name, _model_safetensors in module.STYLE_BERT_MODELS}

    assert repos == {"RinneAi/Rinne_Style-Bert-VITS2"}
    assert all(repo_id != "kaunista/kaunista-style-bert-vits2-models" for repo_id in repos)


def test_setup_python_script_skips_cuda_index_on_macos():
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("setup_easy_novel_assistant_style_macos", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    args = module.style_bert_uv_dependencies("Darwin")

    assert "torch" in args
    assert "--extra-index-url" not in args
    assert "https://download.pytorch.org/whl/cu118" not in args


def test_setup_python_script_rejects_unsafe_zip_member(tmp_path):
    script = ROOT / "EasyNovelAssistant" / "setup" / "setup_easy_novel_assistant.py"
    spec = importlib.util.spec_from_file_location("setup_easy_novel_assistant_zip", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("../evil.txt", "bad")
    data.seek(0)

    with zipfile.ZipFile(data) as archive:
        with pytest.raises(RuntimeError, match="Unsafe archive member"):
            module.safe_extract_zip(archive, tmp_path)


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
