import os
import re
import time

from path import Path
from platform_support import PlatformSupport


class MovieMaker:
    _SERIF_REGEX = re.compile(r"^[\d_]*-(.+)")

    def __init__(self, ctx, platform_support=None):
        self.ctx = ctx
        self.platform = platform_support or PlatformSupport()
        self.audio_dir = None
        self.image_dir = ""

    def _filedialog(self):
        from tkinter import filedialog

        return filedialog

    def _concat_file_line(self, path):
        escaped = str(path).replace("'", "'\\''")
        return f"file '{escaped}'\n"

    def _ffmpeg_filter_single_quote_value(self, value):
        escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"

    def make(self):
        audio_image_sets = self._select_audio_image_sets()
        if len(audio_image_sets) == 0:
            return False

        movie_path = self._select_movie_path()
        if movie_path is None:
            return False

        script_path = self._prepare(audio_image_sets, movie_path)
        if script_path is None:
            return False

        self.platform.launch_command([self.platform.resolve_uv(), "run", script_path], cwd=os.path.dirname(script_path))
        return True

    def _select_audio_image_sets(self):
        filedialog = self._filedialog()
        win = self.ctx.form.win
        result = []

        if self.audio_dir is None:
            if os.path.exists(Path.daily_speech):
                self.audio_dir = Path.daily_speech
            elif os.path.exists(Path.speech):
                self.audio_dir = Path.speech
            else:
                self.audio_dir = Path.cwd

        image_dir = self.ctx["mov_image_dir"]
        if image_dir == "":
            image_dir = Path.cwd

        while True:
            title = "動画にする音声ファイルを選択します。"
            if len(result) > 0:
                title += " [キャンセル] で選択を終了します。"
            audio_path = filedialog.askopenfilename(
                title=title,
                filetypes=[("音声ファイル", "*.wav")],
                initialdir=self.audio_dir,
                parent=win,
            )
            if audio_path == "":
                break
            self.audio_dir = os.path.dirname(audio_path)
            audio_name = os.path.basename(audio_path).split(".")[0]

            image_path = filedialog.askopenfilename(
                title=f"{audio_name} の再生中に表示する画像ファイルを選択します。",
                filetypes=[("画像ファイル", "*.png *.webp *.jpg *.jpeg")],
                initialdir=image_dir,
                parent=win,
            )
            if image_path == "":
                break
            image_dir = os.path.dirname(image_path)
            self.ctx["mov_image_dir"] = image_dir

            result.append({"image_path": image_path, "audio_path": audio_path})

        return result

    def _select_movie_path(self):
        filedialog = self._filedialog()
        movie_dir = self.ctx["mov_movie_dir"]
        if movie_dir == "":
            movie_dir = Path.movie

        YYYYMMDD_HHMMSS = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        movie_path = filedialog.asksaveasfilename(
            title="動画ファイルを保存",
            filetypes=[("動画ファイル", "*.mp4")],
            initialdir=movie_dir,
            initialfile=f"{YYYYMMDD_HHMMSS}.mp4",
            parent=self.ctx.form.win,
        )
        if movie_path == "":
            return None
        if not movie_path.endswith(".mp4"):
            movie_path += ".mp4"
        self.ctx["mov_movie_dir"] = os.path.dirname(movie_path)
        return movie_path

    def _prepare(self, audio_image_sets, movie_path):
        movie_name = os.path.basename(movie_path).split(".")[0]
        assets_dir = os.path.join(os.path.dirname(movie_path), movie_name)
        os.makedirs(assets_dir, exist_ok=True)
        return self._prepare_python(audio_image_sets, movie_path, assets_dir)

    def _ffmpeg_tools(self):
        ffmpeg = Path.ffmpeg if os.path.exists(Path.ffmpeg) else self.platform.resolve_tool("ffmpeg")
        ffplay = Path.ffplay if os.path.exists(Path.ffplay) else self.platform.resolve_tool("ffplay")
        return ffmpeg, ffplay

    def _prepare_python(self, audio_image_sets, movie_path, assets_dir):
        movie_name = os.path.basename(movie_path).split(".")[0]
        ffmpeg, ffplay = self._ffmpeg_tools()
        subtitle_template = "1\n00:00:00,000 --> 90:00:00,000\n{serif}\n"
        part_paths = []
        commands = []
        for i, audio_image_set in enumerate(audio_image_sets):
            audio_path = audio_image_set["audio_path"]
            image_path = audio_image_set["image_path"]
            audio_name, _ext = os.path.splitext(os.path.basename(audio_path))
            serif = audio_name
            m = self._SERIF_REGEX.match(audio_name)
            if m is not None:
                serif = m.group(1)
            subtitle = subtitle_template.format(serif=serif)
            subtitle_path = os.path.join(assets_dir, f"{audio_name}.srt")
            with open(subtitle_path, "w", encoding="utf-8-sig") as f:
                f.write(subtitle)

            part_path = os.path.join(assets_dir, f"{audio_name}.mp4")
            part_paths.append(part_path)

            vf = []
            if self.ctx["mov_resize"] > 0:
                vf.append(f"scale='if(gt(a,1),{self.ctx['mov_resize']},-2)':'if(gt(a,1),-2,{self.ctx['mov_resize']})'")
            if self.ctx["mov_subtitles"]:
                vf.append(f"subtitles={self._ffmpeg_filter_single_quote_value(os.path.basename(subtitle_path))}")
            af = []
            if self.ctx["mov_volume_adjust"]:
                af.append(f"volume={self.ctx['speech_volume'] / 100}")
            if self.ctx["mov_tempo_adjust"]:
                af.append(f"atempo={self.ctx['speech_speed']}")

            command = [
                ffmpeg, "-y", "-loglevel", "error",
                "-i", audio_path,
                "-loop", "1", "-i", image_path,
                "-vcodec", "libx264",
                "-pix_fmt", "yuv420p",
                "-acodec", "aac",
                "-ab", "128k",
                "-ac", "1",
                "-ar", "44100",
                "-shortest",
            ]
            if vf:
                command.extend(["-vf", ", ".join(vf)])
            if af:
                command.extend(["-af", ", ".join(af)])
            command.extend(["-crf", str(self.ctx["mov_crf"]), part_path])
            commands.append((f"{i}: {serif}", command))

        file_list_path = os.path.join(assets_dir, f"{movie_name}.txt")
        with open(file_list_path, "w", encoding="utf-8") as f:
            for part_path in part_paths:
                f.write(self._concat_file_line(part_path))

        commands.append(("concat", [ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", file_list_path, "-c", "copy", movie_path]))
        commands.append(("preview", [ffplay, "-loglevel", "error", "-autoexit", "-loop", "3", movie_path]))
        script_path = os.path.join(assets_dir, f"{movie_name}.py")
        script = [
            "# /// script",
            '# requires-python = ">=3.10"',
            "# ///",
            "",
            "import subprocess",
            "",
            f"COMMANDS = {commands!r}",
            "",
            "for label, command in COMMANDS:",
            "    print(label)",
            "    subprocess.run(command, check=True)",
            "",
        ]
        with open(script_path, "w", encoding="utf-8") as f:
            f.write("\n".join(script))
        return script_path
