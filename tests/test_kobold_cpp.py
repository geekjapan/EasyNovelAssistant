import os
from pathlib import Path

from kobold_cpp import KoboldCpp
from platform_support import PlatformInfo, PlatformSupport


class DummyContext(dict):
    def __init__(self, tmp_path):
        super().__init__(
            koboldcpp_host="localhost",
            koboldcpp_port=5001,
            koboldcpp_command_timeout=0.05,
            koboldcpp_arg="--usecublas",
            llm_name="Modern",
            llm_gpu_layer=7,
            llm_context_size=8192,
            max_length=512,
            rep_pen=1.1,
            rep_pen_range=320,
            rep_pen_slope=0.7,
            temperature=0.7,
            tfs=1,
            top_a=0,
            top_k=100,
            top_p=0.92,
            typical=1,
            min_p=0,
            sampler_order=[6, 0, 1, 3, 4, 2, 5],
        )
        self.llm = {
            "Modern": {
                "urls": ["https://huggingface.co/example/modern/resolve/main/modern.gguf"],
                "context_size": 32768,
                "max_gpu_layer": 99,
                "launch_args": ["--jinja"],
                "generate_args": {"reasoning_effort": "low"},
                "stop_sequence": ["<|im_end|>"],
            }
        }
        self.llm_sequence = {}
        self.tmp_path = tmp_path


def test_build_launch_args_uses_platform_binary_and_model_launch_args(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    kobold_dir = tmp_path / "KoboldCpp"
    kobold_dir.mkdir()
    model_path = kobold_dir / "modern.gguf"
    model_path.write_text("", encoding="utf-8")
    ctx = DummyContext(tmp_path)
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))
    kobold = KoboldCpp(ctx, platform_support=support)

    args = kobold.build_launch_args("Modern", 7)

    assert args[0].endswith("koboldcpp-linux-x64")
    assert "--gpulayers" in args
    assert "7" in args
    assert "--contextsize" in args
    assert "8192" in args
    assert "--jinja" in args
    assert str(model_path) in args


def test_build_generate_payload_merges_model_generate_args(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "KoboldCpp").mkdir()
    ctx = DummyContext(tmp_path)
    kobold = KoboldCpp(ctx, platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")))

    payload = kobold.build_generate_payload("hello")

    assert payload["prompt"] == "hello"
    assert payload["max_context_length"] == 8192
    assert payload["stop_sequence"] == ["<|im_end|>"]
    assert payload["reasoning_effort"] == "low"
