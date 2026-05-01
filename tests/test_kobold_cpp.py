import os
from unittest.mock import Mock

from kobold_cpp import KoboldCpp
import kobold_cpp
from path import Path as AppPath
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


def test_build_launch_args_uses_platform_binary_and_model_launch_args(tmp_path):
    kobold_dir = tmp_path / "KoboldCpp"
    kobold_dir.mkdir()
    model_path = kobold_dir / "modern.gguf"
    model_path.write_text("", encoding="utf-8")
    ctx = DummyContext(tmp_path)
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))
    kobold = KoboldCpp(ctx, platform_support=support, kobold_cpp_dir=kobold_dir)

    args = kobold.build_launch_args("Modern", 7)

    assert args[0].endswith("koboldcpp-linux-x64")
    assert "--gpulayers" in args
    assert "7" in args
    assert "--contextsize" in args
    assert "8192" in args
    assert "--jinja" in args
    assert str(model_path) in args


def test_build_generate_payload_merges_model_generate_args(tmp_path):
    kobold_dir = tmp_path / "KoboldCpp"
    kobold_dir.mkdir()
    ctx = DummyContext(tmp_path)
    kobold = KoboldCpp(
        ctx,
        platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")),
        kobold_cpp_dir=kobold_dir,
    )

    payload = kobold.build_generate_payload("hello")

    assert payload["prompt"] == "hello"
    assert payload["max_context_length"] == 8192
    assert payload["stop_sequence"] == ["<|im_end|>"]
    assert payload["reasoning_effort"] == "low"


def test_init_does_not_mutate_global_path_constants(tmp_path):
    kobold_dir = tmp_path / "custom-kobold"
    before = (
        AppPath.kobold_cpp,
        AppPath.kobold_cpp_win,
        AppPath.kobold_cpp_linux,
        AppPath.kobold_cpp_mac_arm64,
    )

    KoboldCpp(
        DummyContext(tmp_path),
        platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")),
        kobold_cpp_dir=kobold_dir,
    )

    after = (
        AppPath.kobold_cpp,
        AppPath.kobold_cpp_win,
        AppPath.kobold_cpp_linux,
        AppPath.kobold_cpp_mac_arm64,
    )
    assert after == before


def test_download_model_uses_curl_argv_without_shell(tmp_path, monkeypatch):
    kobold_dir = tmp_path / "KoboldCpp"
    ctx = DummyContext(tmp_path)
    run = Mock(return_value=Mock(returncode=0))
    replace = Mock()
    monkeypatch.setattr(kobold_cpp.webbrowser, "open", Mock())
    monkeypatch.setattr(kobold_cpp.subprocess, "run", run)
    monkeypatch.setattr(kobold_cpp.os, "replace", replace)
    kobold = KoboldCpp(
        ctx,
        platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")),
        kobold_cpp_dir=kobold_dir,
    )

    result = kobold.download_model("Modern")

    assert result is None
    run.assert_called_once()
    cmd = run.call_args.args[0]
    assert cmd[:4] == ["curl", "-k", "-L", "-f"]
    assert "-O" not in cmd
    assert cmd[-1] == "https://huggingface.co/example/modern/resolve/main/modern.gguf"
    temp_path = cmd[cmd.index("-o") + 1]
    assert os.path.dirname(temp_path) == str(kobold_dir)
    assert os.path.basename(temp_path) != "modern.gguf"
    run.assert_called_once_with(cmd, cwd=str(kobold_dir))
    replace.assert_called_once_with(temp_path, str(kobold_dir / "modern.gguf"))


def test_download_model_removes_temp_file_after_curl_failure(tmp_path, monkeypatch):
    kobold_dir = tmp_path / "KoboldCpp"
    ctx = DummyContext(tmp_path)
    temp_paths = []

    def failed_run(cmd, cwd):
        temp_path = cmd[cmd.index("-o") + 1]
        temp_paths.append(temp_path)
        assert cwd == str(kobold_dir)
        assert "-f" in cmd
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write("404 page")
        return Mock(returncode=22)

    monkeypatch.setattr(kobold_cpp.webbrowser, "open", Mock())
    monkeypatch.setattr(kobold_cpp.subprocess, "run", failed_run)
    kobold = KoboldCpp(
        ctx,
        platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")),
        kobold_cpp_dir=kobold_dir,
    )

    result = kobold.download_model("Modern")

    assert "Modern" in result
    assert temp_paths
    assert not os.path.exists(temp_paths[0])
    assert not (kobold_dir / "modern.gguf").exists()


def test_init_writes_bat_with_launch_args_and_quoted_model_name(tmp_path):
    kobold_dir = tmp_path / "KoboldCpp"
    ctx = DummyContext(tmp_path)
    ctx.llm["Modern"]["launch_args"] = ["--jinja", "--template", "chat template.jinja"]

    KoboldCpp(
        ctx,
        platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")),
        kobold_cpp_dir=kobold_dir,
    )

    bat_text = (kobold_dir / "Run-Modern-C8K-L0.bat").read_text(encoding="utf-8")
    assert "--jinja" in bat_text
    assert '--template "chat template.jinja"' in bat_text
    assert '"modern.gguf"' in bat_text


def test_launch_server_launches_built_command_with_kobold_dir(tmp_path, monkeypatch):
    kobold_dir = tmp_path / "KoboldCpp"
    kobold_dir.mkdir()
    (kobold_dir / "modern.gguf").write_text("", encoding="utf-8")
    ctx = DummyContext(tmp_path)
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))
    support.launch_command = Mock()
    kobold = KoboldCpp(ctx, platform_support=support, kobold_cpp_dir=kobold_dir)
    monkeypatch.setattr(kobold, "get_model", Mock(return_value=None))
    expected_command = kobold.build_launch_args("Modern", 7)

    result = kobold.launch_server()

    assert result is None
    support.launch_command.assert_called_once_with(expected_command, cwd=str(kobold_dir))


def test_generate_posts_payload_and_returns_text(tmp_path, monkeypatch):
    kobold_dir = tmp_path / "KoboldCpp"
    log_path = tmp_path / "generate-log.txt"
    ctx = DummyContext(tmp_path)
    response = Mock(status_code=200)
    response.json.return_value = {"results": [{"text": " world"}]}
    post = Mock(return_value=response)
    monkeypatch.setattr(kobold_cpp.requests, "post", post)
    monkeypatch.setattr(AppPath, "generate_log", str(log_path))
    kobold = KoboldCpp(
        ctx,
        platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")),
        kobold_cpp_dir=kobold_dir,
    )

    result = kobold.generate("hello")

    assert result == " world"
    post.assert_called_once()
    assert post.call_args.args == (kobold.generate_url,)
    posted_json = post.call_args.kwargs["json"]
    assert posted_json["prompt"] == "hello"
    assert posted_json["reasoning_effort"] == "low"


def test_build_launch_args_shlex_splits_user_koboldcpp_arg(tmp_path):
    kobold_dir = tmp_path / "KoboldCpp"
    ctx = DummyContext(tmp_path)
    ctx["koboldcpp_arg"] = '--usecublas --threads "8 workers"'
    kobold = KoboldCpp(
        ctx,
        platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")),
        kobold_cpp_dir=kobold_dir,
    )

    args = kobold.build_launch_args("Modern", 7)

    assert "--threads" in args
    assert "8 workers" in args
