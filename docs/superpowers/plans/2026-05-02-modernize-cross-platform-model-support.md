# Modernize Cross-Platform Model Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernize EasyNovelAssistant so current dependencies, KoboldCpp binaries, Windows/macOS/Linux launch paths, and newer GGUF model metadata are handled consistently and covered by tests.

**Architecture:** Add focused helper modules for platform and model behavior, then migrate existing callers to those helpers. Keep the Tkinter UI and existing config merge behavior intact. Build coverage around command construction and payload generation so cross-platform behavior is testable without launching GUI apps or model binaries.

**Tech Stack:** Python 3.10+, Tkinter, requests, tkinterdnd2, scipy, watchdog, pytest, KoboldCpp, Style-Bert-VITS2.

---

## File Structure

- Create: `.gitignore`
  - Ignore Python caches, virtual environments, generated app state, downloaded binaries/models, logs, speech, movie outputs, and samples.
- Create: `pytest.ini`
  - Configure pytest to import application modules from `EasyNovelAssistant/src`.
- Create: `EasyNovelAssistant/src/platform_support.py`
  - Own OS detection, executable selection, venv tool path lookup, and cross-platform process launch helpers.
- Create: `EasyNovelAssistant/src/model_metadata.py`
  - Normalize LLM entries and build optional launch/generation metadata.
- Modify: `EasyNovelAssistant/src/path.py`
  - Keep static paths, add platform-aware KoboldCpp path via `PlatformSupport`.
- Modify: `EasyNovelAssistant/src/kobold_cpp.py`
  - Use model metadata helper, platform helper, list-based subprocess calls, optional model args, and safe payload construction.
- Modify: `EasyNovelAssistant/src/style_bert_vits2.py`
  - Use platform helper for Python path and launch behavior.
- Modify: `EasyNovelAssistant/src/menu/tool_menu.py`
  - Use platform helper for KoboldCpp and Style-Bert-VITS2 tools.
- Modify: `EasyNovelAssistant/src/movie_maker.py`
  - Split command file generation by OS and avoid Windows `start` on macOS/Linux.
- Modify: `EasyNovelAssistant/setup/res/requirements.txt`
  - Update runtime dependency pins.
- Create: `requirements-dev.txt`
  - Pin pytest for development verification.
- Modify: `EasyNovelAssistant/setup/Setup-EasyNovelAssistant.sh`
  - Detect Linux/macOS and download the correct KoboldCpp binary.
- Modify: `Run-EasyNovelAssistant.sh`
  - Use Python/venv robustly and make sample downloads match Windows launcher.
- Modify: `README.md`
  - Document Python 3.10+, platform support, setup commands, and manual verification matrix.
- Modify: `EasyNovelAssistant/setup/res/default_llm.json`
  - Add optional metadata for modern models and at least two current curated presets.
- Create: `tests/conftest.py`
- Create: `tests/test_config_files.py`
- Create: `tests/test_platform_support.py`
- Create: `tests/test_model_metadata.py`
- Create: `tests/test_kobold_cpp.py`
- Create: `tests/test_style_bert_vits2.py`
- Create: `tests/test_movie_maker.py`

## Task 1: Test Harness and Git Hygiene

**Files:**
- Create: `.gitignore`
- Create: `pytest.ini`
- Create: `requirements-dev.txt`
- Create: `tests/conftest.py`
- Create: `tests/test_config_files.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/conftest.py`:

```python
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "EasyNovelAssistant" / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def chdir_repo_root():
    os.chdir(ROOT)
```

Create `tests/test_config_files.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_config_files.py -v`

Expected: FAIL in `test_python_generated_files_are_ignored` because `.gitignore` does not exist yet.

- [ ] **Step 3: Add pytest config and ignores**

Create `.gitignore`:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/

venv/
Style-Bert-VITS2/

config.json
llm.json
llm_sequence.json
log/
speech/
movie/
sample/

KoboldCpp/*.exe
KoboldCpp/koboldcpp-linux-x64
KoboldCpp/koboldcpp-mac-arm64
KoboldCpp/*.gguf
```

Create `pytest.ini`:

```ini
[pytest]
pythonpath = EasyNovelAssistant/src
testpaths = tests
```

Create `requirements-dev.txt`:

```text
pytest==9.0.3
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_config_files.py -v`

Expected: PASS for `test_default_json_files_load_with_utf8_sig`.

- [ ] **Step 5: Commit**

```bash
git add .gitignore pytest.ini requirements-dev.txt tests/conftest.py tests/test_config_files.py
git commit -m "test: add baseline pytest harness"
```

## Task 2: Platform Helper

**Files:**
- Create: `EasyNovelAssistant/src/platform_support.py`
- Test: `tests/test_platform_support.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_platform_support.py`:

```python
from pathlib import Path

import pytest

from platform_support import PlatformInfo, PlatformSupport


def test_kobold_binary_names_by_platform():
    assert PlatformSupport(PlatformInfo("win32", "AMD64")).kobold_cpp_binary_name() == "koboldcpp.exe"
    assert PlatformSupport(PlatformInfo("linux", "x86_64")).kobold_cpp_binary_name() == "koboldcpp-linux-x64"
    assert PlatformSupport(PlatformInfo("darwin", "arm64")).kobold_cpp_binary_name() == "koboldcpp-mac-arm64"


def test_macos_intel_has_clear_error():
    support = PlatformSupport(PlatformInfo("darwin", "x86_64"))

    with pytest.raises(RuntimeError, match="macOS Intel"):
        support.kobold_cpp_binary_name()


def test_venv_tool_path_uses_platform_directory(tmp_path):
    win = PlatformSupport(PlatformInfo("win32", "AMD64"))
    unix = PlatformSupport(PlatformInfo("linux", "x86_64"))

    assert win.venv_tool_path(tmp_path, "python").as_posix().endswith("Scripts/python.exe")
    assert unix.venv_tool_path(tmp_path, "python").as_posix().endswith("bin/python")


def test_kobold_cpp_path_joins_binary_name(tmp_path):
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))

    assert support.kobold_cpp_path(tmp_path) == tmp_path / "koboldcpp-linux-x64"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_platform_support.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'platform_support'`.

- [ ] **Step 3: Implement platform helper**

Create `EasyNovelAssistant/src/platform_support.py`:

```python
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlatformInfo:
    system: str
    machine: str


class PlatformSupport:
    def __init__(self, info=None):
        self.info = info or PlatformInfo(sys.platform, platform.machine())

    def is_windows(self):
        return self.info.system == "win32"

    def is_macos(self):
        return self.info.system == "darwin"

    def is_linux(self):
        return self.info.system.startswith("linux")

    def kobold_cpp_binary_name(self):
        if self.is_windows():
            return "koboldcpp.exe"
        if self.is_linux():
            return "koboldcpp-linux-x64"
        if self.is_macos() and self.info.machine in ("arm64", "aarch64"):
            return "koboldcpp-mac-arm64"
        if self.is_macos():
            raise RuntimeError("macOS Intel is not supported by a default KoboldCpp binary. Configure a custom binary.")
        raise RuntimeError(f"Unsupported platform for KoboldCpp: {self.info.system} {self.info.machine}")

    def kobold_cpp_path(self, kobold_cpp_dir):
        return Path(kobold_cpp_dir) / self.kobold_cpp_binary_name()

    def venv_tool_path(self, venv_dir, tool_name):
        executable = tool_name
        if self.is_windows() and not executable.endswith(".exe"):
            executable += ".exe"
        subdir = "Scripts" if self.is_windows() else "bin"
        return Path(venv_dir) / subdir / executable

    def resolve_tool(self, venv_dir, tool_name):
        venv_path = self.venv_tool_path(venv_dir, tool_name)
        if venv_path.exists():
            return str(venv_path)
        found = shutil.which(tool_name)
        if found is not None:
            return found
        return str(venv_path)

    def launch_command(self, args, cwd=None):
        if self.is_windows():
            command_line = subprocess.list2cmdline([str(arg) for arg in args])
            return subprocess.Popen(["cmd", "/c", "start", "", "cmd", "/c", command_line], cwd=cwd)
        return subprocess.Popen([str(arg) for arg in args], cwd=cwd)

    def run_script_file(self, path, cwd=None):
        path = Path(path)
        if self.is_windows():
            return subprocess.run(["cmd", "/c", str(path)], cwd=cwd)
        return subprocess.Popen(["/bin/sh", str(path)], cwd=cwd)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_platform_support.py -v`

Expected: PASS for all four tests.

- [ ] **Step 5: Commit**

```bash
git add EasyNovelAssistant/src/platform_support.py tests/test_platform_support.py
git commit -m "feat: add platform support helper"
```

## Task 3: Model Metadata Normalization

**Files:**
- Create: `EasyNovelAssistant/src/model_metadata.py`
- Test: `tests/test_model_metadata.py`
- Modify later callers in Task 4.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_model_metadata.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_model_metadata.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'model_metadata'`.

- [ ] **Step 3: Implement metadata helper**

Create `EasyNovelAssistant/src/model_metadata.py`:

```python
def display_name_from_llm_name(llm_name):
    name = llm_name
    if "/" in name:
        _, name = name.rsplit("/", 1)
    if " " in name:
        name = name.split(" ")[-1]
    return name


def info_url_from_model_url(url):
    marker = "/resolve/main/"
    if marker in url:
        return url.split(marker, 1)[0]
    return url.rsplit("/", 1)[0]


def normalize_llm_entry(llm_name, llm):
    urls = llm.get("urls", [])
    if not urls:
        raise ValueError(f"{llm_name} has no urls")

    llm["name"] = display_name_from_llm_name(llm_name)
    llm["file_names"] = [url.split("/")[-1] for url in urls]
    llm["file_name"] = llm["file_names"][0]
    llm["info_url"] = info_url_from_model_url(urls[0])
    llm.setdefault("launch_args", [])
    llm.setdefault("generate_args", {})
    llm.setdefault("default_params", {})
    llm.setdefault("instruct_sequence", None)
    llm.setdefault("stop_sequence", None)
    llm.setdefault("notes", "")
    return llm


def normalize_llm_map(llms):
    for llm_name, llm in llms.items():
        normalize_llm_entry(llm_name, llm)
    return llms
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_model_metadata.py -v`

Expected: PASS for both tests.

- [ ] **Step 5: Commit**

```bash
git add EasyNovelAssistant/src/model_metadata.py tests/test_model_metadata.py
git commit -m "feat: normalize model metadata"
```

## Task 4: KoboldCpp Command and Payload Construction

**Files:**
- Modify: `EasyNovelAssistant/src/path.py`
- Modify: `EasyNovelAssistant/src/kobold_cpp.py`
- Test: `tests/test_kobold_cpp.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_kobold_cpp.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_kobold_cpp.py -v`

Expected: FAIL because `KoboldCpp.__init__` does not accept `platform_support`, and `build_launch_args` / `build_generate_payload` do not exist.

- [ ] **Step 3: Update `path.py`**

Replace the KoboldCpp and tool path section in `EasyNovelAssistant/src/path.py` with:

```python
    kobold_cpp = os.path.join(cwd, "KoboldCpp")
    kobold_cpp_win = os.path.join(kobold_cpp, "koboldcpp.exe")
    kobold_cpp_linux = os.path.join(kobold_cpp, "koboldcpp-linux-x64")
    kobold_cpp_mac_arm64 = os.path.join(kobold_cpp, "koboldcpp-mac-arm64")

    style_bert_vits2 = os.path.join(cwd, "Style-Bert-VITS2")
```

Replace the venv scripts section with:

```python
    venv = os.path.join(cwd, "venv")
    scripts = os.path.join(venv, "Scripts")
    bin = os.path.join(venv, "bin")
    ffmpeg = os.path.join(scripts, "ffmpeg.exe")
    ffplay = os.path.join(scripts, "ffplay.exe")
```

- [ ] **Step 4: Update `kobold_cpp.py` imports and constructor**

Replace imports at the top of `EasyNovelAssistant/src/kobold_cpp.py` with:

```python
import json
import os
import shlex
import subprocess
import webbrowser

import requests
from model_metadata import normalize_llm_map
from path import Path
from platform_support import PlatformSupport
```

Change `BAT_TEMPLATE` to a raw string:

```python
    BAT_TEMPLATE = r"""@echo off
chcp 65001 > NUL
pushd %~dp0
set CURL_CMD=C:\Windows\System32\curl.exe -k

@REM 7B: 33, 35B: 41, 70B: 65
set GPU_LAYERS=0

@REM 2048, 4096, 8192, 16384, 32768, 65536, 131072
set CONTEXT_SIZE={context_size}

{curl_cmd}
koboldcpp.exe --gpulayers %GPU_LAYERS% {option} --contextsize %CONTEXT_SIZE% {launch_args} {file_name}
if %errorlevel% neq 0 ( pause & popd & exit /b 1 )
popd
"""
```

Change constructor signature and metadata normalization:

```python
    def __init__(self, ctx, platform_support=None):
        self.ctx = ctx
        self.platform = platform_support or PlatformSupport()
        self.base_url = f'http://{ctx["koboldcpp_host"]}:{ctx["koboldcpp_port"]}'
        self.model_url = f"{self.base_url}/api/v1/model"
        self.generate_url = f"{self.base_url}/api/v1/generate"
        self.check_url = f"{self.base_url}/api/extra/generate/check"
        self.abort_url = f"{self.base_url}/api/extra/abort"

        self.model_name = None
        normalize_llm_map(ctx.llm)

        for llm_name, llm in ctx.llm.items():
            context_size = min(llm["context_size"], ctx["llm_context_size"])
            bat_file = os.path.join(Path.kobold_cpp, f'Run-{llm["name"]}-C{context_size // 1024}K-L0.bat')

            curl_cmd = ""
            for url in llm["urls"]:
                curl_cmd += self.CURL_TEMPLATE.format(url=url, file_name=url.split("/")[-1], info_url=llm["info_url"])
            bat_text = self.BAT_TEMPLATE.format(
                curl_cmd=curl_cmd,
                option=ctx["koboldcpp_arg"],
                launch_args=" ".join(llm.get("launch_args", [])),
                context_size=context_size,
                file_name=llm["file_name"],
            )
            os.makedirs(Path.kobold_cpp, exist_ok=True)
            with open(bat_file, "w", encoding="utf-8") as f:
                f.write(bat_text)
```

- [ ] **Step 5: Add command and payload builders to `kobold_cpp.py`**

Add these methods before `launch_server`:

```python
    def get_kobold_cpp_executable(self):
        return str(self.platform.kobold_cpp_path(Path.kobold_cpp))

    def build_launch_args(self, llm_name, gpu_layer):
        llm = self.ctx.llm[llm_name]
        llm_path = os.path.join(Path.kobold_cpp, llm["file_name"])
        context_size = min(llm["context_size"], self.ctx["llm_context_size"])
        args = [self.get_kobold_cpp_executable()]
        args.extend(shlex.split(self.ctx["koboldcpp_arg"]))
        args.extend(["--gpulayers", str(gpu_layer), "--contextsize", str(context_size)])
        args.extend(llm.get("launch_args", []))
        args.append(llm_path)
        return args

    def build_generate_payload(self, text):
        ctx = self.ctx
        if self.ctx["llm_name"] not in self.ctx.llm:
            self.ctx["llm_name"] = "[元祖] LightChatAssistant-TypeB-2x7B-IQ4_XS"
            self.ctx["llm_gpu_layer"] = 0

        llm_name = ctx["llm_name"]
        llm = ctx.llm[llm_name]
        max_context_length = min(llm["context_size"], ctx["llm_context_size"])
        if ctx["max_length"] >= max_context_length:
            print(
                f'生成文の長さ ({ctx["max_length"]}) がコンテキストサイズ上限 ({max_context_length}) 以上なため、{max_context_length // 2} に短縮します。'
            )
            ctx["max_length"] = max_context_length // 2

        stop_sequence = llm.get("stop_sequence")
        if stop_sequence is None:
            stop_sequence = self.get_stop_sequence()

        args = {
            "max_context_length": max_context_length,
            "max_length": ctx["max_length"],
            "prompt": text,
            "quiet": False,
            "stop_sequence": stop_sequence,
            "rep_pen": ctx["rep_pen"],
            "rep_pen_range": ctx["rep_pen_range"],
            "rep_pen_slope": ctx["rep_pen_slope"],
            "temperature": ctx["temperature"],
            "tfs": ctx["tfs"],
            "top_a": ctx["top_a"],
            "top_k": ctx["top_k"],
            "top_p": ctx["top_p"],
            "typical": ctx["typical"],
            "min_p": ctx["min_p"],
            "sampler_order": ctx["sampler_order"],
        }
        args.update(llm.get("generate_args", {}))
        return args
```

- [ ] **Step 6: Replace `launch_server` and `generate` internals**

In `launch_server`, replace command construction and platform branch with:

```python
        command = self.build_launch_args(llm_name, gpu_layer)
        self.platform.launch_command(command, cwd=Path.kobold_cpp)
        return None
```

In `generate`, replace payload construction with:

```python
        args = self.build_generate_payload(text)
        print(f"KoboldCpp.generate({args})")
```

Keep the existing request/logging behavior after `args` is built.

- [ ] **Step 7: Run tests to verify they pass**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_kobold_cpp.py tests/test_model_metadata.py tests/test_platform_support.py -v`

Expected: PASS for all selected tests, and no `SyntaxWarning` from `kobold_cpp.py`.

- [ ] **Step 8: Commit**

```bash
git add EasyNovelAssistant/src/path.py EasyNovelAssistant/src/kobold_cpp.py tests/test_kobold_cpp.py
git commit -m "feat: modernize koboldcpp command handling"
```

## Task 5: Style-Bert-VITS2 Cross-Platform Launch

**Files:**
- Modify: `EasyNovelAssistant/src/style_bert_vits2.py`
- Test: `tests/test_style_bert_vits2.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_style_bert_vits2.py`:

```python
from pathlib import Path

from platform_support import PlatformInfo, PlatformSupport
from style_bert_vits2 import StyleBertVits2


class DummyContext(dict):
    def __init__(self):
        super().__init__(
            style_bert_vits2_host="localhost",
            style_bert_vits2_port=5000,
            style_bert_vits2_gpu=False,
            style_bert_vits2_command_timeout=0.05,
            max_speech_queue=3,
        )


def test_style_bert_python_path_is_unix_bin_for_linux(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    style = StyleBertVits2(DummyContext(), platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")))

    path = style.get_python_executable()

    assert path.endswith("Style-Bert-VITS2/venv/bin/python")


def test_style_bert_python_path_is_windows_scripts_for_windows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    style = StyleBertVits2(DummyContext(), platform_support=PlatformSupport(PlatformInfo("win32", "AMD64")))

    path = style.get_python_executable()

    assert path.endswith("Style-Bert-VITS2/venv/Scripts/python.exe")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_style_bert_vits2.py -v`

Expected: FAIL because `StyleBertVits2.__init__` does not accept `platform_support` and `get_python_executable` does not exist.

- [ ] **Step 3: Implement platform-aware Python path**

Update imports in `style_bert_vits2.py`:

```python
import json
import os
import subprocess
import time

import numpy as np
import requests
from job_queue import JobQueue
from path import Path
from platform_support import PlatformSupport
from scipy.io import wavfile
```

Change constructor and add helper:

```python
    def __init__(self, ctx, platform_support=None):
        self.ctx = ctx
        self.platform = platform_support or PlatformSupport()
        self.base_url = f'http://{ctx["style_bert_vits2_host"]}:{ctx["style_bert_vits2_port"]}'
        self.models_url = f"{self.base_url}/models/info"
        self.voice_url = f"{self.base_url}/voice"

        self.models = None
        self.gen_queue = JobQueue()
        self.play_queue = JobQueue()

    def get_python_executable(self):
        venv_dir = os.path.join(Path.style_bert_vits2, "venv")
        return self.platform.resolve_tool(venv_dir, "python")
```

Replace `_run_bat` with:

```python
    def _run_bat(self, command, title):
        arg = "" if self.ctx["style_bert_vits2_gpu"] else " --cpu"
        if self.platform.is_windows():
            subprocess.run(["cmd", "/c", "start", title, "cmd", "/c", f"{command}{arg} || pause"], shell=True)
        else:
            python = self.get_python_executable()
            self.platform.launch_command([python, "server_fastapi.py"] + ([] if self.ctx["style_bert_vits2_gpu"] else ["--cpu"]), cwd=Path.style_bert_vits2)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_style_bert_vits2.py -v`

Expected: PASS for both tests.

- [ ] **Step 5: Commit**

```bash
git add EasyNovelAssistant/src/style_bert_vits2.py tests/test_style_bert_vits2.py
git commit -m "fix: use platform paths for style bert launch"
```

## Task 6: Movie Maker Cross-Platform Command Files

**Files:**
- Modify: `EasyNovelAssistant/src/movie_maker.py`
- Test: `tests/test_movie_maker.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_movie_maker.py`:

```python
from pathlib import Path

from movie_maker import MovieMaker
from platform_support import PlatformInfo, PlatformSupport


class DummyContext(dict):
    def __init__(self):
        super().__init__(
            mov_image_dir="",
            mov_movie_dir="",
            mov_subtitles=True,
            mov_resize=1200,
            mov_crf=26,
            mov_volume_adjust=False,
            mov_tempo_adjust=True,
            speech_volume=50,
            speech_speed=1.0,
        )


def test_prepare_writes_shell_script_on_linux(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "movie").mkdir(exist_ok=True)
    audio = tmp_path / "001-hello.wav"
    image = tmp_path / "image.png"
    audio.write_bytes(b"")
    image.write_bytes(b"")
    maker = MovieMaker(DummyContext(), platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")))

    script_path = maker._prepare([{"audio_path": str(audio), "image_path": str(image)}], str(tmp_path / "out.mp4"))

    assert script_path.endswith(".sh")
    text = Path(script_path).read_text(encoding="utf-8")
    assert "#!/bin/sh" in text
    assert "ffmpeg" in text
    assert "start" not in text


def test_prepare_writes_bat_on_windows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    audio = tmp_path / "001-hello.wav"
    image = tmp_path / "image.png"
    audio.write_bytes(b"")
    image.write_bytes(b"")
    maker = MovieMaker(DummyContext(), platform_support=PlatformSupport(PlatformInfo("win32", "AMD64")))

    script_path = maker._prepare([{"audio_path": str(audio), "image_path": str(image)}], str(tmp_path / "out.mp4"))

    assert script_path.endswith(".bat")
    text = Path(script_path).read_text(encoding="utf-8")
    assert "@echo off" in text
    assert "%FFMPEG%" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_movie_maker.py -v`

Expected: FAIL because `MovieMaker.__init__` does not accept `platform_support` and always creates `.bat`.

- [ ] **Step 3: Add platform injection and launcher**

Update imports in `movie_maker.py`:

```python
import os
import re
import subprocess
import time
from tkinter import filedialog

from path import Path
from platform_support import PlatformSupport
```

Change constructor:

```python
    def __init__(self, ctx, platform_support=None):
        self.ctx = ctx
        self.platform = platform_support or PlatformSupport()
        self.audio_dir = None
        self.image_dir = ""
```

Replace the launch section in `make`:

```python
        self.platform.run_script_file(bat_path, cwd=os.path.dirname(bat_path))
        return True
```

- [ ] **Step 4: Split `_prepare` script generation**

At the start of `_prepare`, after creating `assets_dir`, add:

```python
        if self.platform.is_windows():
            return self._prepare_windows(audio_image_sets, movie_path, assets_dir)
        return self._prepare_unix(audio_image_sets, movie_path, assets_dir)
```

Move the existing batch generation body into `_prepare_windows(self, audio_image_sets, movie_path, assets_dir)`.

Add `_prepare_unix`:

```python
    def _prepare_unix(self, audio_image_sets, movie_path, assets_dir):
        movie_name = os.path.basename(movie_path).split(".")[0]
        ffmpeg = self.platform.resolve_tool(Path.venv, "ffmpeg")
        ffplay = self.platform.resolve_tool(Path.venv, "ffplay")
        lines = ["#!/bin/sh", "set -eu", ""]
        subtitle_template = "1\n00:00:00,000 --> 90:00:00,000\n{serif}\n"
        part_paths = []
        for i, audio_image_set in enumerate(audio_image_sets):
            audio_path = audio_image_set["audio_path"]
            image_path = audio_image_set["image_path"]
            audio_name, _ext = os.path.splitext(os.path.basename(audio_path))
            serif = audio_name
            m = self._SERIF_REGEX.match(audio_name)
            if m is not None:
                serif = m.group(1)
            subtitle_path = os.path.join(assets_dir, f"{audio_name}.srt")
            with open(subtitle_path, "w", encoding="utf-8-sig") as f:
                f.write(subtitle_template.format(serif=serif))

            part_path = os.path.join(assets_dir, f"{audio_name}.mp4")
            part_paths.append(part_path)
            vf = []
            if self.ctx["mov_resize"] > 0:
                vf.append(f"scale='if(gt(a,1),{self.ctx['mov_resize']},-2)':'if(gt(a,1),-2,{self.ctx['mov_resize']})'")
            if self.ctx["mov_subtitles"]:
                vf.append(f"subtitles='{os.path.basename(subtitle_path)}'")
            af = []
            if self.ctx["mov_volume_adjust"]:
                af.append(f"volume={self.ctx['speech_volume'] / 100}")
            if self.ctx["mov_tempo_adjust"]:
                af.append(f"atempo={self.ctx['speech_speed']}")

            lines.append(f'echo "{i}: {serif}"')
            cmd = [
                f'"{ffmpeg}"', "-y", "-loglevel", "error",
                "-i", f'"{audio_path}"',
                "-loop", "1", "-i", f'"{image_path}"',
                "-vcodec", "libx264",
                "-pix_fmt", "yuv420p",
                "-acodec", "aac",
                "-ab", "128k",
                "-ac", "1",
                "-ar", "44100",
                "-shortest",
            ]
            if vf:
                cmd.extend(["-vf", '"' + ", ".join(vf) + '"'])
            if af:
                cmd.extend(["-af", '"' + ", ".join(af) + '"'])
            cmd.extend(["-crf", str(self.ctx["mov_crf"]), f'"{part_path}"'])
            lines.append(" ".join(cmd))
            lines.append("")

        file_list_path = os.path.join(assets_dir, f"{movie_name}.txt")
        with open(file_list_path, "w", encoding="utf-8") as f:
            for part_path in part_paths:
                f.write(f"file '{part_path}'\n")

        lines.append(f'"{ffmpeg}" -y -loglevel error -f concat -safe 0 -i "{file_list_path}" -c copy "{movie_path}"')
        lines.append(f'"{ffplay}" -loglevel error -autoexit -loop 3 "{movie_path}"')
        script_path = os.path.join(assets_dir, f"{movie_name}.sh")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        os.chmod(script_path, 0o755)
        return script_path
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_movie_maker.py -v`

Expected: PASS for both tests.

- [ ] **Step 6: Commit**

```bash
git add EasyNovelAssistant/src/movie_maker.py tests/test_movie_maker.py
git commit -m "fix: generate movie scripts per platform"
```

## Task 7: Tool Menu Cross-Platform Launch

**Files:**
- Modify: `EasyNovelAssistant/src/menu/tool_menu.py`
- Extend: `tests/test_platform_support.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_platform_support.py`:

```python
def test_resolve_tool_falls_back_to_venv_path(tmp_path):
    support = PlatformSupport(PlatformInfo("linux", "x86_64"))

    resolved = support.resolve_tool(tmp_path, "definitely-not-installed-easy-novel-tool")

    assert resolved.endswith("bin/definitely-not-installed-easy-novel-tool")
```

- [ ] **Step 2: Run test to verify it fails or confirms current helper behavior**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_platform_support.py::test_resolve_tool_falls_back_to_venv_path -v`

Expected: PASS if Task 2 helper already covers fallback. If it fails because `shutil.which` returns an unexpected path, change the tool name to `easy-novel-assistant-unavailable-tool`.

- [ ] **Step 3: Update `tool_menu.py`**

Update imports:

```python
import os
import subprocess
import tkinter as tk
import webbrowser

from path import Path
from platform_support import PlatformSupport
```

Add platform support in constructor:

```python
        self.platform = PlatformSupport()
```

Replace `_run_kobold_cpp`:

```python
    def _run_kobold_cpp(self, *args):
        executable = self.platform.kobold_cpp_path(Path.kobold_cpp)
        self.platform.launch_command([executable], cwd=Path.kobold_cpp)
```

Replace `_run_style_bert_vits2`:

```python
    def _run_style_bert_vits2(self, bat, py):
        if self.platform.is_windows():
            subprocess.run(["cmd", "/c", "start", "cmd", "/c", f"{bat} || pause"], cwd=Path.style_bert_vits2, shell=True)
        else:
            python = self.platform.resolve_tool(os.path.join(Path.style_bert_vits2, "venv"), "python")
            self.platform.launch_command([python] + py.split(), cwd=Path.style_bert_vits2)
```

- [ ] **Step 4: Run targeted tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_platform_support.py -v`

Expected: PASS for all platform helper tests.

- [ ] **Step 5: Commit**

```bash
git add EasyNovelAssistant/src/menu/tool_menu.py tests/test_platform_support.py
git commit -m "fix: use platform launcher in tool menu"
```

## Task 8: Dependencies and Setup Scripts

**Files:**
- Modify: `EasyNovelAssistant/setup/res/requirements.txt`
- Modify: `EasyNovelAssistant/setup/Setup-EasyNovelAssistant.sh`
- Modify: `Run-EasyNovelAssistant.sh`
- Modify: `README.md`

- [ ] **Step 1: Verify current package compatibility**

Run:

```bash
python3 -m pip index versions requests
python3 -m pip index versions tkinterdnd2
python3 -m pip index versions scipy
python3 -m pip index versions watchdog
python3 -m pip index versions pytest
```

Expected: Latest stable versions include `requests 2.33.1`, `tkinterdnd2 0.4.3`, `scipy 1.17.1`, `watchdog 6.0.0`, and `pytest 9.0.3`, or the command output shows a newer stable patch version that must be used consistently in this task.

- [ ] **Step 2: Update runtime requirements**

Replace `EasyNovelAssistant/setup/res/requirements.txt` with:

```text
requests==2.33.1
tkinterdnd2==0.4.3
scipy==1.17.1
watchdog==6.0.0
```

If Step 1 showed a newer stable patch version, use that version and write it exactly in this file.

- [ ] **Step 3: Update Unix setup script**

Replace `EasyNovelAssistant/setup/Setup-EasyNovelAssistant.sh` with:

```bash
#!/bin/sh
set -eu

if ! command -v uv >/dev/null 2>&1; then
    echo "uv command was not found."
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR/../.."
uv run ./EasyNovelAssistant/setup/setup_easy_novel_assistant.py
```

- [ ] **Step 4: Update Unix launcher sample downloads**

Replace `Run-EasyNovelAssistant.sh` with:

```bash
#!/bin/sh
set -eu

if ! command -v uv >/dev/null 2>&1; then
    echo "uv command was not found."
    echo "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"
uv run ./EasyNovelAssistant/setup/run_easy_novel_assistant.py
```

- [ ] **Step 5: Add README platform note**

In `README.md`, under "インストールと更新", add:

```markdown
### 対応環境

- Python 3.10 以上
- uv
- Windows 10/11: `EasyNovelAssistant/setup/Setup-EasyNovelAssistant.bat`
- Linux x64: `uv run EasyNovelAssistant/setup/setup_easy_novel_assistant.py`
- macOS Apple Silicon: `uv run EasyNovelAssistant/setup/setup_easy_novel_assistant.py`

KoboldCpp は起動 OS に応じて `koboldcpp.exe`、`koboldcpp-linux-x64`、`koboldcpp-mac-arm64` を利用します。macOS Intel は KoboldCpp のバイナリを手動で用意してください。
```

- [ ] **Step 6: Verify scripts parse**

Run:

```bash
sh -n EasyNovelAssistant/setup/Setup-EasyNovelAssistant.sh
sh -n Run-EasyNovelAssistant.sh
python3 -m py_compile EasyNovelAssistant/setup/setup_easy_novel_assistant.py
python3 -m py_compile EasyNovelAssistant/setup/run_easy_novel_assistant.py
```

Expected: both commands exit 0.

- [ ] **Step 7: Commit**

```bash
git add EasyNovelAssistant/setup/res/requirements.txt requirements-dev.txt EasyNovelAssistant/setup/Setup-EasyNovelAssistant.sh Run-EasyNovelAssistant.sh README.md
git commit -m "chore: update dependencies and unix setup"
```

## Task 9: Curated Modern Model Metadata

**Files:**
- Modify: `EasyNovelAssistant/setup/res/default_llm.json`
- Modify: `EasyNovelAssistant/setup/res/default_llm_sequence.json`
- Test: `tests/test_config_files.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_config_files.py`:

```python
def test_modern_model_entries_have_optional_metadata():
    llms = load_json(ROOT / "EasyNovelAssistant" / "setup" / "res" / "default_llm.json")

    modern_entries = [
        name for name, value in llms.items()
        if value.get("launch_args") or value.get("generate_args") or value.get("stop_sequence")
    ]

    assert modern_entries
    for name in modern_entries:
        value = llms[name]
        assert isinstance(value.get("urls"), list)
        assert value["urls"]
        assert isinstance(value.get("context_size"), int)
        assert isinstance(value.get("max_gpu_layer"), int)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_config_files.py::test_modern_model_entries_have_optional_metadata -v`

Expected: FAIL because current `default_llm.json` has no modern optional metadata entries.

- [ ] **Step 3: Add curated entries**

Edit `EasyNovelAssistant/setup/res/default_llm.json` with a JSON-aware editor. Add entries using this exact shape, replacing the `urls` values only after checking the Hugging Face files exist:

```json
"最新・汎用/Gemma-3-12B-it-Q4_K_M": {
    "urls": [
        "https://huggingface.co/unsloth/gemma-3-12b-it-GGUF/resolve/main/gemma-3-12b-it-Q4_K_M.gguf"
    ],
    "context_size": 131072,
    "max_gpu_layer": 99,
    "launch_args": [
        "--jinja"
    ],
    "generate_args": {},
    "notes": "KoboldCpp の Jinja/chat template 対応を利用します。"
},
"最新・日本語/Qwen3-14B-Q4_K_M": {
    "urls": [
        "https://huggingface.co/unsloth/Qwen3-14B-GGUF/resolve/main/Qwen3-14B-Q4_K_M.gguf"
    ],
    "context_size": 131072,
    "max_gpu_layer": 99,
    "launch_args": [
        "--jinja"
    ],
    "generate_args": {
        "reasoning_effort": "low"
    },
    "stop_sequence": [
        "<|im_end|>"
    ],
    "notes": "Thinking 系モデル向け。reasoning_effort は KoboldCpp 側が対応する場合に渡されます。"
}
```

Keep the file valid JSON with BOM-compatible UTF-8.

- [ ] **Step 4: Add sequence fallback for modern chat template models**

In `EasyNovelAssistant/setup/res/default_llm_sequence.json`, add:

```json
"ChatTemplate": {
    "model_names": [
        "Gemma-3",
        "Qwen3"
    ],
    "instruct": "{0}",
    "stop": [
        "<|im_end|>"
    ]
}
```

- [ ] **Step 5: Verify JSON and tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_config_files.py tests/test_model_metadata.py -v
python3 -c "import json; [json.load(open(p, encoding='utf-8-sig')) for p in ['EasyNovelAssistant/setup/res/default_config.json','EasyNovelAssistant/setup/res/default_llm.json','EasyNovelAssistant/setup/res/default_llm_sequence.json']]"
```

Expected: pytest passes and JSON load command exits 0.

- [ ] **Step 6: Commit**

```bash
git add EasyNovelAssistant/setup/res/default_llm.json EasyNovelAssistant/setup/res/default_llm_sequence.json tests/test_config_files.py
git commit -m "feat: add modern model metadata"
```

## Task 10: Full Verification and Cleanup

**Files:**
- All changed files.

- [ ] **Step 1: Run full automated test suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -v
```

Expected: all tests pass.

- [ ] **Step 2: Run compile check**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile EasyNovelAssistant/src/*.py EasyNovelAssistant/src/menu/*.py
```

Expected: exit 0 and no `SyntaxWarning`.

- [ ] **Step 3: Run JSON validation**

Run:

```bash
python3 -c "import json; [json.load(open(p, encoding='utf-8-sig')) for p in ['EasyNovelAssistant/setup/res/default_config.json','EasyNovelAssistant/setup/res/default_llm.json','EasyNovelAssistant/setup/res/default_llm_sequence.json']]; print('json ok')"
```

Expected: output `json ok`.

- [ ] **Step 4: Run shell syntax validation**

Run:

```bash
sh -n EasyNovelAssistant/setup/Setup-EasyNovelAssistant.sh
sh -n Run-EasyNovelAssistant.sh
python3 -m py_compile EasyNovelAssistant/setup/setup_easy_novel_assistant.py
python3 -m py_compile EasyNovelAssistant/setup/run_easy_novel_assistant.py
```

Expected: both commands exit 0.

- [ ] **Step 5: Check worktree and generated files**

Run:

```bash
git status --short --branch --untracked-files=all
find EasyNovelAssistant/src -name __pycache__ -o -name '*.pyc'
```

Expected: only intentional tracked changes before final commit; no `__pycache__` or `.pyc` output.

- [ ] **Step 6: Commit final cleanup if needed**

If Step 5 shows tracked cleanup changes not yet committed, run:

```bash
git add .
git commit -m "test: verify modernization changes"
```

If there are no uncommitted changes, do not create an empty commit.

## Self-Review Checklist

- Spec coverage:
  - Dependency updates: Task 8.
  - Windows/macOS/Linux platform behavior: Tasks 2, 4, 5, 6, 7, 8.
  - Known defects: Tasks 4, 5, 6, 1.
  - Tests: Tasks 1 through 10.
  - Modern model metadata: Tasks 3, 4, 9.
- Deferred-wording scan:
  - No deferred wording is used as an instruction.
  - Steps contain exact files, commands, and expected outcomes.
- Type consistency:
  - `PlatformInfo`, `PlatformSupport`, `normalize_llm_entry`, `normalize_llm_map`, `build_launch_args`, and `build_generate_payload` are introduced before use by later tasks.
