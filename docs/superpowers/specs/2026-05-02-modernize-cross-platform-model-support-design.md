# EasyNovelAssistant Modernization, Cross-Platform, and Model Support Design

Date: 2026-05-02

## Context

EasyNovelAssistant is a Tkinter desktop application for local novel generation. It coordinates:

- Tkinter UI and prompt tabs in `EasyNovelAssistant/src/form.py` and `input_area.py`.
- Generation orchestration in `generator.py`.
- KoboldCpp model server launch and API calls in `kobold_cpp.py`.
- Style-Bert-VITS2 speech generation in `style_bert_vits2.py`.
- Setup and launch scripts for Windows and Unix-like systems.

The current code and scripts are primarily Windows-oriented, with partial Linux support. The Linux path is pinned to the older `koboldcpp-linux-x64-cuda1150` binary name. macOS is not handled explicitly. Python dependencies are pinned to older versions from the 2024 timeframe.

Current upstream checks found:

- KoboldCpp latest release page redirects to `v1.112.2` and documents Windows `koboldcpp.exe`, Linux `koboldcpp-linux-x64`, and macOS Apple Silicon `koboldcpp-mac-arm64`.
- Style-Bert-VITS2 latest release page redirects to `2.7.0`.
- Current PyPI versions observed: `requests 2.33.1`, `tkinterdnd2 0.4.3`, `scipy 1.17.1`, and `watchdog 6.0.0`.

## Goals

1. Update stale dependencies and external tool references where the newer versions are compatible with the application.
2. Make the app and setup/launch flow explicit for Windows, macOS, and Linux.
3. Fix reproducible defects found during modernization.
4. Add automated tests and rerun the full available test suite.
5. Support newer GGUF models both through flexible custom model definitions and curated Japanese/novel-oriented presets.

## Non-Goals

- Do not replace Tkinter with another UI framework.
- Do not bundle large model binaries or KoboldCpp binaries in the repository.
- Do not guarantee real GPU execution on every OS from this workspace; cross-platform runtime checks will be represented by automated unit tests and documented manual verification steps.
- Do not fully reimplement KoboldCpp chat templating. EasyNovelAssistant should pass through model-specific settings and use KoboldCpp's current capabilities where possible.

## Approach

Use a staged compatibility modernization rather than a broad rewrite.

This keeps existing user configuration files and local workflows recognizable while adding platform detection, safer subprocess handling, test coverage, and flexible model metadata.

## Architecture Changes

### Platform Abstraction

Introduce a small platform helper module responsible for:

- Detecting `windows`, `macos`, or `linux`.
- Selecting the expected KoboldCpp executable name:
  - Windows: `koboldcpp.exe`
  - Linux: `koboldcpp-linux-x64`
  - macOS Apple Silicon: `koboldcpp-mac-arm64`
  - macOS Intel: no bundled upstream binary assumption; show a clear error unless the user configures a custom path.
- Building subprocess argument lists without shell string interpolation where practical.
- Finding `python`, `ffmpeg`, and `ffplay` in the active venv or system PATH.

`path.py`, `kobold_cpp.py`, `tool_menu.py`, `style_bert_vits2.py`, and `movie_maker.py` should consume this helper instead of branching directly on `sys.platform`.

### Setup and Launch Scripts

Retain `.bat` files for Windows and `.sh` files for macOS/Linux, but align behavior:

- Use `python3` fallback on macOS/Linux when `python` is unavailable.
- Download the current KoboldCpp binary name for the detected OS.
- Avoid hard-coded Linux CUDA 11.5 binary names.
- Add macOS handling for Apple Silicon.
- Keep Windows CUDA 12 update script, but document that Linux/macOS users should use the platform setup script or replace the binary manually.
- Make sample downloads consistent between Windows and Unix launch scripts, including `GoalSeek` files if launch-time download remains the intended behavior.

### Dependency Updates

Update `EasyNovelAssistant/setup/res/requirements.txt` conservatively:

- `requests` to the latest compatible stable version.
- `tkinterdnd2` to the latest compatible stable version.
- `scipy` to the latest compatible stable version only if Python version support and wheel availability are acceptable.
- `watchdog` to the latest compatible stable version.

Add a README note with the supported Python range. If a dependency requires Python 3.10+, make Python 3.10 the minimum supported version.

### KoboldCpp Model Support

Extend model metadata in `default_llm.json` while remaining backward compatible. Existing entries should still work. New optional fields:

- `launch_args`: extra KoboldCpp launch flags for a model.
- `generate_args`: extra request payload fields for `/api/v1/generate`.
- `default_params`: optional KoboldCpp default generation params passed at launch when appropriate.
- `instruct_sequence`: optional inline prompt wrapper override.
- `stop_sequence`: optional inline stop sequence override.
- `notes`: short human-facing compatibility notes.

The application should merge these optional fields into generated launch commands and generation payloads without requiring every model entry to define them.

For modern models where KoboldCpp recommends Jinja/chat-template support, presets can add launch args such as `--jinja` or related template flags. Thinking models can pass supported fields such as `reasoning_effort` through `generate_args` when configured.

### Curated Model Refresh

Refresh the curated Japanese/novel-oriented presets in `default_llm.json` after checking current Hugging Face model pages. Add only entries that have stable GGUF download URLs and clear prompt format expectations.

Keep the current model list unless a URL is clearly broken or superseded in a way that makes the old entry misleading.

### Defect Fixes

Known defects or likely defects to address:

- Python `SyntaxWarning` in `kobold_cpp.py` caused by Windows backslashes inside a normal triple-quoted string.
- Unix/macOS Style-Bert-VITS2 launcher currently looks under `venv/Scripts/python`, which is Windows-specific.
- Linux KoboldCpp binary path is pinned to an old CUDA 11.5 binary name.
- `movie_maker.py` uses Windows `start` unconditionally, so video creation cannot work on macOS/Linux.
- Subprocess calls use shell interpolation in several paths; where possible they should use argument lists to reduce quoting problems with spaces and non-ASCII paths.
- `__pycache__` files are not ignored, so test and compile runs dirty the worktree.

Each behavior-changing defect fix should have a regression test where feasible.

## Testing Strategy

Add `pytest` tests under `tests/`.

Initial coverage:

- JSON config files load with `utf-8-sig`.
- Existing and new model definitions normalize file names and info URLs correctly.
- Platform helper returns the expected KoboldCpp binary name for Windows, Linux, macOS arm64, and unsupported macOS Intel.
- KoboldCpp launch command construction includes platform-specific executable and model-specific launch args.
- KoboldCpp generate payload merges common sampler settings with model-specific `generate_args`.
- Style-Bert-VITS2 Python path selection uses `venv/bin/python` on macOS/Linux and `venv/Scripts/python.exe` on Windows.
- Movie maker command construction avoids Windows-only `start` on macOS/Linux.

Verification commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile EasyNovelAssistant/src/*.py EasyNovelAssistant/src/menu/*.py
python3 -m pytest
python3 -c "import json; [json.load(open(p, encoding='utf-8-sig')) for p in ['EasyNovelAssistant/setup/res/default_config.json','EasyNovelAssistant/setup/res/default_llm.json','EasyNovelAssistant/setup/res/default_llm_sequence.json']]"
```

Manual verification matrix:

- Windows: setup, launch, model download, KoboldCpp start, generation, speech launch, video creation.
- macOS Apple Silicon: setup, launch, KoboldCpp binary download/start, generation against local server.
- Linux x64: setup, launch, KoboldCpp binary download/start, generation against local server.

## Compatibility and Migration

Existing `config.json`, `llm.json`, and `llm_sequence.json` should continue to work. New optional fields should be additive. If a user has a custom `llm.json`, the app should merge it as before.

If old KoboldCpp binaries exist locally, the app should either continue using a configured custom executable path or show a clear message instructing the user to run the updated setup script.

## Risks

- Latest dependency versions may drop support for older Python versions. The implementation must verify compatibility before pinning.
- KoboldCpp API payload fields can vary across releases. Unknown optional fields should be configured per model and easy to remove.
- Full OS runtime verification is limited by local machine availability. Tests should isolate command construction and config behavior, and documentation should list manual checks.

## Acceptance Criteria

- Requirements and setup scripts reference current compatible dependencies and KoboldCpp binary names.
- Windows, macOS, and Linux code paths are represented in tested platform helper behavior.
- Known cross-platform bugs listed above are fixed or documented with a clear reason if deferred.
- Existing JSON config files and model presets load successfully.
- A test suite exists and passes in the available environment.
- Curated model definitions include current Japanese/novel-oriented presets and support optional modern model launch/generation parameters.
- The worktree remains clean except for intentional tracked changes.
