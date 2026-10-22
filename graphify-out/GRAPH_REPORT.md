# Graph Report - EasyNovelAssistant  (2026-10-23)

## Corpus Check
- 7 semantic source files; AST status: extracted. Exclusions and reuse evidence: build-audit.json.

## Summary
- 555 nodes · 1287 edges · 22 communities (17 shown, 5 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 232 edges (avg confidence: 0.92)
- Token usage: per-project usage unavailable (native Codex semantic extraction).

## Graph Freshness
- Built from commit: `74ffeae1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Path
- form.py
- PlatformSupport
- StyleBertVits2
- test_app_logger.py
- huggingface_models.py
- test_uv_scripts.py
- setup_easy_novel_assistant.py
- InputArea
- MovieMaker
- log_error
- InputTab
- FileMenu
- GenMenu
- normalize_llm_entry
- EasyNovelAssistant modernization implementation plan
- EasyNovelAssistant modernization design
- EasyNovelAssistant fork overview
- Style-Bert-VITS2 configuration
- requests tkinterdnd2 scipy watchdog
- pytest 9.0.3
- MIT License 2024 Zuntan

## God Nodes (most connected - your core abstractions)
1. `PlatformSupport` - 67 edges
2. `PlatformInfo` - 44 edges
3. `KoboldCpp` - 39 edges
4. `StyleBertVits2` - 26 edges
5. `InputArea` - 24 edges
6. `MovieMaker` - 23 edges
7. `FileMenu` - 21 edges
8. `Form` - 20 edges
9. `DummyContext` - 20 edges
10. `InputTab` - 18 edges

## Surprising Connections (you probably didn't know these)
- `test_init_accepts_platform_support()` --uses--> `ToolMenu`  [INFERRED]
  tests/test_tool_menu.py → EasyNovelAssistant/src/menu/tool_menu.py
- `test_path_points_ffplay_at_downloaded_ffmpeg_bundle()` --uses--> `Path`  [INFERRED]
  tests/test_uv_scripts.py → EasyNovelAssistant/src/path.py
- `test_setup_python_script_runs_speech_setup_during_initial_setup()` --calls--> `Path`  [INFERRED]
  tests/test_uv_scripts.py → EasyNovelAssistant/src/path.py
- `test_build_custom_llm_name_does_not_add_extra_category_slashes()` --calls--> `build_custom_llm_name()`  [INFERRED]
  tests/test_huggingface_models.py → EasyNovelAssistant/src/huggingface_models.py
- `test_speech_menu_only_exposes_global_enable_toggle()` --uses--> `SpeechMenu`  [INFERRED]
  tests/test_speech_menu.py → EasyNovelAssistant/src/menu/speech_menu.py

## Import Cycles
- None detected.

## Communities (22 total, 5 thin omitted)

### Community 0 - "Path"
Cohesion: 0.08
Nodes (25): main(), run_script(), build_sample_url(), download_file(), ensure_sample(), ensure_samples(), launch_app(), main() (+17 more)

### Community 1 - "form.py"
Cohesion: 0.06
Nodes (8): Const, Form, GenArea, HelpMenu, SettingMenu, SpeechMenu, ToolMenu, OutputArea

### Community 2 - "PlatformSupport"
Cohesion: 0.09
Nodes (37): KoboldCpp, PlatformInfo, PlatformSupport, DummyContext, test_build_generate_payload_merges_model_generate_args(), test_build_launch_args_preserves_windows_paths_in_user_koboldcpp_arg(), test_build_launch_args_shlex_splits_user_koboldcpp_arg(), test_build_launch_args_uses_platform_binary_and_model_launch_args() (+29 more)

### Community 3 - "StyleBertVits2"
Cohesion: 0.06
Nodes (16): configure(), Context, EasyNovelAssistant, Generator, Job, JobQueue, StyleBertVits2, DummyContext (+8 more)

### Community 4 - "test_app_logger.py"
Cohesion: 0.07
Nodes (17): read_jsonl(), test_app_logger_formats_traceback_from_passed_exception(), test_app_logger_preserves_reserved_schema_fields(), test_app_logger_records_exception_traceback(), test_app_logger_writes_jsonl_without_bom(), test_app_logger_writes_separate_structured_logs(), FakeBooleanVar, FakeContext (+9 more)

### Community 5 - "huggingface_models.py"
Cohesion: 0.08
Nodes (23): build_gguf_llm_entry(), build_hf_resolve_url(), fetch_hf_model_payload(), gguf_siblings_from_api_payload(), HfGgufReference, parse_hf_gguf_reference(), parse_hf_gguf_url(), resolve_gguf_file_hint() (+15 more)

### Community 6 - "test_uv_scripts.py"
Cohesion: 0.07
Nodes (16): make_style_dir(), test_build_command_filters_only_when_macos_arm64_flag_is_set(), test_runtime_requirements_exclude_faster_whisper_for_macos_arm64(), test_runtime_requirements_keep_faster_whisper_by_default(), test_runtime_requirements_missing_source_has_clear_error(), read_text(), test_app_scripts_do_not_create_or_activate_virtualenvs(), test_ena_python_script_has_pep723_metadata() (+8 more)

### Community 7 - "setup_easy_novel_assistant.py"
Cohesion: 0.16
Nodes (22): download_file(), download_first_available(), ensure_app_dependencies(), ensure_default_model(), ensure_kobold_cpp(), ensure_speech_engine(), ensure_style_bert_assets(), ensure_style_bert_model() (+14 more)

### Community 8 - "InputArea"
Cohesion: 0.11
Nodes (4): InputArea, close_others(), close_right(), copy_tab()

### Community 9 - "MovieMaker"
Cohesion: 0.18
Nodes (10): MovieMaker, DummyContext, read_generated_commands(), test_make_runs_generated_script_with_script_directory(), test_prepare_escapes_subtitle_path_for_ffmpeg_filtergraph(), test_prepare_filter_chains_are_single_subprocess_arguments(), test_prepare_python_script_preserves_paths_and_concat_file(), test_prepare_python_script_uses_argument_lists_for_space_paths() (+2 more)

### Community 10 - "log_error"
Cohesion: 0.16
Nodes (11): _add_details(), _base_record(), _enabled(), log_error(), log_exception(), log_generated(), log_info(), log_operation() (+3 more)

### Community 11 - "InputTab"
Cohesion: 0.15
Nodes (5): FileWatcher, InputTab, edit_clear(), edit_redo(), edit_undo()

### Community 14 - "normalize_llm_entry"
Cohesion: 0.33
Nodes (7): display_name_from_llm_name(), info_url_from_model_url(), normalize_llm_entry(), normalize_llm_map(), test_normalize_llm_entry_derives_name_files_and_info_url(), test_normalize_llm_entry_preserves_explicit_info_url(), test_normalize_llm_map_keeps_optional_modern_fields()

### Community 15 - "EasyNovelAssistant modernization implementation plan"
Cohesion: 0.33
Nodes (6): PlatformSupport owns executable and venv paths, Model metadata normalization and optional launch/generate fields, KoboldCpp payload and process argument builders, Style-Bert-VITS2 movie and tool launch migration, Dependency configuration and platform verification tests, EasyNovelAssistant modernization implementation plan

### Community 16 - "EasyNovelAssistant modernization design"
Cohesion: 0.40
Nodes (5): Tkinter retained with focused platform helper, GGUF curated models and chat-template passthrough, Existing config compatibility, Manual Windows Linux macOS runtime verification limits, EasyNovelAssistant modernization design

### Community 17 - "EasyNovelAssistant fork overview"
Cohesion: 0.40
Nodes (5): Windows Linux x64 macOS Apple Silicon, KoboldCppとStyle-Bert-VITS2, GGUF Hugging Faceモデル追加, PEP723 uv setup/run とJSONLログ, EasyNovelAssistant fork overview

### Community 18 - "Style-Bert-VITS2 configuration"
Cohesion: 0.67
Nodes (3): CUDA resampling BERT style generation and training, Japanese FastAPI server, Style-Bert-VITS2 configuration

## Knowledge Gaps
- **20 isolated node(s):** `PlatformSupport owns executable and venv paths`, `Model metadata normalization and optional launch/generate fields`, `KoboldCpp payload and process argument builders`, `Style-Bert-VITS2 movie and tool launch migration`, `Dependency configuration and platform verification tests` (+15 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 135 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Path` connect `Path` to `form.py`, `PlatformSupport`, `StyleBertVits2`, `huggingface_models.py`, `test_uv_scripts.py`, `setup_easy_novel_assistant.py`, `MovieMaker`, `log_error`, `FileMenu`?**
  _High betweenness centrality (0.228) - this node is a cross-community bridge._
- **Are the 46 inferred relationships involving `PlatformSupport` (e.g. with `KoboldCpp` and `ToolMenu`) actually correct?**
  _`PlatformSupport` has 46 INFERRED edges - model-reasoned connections that need verification._
- **What connects `PlatformSupport owns executable and venv paths`, `Model metadata normalization and optional launch/generate fields`, `KoboldCpp payload and process argument builders` to the rest of the system?**
  _20 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Path` be split into smaller, more focused modules?**
  _Cohesion score 0.0818452380952381 - nodes in this community are weakly interconnected._
- **Why does `PlatformSupport` connect `PlatformSupport` to `Path`, `form.py`, `StyleBertVits2`, `MovieMaker`, `normalize_llm_entry`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `Path` (e.g. with `download_file()` and `ensure_samples()`) actually correct?**
  _`Path` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Should `form.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05654761904761905 - nodes in this community are weakly interconnected._