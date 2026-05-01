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
    assert loaded[0]["speech_enabled"] is True
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
    sequences = load_json(
        ROOT / "EasyNovelAssistant" / "setup" / "res" / "default_llm_sequence.json"
    )

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

    gemma = llms["最新・汎用/Gemma-3-12B-it-Q4_K_M"]
    assert gemma["context_size"] == 131072
    assert gemma["max_gpu_layer"] == 99
    assert gemma["launch_args"] == ["--jinja"]
    assert gemma["generate_args"] == {}

    qwen3 = llms["最新・日本語/Qwen3-14B-Q4_K_M"]
    assert qwen3["context_size"] == 131072
    assert qwen3["max_gpu_layer"] == 99
    assert qwen3["launch_args"] == ["--jinja"]
    assert qwen3["generate_args"] == {"reasoning_effort": "low"}
    assert qwen3["stop_sequence"] == ["<|im_end|>"]

    chat_template = sequences["ChatTemplate"]
    assert "Qwen3" in chat_template["model_names"]
    assert "gemma-3" in chat_template["model_names"]
