import sys
import types
from pathlib import Path

sys.modules.setdefault("tkinter", types.SimpleNamespace(filedialog=types.SimpleNamespace()))

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
