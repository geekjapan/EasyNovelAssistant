import json
import os
import shutil
import subprocess
import sys
import time

import app_logger
import numpy as np
import requests
from job_queue import JobQueue
from path import Path
from platform_support import PlatformSupport
from scipy.io import wavfile


class StyleBertVits2:
    def __init__(self, ctx, platform_support=None, style_bert_vits2_dir=None):
        self.ctx = ctx
        self.platform = platform_support or PlatformSupport()
        self.style_bert_vits2_dir = str(style_bert_vits2_dir or Path.style_bert_vits2)
        self.base_url = f'http://{ctx["style_bert_vits2_host"]}:{ctx["style_bert_vits2_port"]}'
        self.models_url = f"{self.base_url}/models/info"
        self.voice_url = f"{self.base_url}/voice"

        self.models = None
        self.gen_queue = JobQueue()
        self.play_queue = JobQueue()

    def build_uv_command(self, script_name, args=None):
        return [
            "uv",
            "run",
            "--python",
            sys.executable,
            "--with-requirements",
            "requirements.txt",
            "--with",
            "GPUtil",
            "--with",
            "torch",
            "--with",
            "torchvision",
            "--with",
            "torchaudio",
            "--index",
            "https://download.pytorch.org/whl/cu118",
            "--index-strategy",
            "unsafe-best-match",
            script_name,
        ] + list(args or [])

    def install(self):
        msg = f"{Path.style_bert_vits2} に Style-Bert-VITS2 をインストールして、"
        app_logger.log_info(
            "speech",
            msg + "uv run EasyNovelAssistant/setup/ena.py setup を実行してください。",
            event="style_bert_vits2_setup_required",
        )

    def launch_server(self):
        self._run_server()

    def _run_server(self):
        launch_command = self.build_uv_command("server_fastapi.py")
        app_logger.log_operation("speech", "launch_server", command=launch_command, cwd=self.style_bert_vits2_dir)
        self.platform.launch_command(launch_command, cwd=self.style_bert_vits2_dir)

    def get_models(self):
        try:
            response = requests.get(self.models_url, timeout=self.ctx["style_bert_vits2_command_timeout"])
            if response.status_code == 200:
                data = response.json()
                models = None
                for key in data:
                    model_id = int(key)
                    model = data[key]
                    model_name = model["id2spk"]["0"]
                    model_style = "Neutral"
                    if not model_style in model["style2id"]:
                        model_style = list(model["style2id"].keys())[0]
                    if models is None:
                        models = {}
                    models[model_name] = {"id": model_id, "style": model_style}
                self.models = models
                return self.models
        except Exception as e:
            pass
        self.models = None
        return self.models

    def update(self):
        self.gen_queue.update()
        self.play_queue.update()

    def abort(self):
        self.gen_queue.cancel_all()
        self.play_queue.cancel_all()

    def get_ffplay_executable(self):
        if os.path.exists(Path.ffplay):
            return Path.ffplay
        return shutil.which("ffplay") or "ffplay"

    def generate(self, text, force=False):
        if not self.ctx["speech_enabled"]:
            return False

        max_speech_queue = self.ctx["max_speech_queue"]

        if not force:
            gen_queue_len = self.gen_queue.len()
            play_queue_len = self.play_queue.len()
            if (gen_queue_len > max_speech_queue) or (play_queue_len > max_speech_queue):
                app_logger.log_info(
                    "speech",
                    "speech queue is full; skipped",
                    event="speech_queue_skipped",
                    text=text,
                    gen_queue_len=gen_queue_len,
                    play_queue_len=play_queue_len,
                    max_speech_queue=max_speech_queue,
                )
                return False
        self.gen_queue.push(self._generate, text=text)
        return True

    def _generate(self, text):
        models = self.get_models()
        if models is None:
            return None

        model_id = 0
        model_style = "Neutral"
        if "「" in text:
            name, msg = text.split("「", 1)
            if msg.endswith("」"):
                msg = msg[:-1]
            if self.ctx["char_name"] in name:
                if self.ctx["char_voice"] in self.models:
                    model_id = self.models[self.ctx["char_voice"]]["id"]
                    model_style = self.models[self.ctx["char_voice"]]["style"]
                    text = msg
            elif self.ctx["user_name"] in name:
                if self.ctx["user_voice"] in self.models:
                    model_id = self.models[self.ctx["user_voice"]]["id"]
                    model_style = self.models[self.ctx["user_voice"]]["style"]
                    text = msg
            else:
                if self.ctx["other_voice"] in self.models:
                    model_id = self.models[self.ctx["other_voice"]]["id"]
                    model_style = self.models[self.ctx["other_voice"]]["style"]
        else:
            if self.ctx["other_voice"] in self.models:
                model_id = self.models[self.ctx["other_voice"]]["id"]
                model_style = self.models[self.ctx["other_voice"]]["style"]

        params = {"text": text, "model_id": model_id, "split_interval": 0.2, "style": model_style}

        try:
            start_time = time.perf_counter()
            response = requests.post(self.voice_url, params=params, headers={"accept": "audio/wav"})
            if response.status_code == 200:
                os.makedirs(Path.daily_speech, exist_ok=True)
                YYYYMMDD_HHMMSS = time.strftime("%Y%m%d_%H%M%S", time.localtime())
                wav_path = os.path.join(Path.daily_speech, f"{YYYYMMDD_HHMMSS}-{Path.get_path_name(text[:128])}.wav")
                with open(wav_path, "wb") as f:
                    f.write(response.content)

                # 無音の付与
                sample_rate, data = wavfile.read(wav_path)
                silence = np.zeros(int(sample_rate * self.ctx["speech_interval"]))
                data_with_silence = np.append(data, silence)
                wavfile.write(wav_path, sample_rate, data_with_silence.astype(np.int16))

                self.play_queue.push(self._play, wav_path=wav_path)
                app_logger.log_info(
                    "speech",
                    "speech generated",
                    event="speech_generated",
                    text=text,
                    wav_path=wav_path,
                    elapsed_sec=round(time.perf_counter() - start_time, 3),
                )
                return True
            app_logger.log_error(
                "speech",
                "speech request failed",
                event="speech_generate_failed",
                status_code=response.status_code,
                response_text=response.text,
                params=params,
            )
        except Exception as e:
            app_logger.log_exception("speech", "speech generation raised exception", e, params=params)
        return None

    def _play(self, wav_path):
        subprocess.Popen(
            [
                self.get_ffplay_executable(),
                "-volume",
                f'{self.ctx["speech_volume"]}',
                "-af",
                f'atempo={self.ctx["speech_speed"]}',
                "-autoexit",
                "-nodisp",
                "-loglevel",
                "fatal",
                wav_path,
            ],
            stdout=subprocess.DEVNULL,  # 終了時の改行対策、stderrは残す
        ).wait()
