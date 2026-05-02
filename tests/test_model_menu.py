import sys
from types import SimpleNamespace
from unittest.mock import Mock

sys.modules.setdefault(
    "tkinter",
    SimpleNamespace(Menu=Mock(), BooleanVar=Mock(), END="end", messagebox=Mock(), simpledialog=Mock()),
)

from menu import model_menu


def test_add_huggingface_model_resolves_variant_and_updates_context(monkeypatch, tmp_path):
    llm_path = tmp_path / "llm.json"
    monkeypatch.setattr(model_menu.Path, "llm", llm_path)
    monkeypatch.setattr(
        model_menu.simpledialog,
        "askstring",
        lambda *args, **kwargs: "example/Gemma-4-GGUF:i1-Q4_K_M",
    )
    monkeypatch.setattr(
        model_menu,
        "fetch_hf_model_payload",
        lambda repo_id: {
            "siblings": [
                {"rfilename": "gemma-4.i1-Q3_K_M.gguf"},
                {"rfilename": "gemma-4.i1-Q4_K_M.gguf"},
            ]
        },
    )
    shown = {}
    monkeypatch.setattr(model_menu.messagebox, "showinfo", lambda title, message, parent=None: shown.update(title=title))

    menu = object.__new__(model_menu.ModelMenu)
    menu.form = SimpleNamespace(win=None)
    menu.ctx = SimpleNamespace(llm={})

    menu.add_huggingface_model()

    llm_name = "Hugging Face/example - Gemma-4-GGUF gemma-4.i1-Q4_K_M"
    assert shown["title"] == "Hugging Face GGUFモデルを追加"
    assert llm_name in menu.ctx.llm
    assert menu.ctx.llm[llm_name]["urls"] == [
        "https://huggingface.co/example/Gemma-4-GGUF/resolve/main/gemma-4.i1-Q4_K_M.gguf"
    ]
    assert menu.ctx.llm[llm_name]["launch_args"] == ["--jinja"]
    assert llm_path.exists()
