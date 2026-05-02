from pathlib import Path

from huggingface_models import (
    build_custom_llm_name,
    build_gguf_llm_entry,
    gguf_siblings_from_api_payload,
    parse_hf_gguf_reference,
    resolve_gguf_file_hint,
    save_custom_llm_entry,
)


def test_parse_direct_huggingface_gguf_url_normalizes_to_resolve_url():
    ref = parse_hf_gguf_reference(
        "https://huggingface.co/example/Gemma-4-GGUF/blob/main/sub/model.Q4_K_M.gguf"
    )

    assert ref.repo_id == "example/Gemma-4-GGUF"
    assert ref.file_path == "sub/model.Q4_K_M.gguf"
    assert ref.url == "https://huggingface.co/example/Gemma-4-GGUF/resolve/main/sub/model.Q4_K_M.gguf"
    assert ref.info_url == "https://huggingface.co/example/Gemma-4-GGUF"


def test_parse_repo_id_accepts_pasted_huggingface_model_name():
    ref = parse_hf_gguf_reference("example/Gemma-4-GGUF")

    assert ref.repo_id == "example/Gemma-4-GGUF"
    assert ref.file_path is None
    assert ref.url is None


def test_parse_repo_id_accepts_colon_variant_hint():
    ref = parse_hf_gguf_reference("example/Gemma-4-GGUF:i1-Q4_K_M")

    assert ref.repo_id == "example/Gemma-4-GGUF"
    assert ref.file_path is None
    assert ref.file_hint == "i1-Q4_K_M"
    assert ref.url is None


def test_parse_huggingface_repo_url_accepts_pasted_model_page_url():
    ref = parse_hf_gguf_reference("https://huggingface.co/example/Gemma-4-GGUF")

    assert ref.repo_id == "example/Gemma-4-GGUF"
    assert ref.file_path is None
    assert ref.url is None


def test_build_gguf_llm_entry_uses_koboldcpp_friendly_defaults():
    entry = build_gguf_llm_entry(
        "example/Gemma-4-GGUF",
        "model.Q4_K_M.gguf",
    )

    assert entry["urls"] == [
        "https://huggingface.co/example/Gemma-4-GGUF/resolve/main/model.Q4_K_M.gguf"
    ]
    assert entry["context_size"] == 131072
    assert entry["max_gpu_layer"] == 99
    assert entry["launch_args"] == ["--jinja"]


def test_gguf_siblings_from_api_payload_returns_sorted_gguf_paths():
    payload = {
        "siblings": [
            {"rfilename": "README.md"},
            {"rfilename": "b/model.Q5_K_M.gguf"},
            {"rfilename": "a/model.Q4_K_M.GGUF"},
        ]
    }

    assert gguf_siblings_from_api_payload(payload) == [
        "a/model.Q4_K_M.GGUF",
        "b/model.Q5_K_M.gguf",
    ]


def test_resolve_gguf_file_hint_accepts_quant_suffix():
    files = [
        "gemma-4-31B-it-uncensored-heretic.i1-Q3_K_M.gguf",
        "gemma-4-31B-it-uncensored-heretic.i1-Q4_K_M.gguf",
        "gemma-4-31B-it-uncensored-heretic.i1-Q5_K_M.gguf",
    ]

    assert (
        resolve_gguf_file_hint(files, "i1-Q4_K_M")
        == "gemma-4-31B-it-uncensored-heretic.i1-Q4_K_M.gguf"
    )


def test_resolve_gguf_file_hint_rejects_ambiguous_hint():
    files = [
        "a/model.i1-Q4_K_M.gguf",
        "b/model.i1-Q4_K_M.gguf",
    ]

    try:
        resolve_gguf_file_hint(files, "i1-Q4_K_M")
    except ValueError as error:
        assert "複数" in str(error)
    else:
        raise AssertionError("expected ValueError")


def test_resolve_gguf_file_hint_truncates_long_error_file_lists():
    files = [f"model-{index:02d}.Q4_K_M.gguf" for index in range(21)]

    try:
        resolve_gguf_file_hint(files, "missing")
    except ValueError as error:
        assert "...他 1 件" in str(error)
    else:
        raise AssertionError("expected ValueError")


def test_save_custom_llm_entry_merges_existing_file(tmp_path):
    llm_path = tmp_path / "llm.json"
    llm_path.write_text('{"Existing": {"urls": ["https://example.com/model.gguf"]}}', encoding="utf-8-sig")
    entry = build_gguf_llm_entry("example/Gemma-4-GGUF", "model.Q4_K_M.gguf")

    save_custom_llm_entry(llm_path, "Hugging Face/example Gemma", entry)

    text = llm_path.read_text(encoding="utf-8-sig")
    assert "Existing" in text
    assert "Hugging Face/example Gemma" in text


def test_build_custom_llm_name_does_not_add_extra_category_slashes():
    name = build_custom_llm_name("example/Gemma-4-GGUF", "sub/model.Q4_K_M.gguf")

    assert name == "Hugging Face/example - Gemma-4-GGUF model.Q4_K_M"
