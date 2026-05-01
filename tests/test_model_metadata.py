from model_metadata import normalize_llm_entry, normalize_llm_map


def test_normalize_llm_entry_derives_name_files_and_info_url():
    llm = {
        "urls": [
            "https://huggingface.co/example/repo/resolve/main/model-a.gguf",
            "https://huggingface.co/example/repo/resolve/main/model-b.gguf",
        ],
        "context_size": 32768,
        "max_gpu_layer": 33,
    }

    normalize_llm_entry("Category/Example Model", llm)

    assert llm["name"] == "Model"
    assert llm["file_names"] == ["model-a.gguf", "model-b.gguf"]
    assert llm["file_name"] == "model-a.gguf"
    assert llm["info_url"] == "https://huggingface.co/example/repo"
    assert llm["launch_args"] == []
    assert llm["generate_args"] == {}
    assert llm["stop_sequence"] is None


def test_normalize_llm_map_keeps_optional_modern_fields():
    llms = {
        "Modern": {
            "urls": ["https://huggingface.co/example/modern/resolve/main/modern.gguf"],
            "context_size": 131072,
            "max_gpu_layer": 99,
            "launch_args": ["--jinja"],
            "generate_args": {"reasoning_effort": "low"},
            "stop_sequence": ["<|im_end|>"],
        }
    }

    normalize_llm_map(llms)

    assert llms["Modern"]["launch_args"] == ["--jinja"]
    assert llms["Modern"]["generate_args"] == {"reasoning_effort": "low"}
    assert llms["Modern"]["stop_sequence"] == ["<|im_end|>"]


def test_normalize_llm_entry_preserves_explicit_info_url():
    llm = {
        "urls": ["https://huggingface.co/example/repo/resolve/main/model.gguf"],
        "context_size": 32768,
        "max_gpu_layer": 33,
        "info_url": "https://example.com/custom-model-info",
    }

    normalize_llm_entry("Category/Example Model", llm)

    assert llm["info_url"] == "https://example.com/custom-model-info"
