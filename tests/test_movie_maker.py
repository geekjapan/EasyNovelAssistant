import ast
import os
from pathlib import Path
from unittest.mock import Mock

from movie_maker import MovieMaker
import movie_maker
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


def read_generated_commands(script_path):
    tree = ast.parse(Path(script_path).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "COMMANDS":
                    return ast.literal_eval(node.value)
    raise AssertionError("COMMANDS not found")


def test_prepare_writes_uv_python_script_on_linux(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "movie").mkdir(exist_ok=True)
    audio = tmp_path / "001-hello.wav"
    image = tmp_path / "image.png"
    audio.write_bytes(b"")
    image.write_bytes(b"")
    maker = MovieMaker(DummyContext(), platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")))

    script_path = maker._prepare([{"audio_path": str(audio), "image_path": str(image)}], str(tmp_path / "out.mp4"))

    assert script_path.endswith(".py")
    text = Path(script_path).read_text(encoding="utf-8")
    assert "# /// script" in text
    assert "ffmpeg" in text
    assert "start" not in text


def test_prepare_writes_uv_python_script_on_windows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    audio = tmp_path / "001-hello.wav"
    image = tmp_path / "image.png"
    audio.write_bytes(b"")
    image.write_bytes(b"")
    maker = MovieMaker(DummyContext(), platform_support=PlatformSupport(PlatformInfo("win32", "AMD64")))

    script_path = maker._prepare([{"audio_path": str(audio), "image_path": str(image)}], str(tmp_path / "out.mp4"))

    assert script_path.endswith(".py")
    text = Path(script_path).read_text(encoding="utf-8")
    assert "# /// script" in text
    assert "subprocess.run" in text


def test_prepare_python_script_uses_argument_lists_for_space_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    audio = tmp_path / "001-hello.wav"
    image = tmp_path / "image.png"
    audio.write_bytes(b"")
    image.write_bytes(b"")
    ffmpeg = tmp_path / "tools with spaces" / "ffmpeg.exe"
    ffplay = tmp_path / "tools with spaces" / "ffplay.exe"
    ffmpeg.parent.mkdir()
    ffmpeg.write_text("", encoding="utf-8")
    ffplay.write_text("", encoding="utf-8")
    monkeypatch.setattr(movie_maker.Path, "ffmpeg", str(ffmpeg))
    monkeypatch.setattr(movie_maker.Path, "ffplay", str(ffplay))
    maker = MovieMaker(DummyContext(), platform_support=PlatformSupport(PlatformInfo("win32", "AMD64")))

    script_path = maker._prepare([{"audio_path": str(audio), "image_path": str(image)}], str(tmp_path / "out.mp4"))

    commands = read_generated_commands(script_path)
    assert commands[0][1][0] == str(ffmpeg)
    assert commands[-1][1][0] == str(ffplay)


def test_prepare_python_script_preserves_paths_and_concat_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    dangerous_dir = tmp_path / "space 日本 'quote $(touch pwned)"
    dangerous_dir.mkdir()
    audio = dangerous_dir / "001-hello ' $(touch pwned).wav"
    image = dangerous_dir / "image 日本 ' $(touch pwned).png"
    movie_path = dangerous_dir / "out 日本 ' $(touch pwned).mp4"
    audio.write_bytes(b"")
    image.write_bytes(b"")
    maker = MovieMaker(DummyContext(), platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")))
    ffmpeg = dangerous_dir / "ffmpeg ' $(touch pwned)"
    ffplay = dangerous_dir / "ffplay ' $(touch pwned)"
    maker.platform.resolve_tool = Mock(side_effect=[str(ffmpeg), str(ffplay)])

    script_path = maker._prepare([{"audio_path": str(audio), "image_path": str(image)}], str(movie_path))

    commands = read_generated_commands(script_path)
    assert commands[0][1][0] == str(ffmpeg)
    assert str(audio) in commands[0][1]
    assert str(image) in commands[0][1]
    assert commands[-1][1][-1] == str(movie_path)

    audio_name = audio.stem
    part_path = movie_path.parent / movie_path.stem / f"{audio_name}.mp4"
    concat_text = (movie_path.parent / movie_path.stem / f"{movie_path.stem}.txt").read_text(encoding="utf-8")
    escaped_part_path = str(part_path).replace("'", "'\\''")
    assert concat_text == f"file '{escaped_part_path}'\n"


def test_prepare_escapes_subtitle_path_for_ffmpeg_filtergraph(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    audio = tmp_path / "001-Bob's line.wav"
    image = tmp_path / "image.png"
    audio.write_bytes(b"")
    image.write_bytes(b"")
    maker = MovieMaker(DummyContext(), platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")))

    script_path = maker._prepare([{"audio_path": str(audio), "image_path": str(image)}], str(tmp_path / "out.mp4"))

    ffmpeg_args = read_generated_commands(script_path)[0][1]
    vf_arg = ffmpeg_args[ffmpeg_args.index("-vf") + 1]
    assert "subtitles='001-Bob\\'s line.srt'" in vf_arg


def test_prepare_filter_chains_are_single_subprocess_arguments(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    audio = tmp_path / "001-Bob's line.wav"
    image = tmp_path / "image.png"
    audio.write_bytes(b"")
    image.write_bytes(b"")
    maker = MovieMaker(DummyContext(), platform_support=PlatformSupport(PlatformInfo("linux", "x86_64")))

    script_path = maker._prepare([{"audio_path": str(audio), "image_path": str(image)}], str(tmp_path / "out.mp4"))

    ffmpeg_args = read_generated_commands(script_path)[0][1]
    vf_arg = ffmpeg_args[ffmpeg_args.index("-vf") + 1]
    af_arg = ffmpeg_args[ffmpeg_args.index("-af") + 1]
    assert ", " in vf_arg
    assert vf_arg.startswith("scale='if(gt(a,1),1200,-2)'")
    assert "subtitles='001-Bob\\'s line.srt'" in vf_arg
    assert af_arg == "atempo=1.0"


def test_make_runs_generated_script_with_script_directory(tmp_path):
    script_path = tmp_path / "movie assets" / "out.py"
    platform = Mock()
    platform.resolve_uv.return_value = "uv"
    maker = MovieMaker(DummyContext(), platform_support=platform)
    audio_image_sets = [{"audio_path": "audio.wav", "image_path": "image.png"}]
    maker._select_audio_image_sets = Mock(return_value=audio_image_sets)
    maker._select_movie_path = Mock(return_value=str(tmp_path / "out.mp4"))
    maker._prepare = Mock(return_value=str(script_path))

    result = maker.make()

    assert result is True
    platform.launch_command.assert_called_once_with(["uv", "run", str(script_path)], cwd=os.path.dirname(str(script_path)))
