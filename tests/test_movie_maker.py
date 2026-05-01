import os
import shlex
from pathlib import Path
from unittest.mock import Mock

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
    assert Path(script_path).stat().st_mode & 0o111
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


def test_prepare_quotes_unix_script_paths_and_concat_file(tmp_path, monkeypatch):
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

    script_text = Path(script_path).read_text(encoding="utf-8")
    assert shlex.quote(str(ffmpeg)) in script_text
    assert shlex.quote(str(ffplay)) in script_text
    assert shlex.quote(str(audio)) in script_text
    assert shlex.quote(str(image)) in script_text
    assert shlex.quote(str(movie_path)) in script_text
    assert f'"{audio}"' not in script_text
    assert f'"{image}"' not in script_text

    audio_name = audio.stem
    part_path = movie_path.parent / movie_path.stem / f"{audio_name}.mp4"
    concat_text = (movie_path.parent / movie_path.stem / f"{movie_path.stem}.txt").read_text(encoding="utf-8")
    escaped_part_path = str(part_path).replace("'", "'\\''")
    assert concat_text == f"file '{escaped_part_path}'\n"


def test_make_runs_generated_script_with_script_directory(tmp_path):
    script_path = tmp_path / "movie assets" / "out.sh"
    platform = Mock()
    maker = MovieMaker(DummyContext(), platform_support=platform)
    audio_image_sets = [{"audio_path": "audio.wav", "image_path": "image.png"}]
    maker._select_audio_image_sets = Mock(return_value=audio_image_sets)
    maker._select_movie_path = Mock(return_value=str(tmp_path / "out.mp4"))
    maker._prepare = Mock(return_value=str(script_path))

    result = maker.make()

    assert result is True
    platform.run_script_file.assert_called_once_with(str(script_path), cwd=os.path.dirname(str(script_path)))
