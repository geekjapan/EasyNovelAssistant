import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def test_default_json_files_load_with_utf8_sig():
    files = [
        ROOT / "EasyNovelAssistant" / "setup" / "res" / "default_config.json",
        ROOT / "EasyNovelAssistant" / "setup" / "res" / "default_llm.json",
        ROOT / "EasyNovelAssistant" / "setup" / "res" / "default_llm_sequence.json",
    ]

    loaded = [load_json(path) for path in files]

    assert all(isinstance(item, dict) for item in loaded)
    assert "llm_name" in loaded[0]
    assert len(loaded[1]) >= 29
    assert "CommandR" in loaded[2]


def test_python_generated_files_are_ignored():
    gitignore = ROOT / ".gitignore"

    assert gitignore.exists()
    text = gitignore.read_text(encoding="utf-8")
    assert "__pycache__/" in text
    assert "*.py[cod]" in text
    assert ".pytest_cache/" in text


def test_modern_model_entries_have_optional_metadata():
    llms = load_json(ROOT / "EasyNovelAssistant" / "setup" / "res" / "default_llm.json")

    modern_entries = [
        name
        for name, value in llms.items()
        if value.get("launch_args") or value.get("generate_args") or value.get("stop_sequence")
    ]

    assert modern_entries
    for name in modern_entries:
        value = llms[name]
        assert isinstance(value.get("urls"), list)
        assert value["urls"]
        assert isinstance(value.get("context_size"), int)
        assert isinstance(value.get("max_gpu_layer"), int)
