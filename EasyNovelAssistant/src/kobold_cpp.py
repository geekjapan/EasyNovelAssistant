import json
import os
import shlex
import subprocess
import tempfile
import time
import webbrowser

import app_logger
import requests
from model_metadata import normalize_llm_map
from path import Path
from platform_support import PlatformSupport


def _strip_surrounding_quotes(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def split_user_args(value, is_windows=False):
    if not value:
        return []
    if is_windows:
        return [_strip_surrounding_quotes(arg) for arg in shlex.split(value, posix=False)]
    return shlex.split(value)


class KoboldCpp:
    def __init__(self, ctx, platform_support=None, kobold_cpp_dir=None):
        self.ctx = ctx
        self.platform = platform_support or PlatformSupport()
        self.kobold_cpp_dir = str(kobold_cpp_dir or Path.kobold_cpp)
        self.base_url = f'http://{ctx["koboldcpp_host"]}:{ctx["koboldcpp_port"]}'
        self.model_url = f"{self.base_url}/api/v1/model"
        self.generate_url = f"{self.base_url}/api/v1/generate"
        self.check_url = f"{self.base_url}/api/extra/generate/check"
        self.abort_url = f"{self.base_url}/api/extra/abort"

        self.model_name = None
        self.server_process = None
        normalize_llm_map(ctx.llm)
        os.makedirs(self.kobold_cpp_dir, exist_ok=True)

    def get_model(self):
        try:
            response = requests.get(self.model_url, timeout=self.ctx["koboldcpp_command_timeout"])
            if response.status_code == 200:
                self.model_name = response.json()["result"].split("/")[-1]
                return self.model_name
        except Exception as e:
            pass
        self.model_name = None
        return self.model_name

    def get_instruct_sequence(self):
        if self.model_name is not None:
            for sequence in self.ctx.llm_sequence.values():
                for model_name in sequence["model_names"]:
                    if model_name in self.model_name:
                        return sequence["instruct"]
        return None

    def get_stop_sequence(self):
        if self.model_name is not None:
            for sequence in self.ctx.llm_sequence.values():
                for model_name in sequence["model_names"]:
                    if model_name in self.model_name:
                        return sequence["stop"]
        return []

    def download_model(self, llm_name):
        llm = self.ctx.llm[llm_name]
        app_logger.log_operation("kobold_cpp", "download_model_start", llm_name=llm_name, urls=llm["urls"])
        webbrowser.open(llm["info_url"])
        for url in llm["urls"]:
            file_name = url.split("/")[-1]
            final_path = os.path.join(self.kobold_cpp_dir, file_name)
            with tempfile.NamedTemporaryFile(
                prefix=f".{file_name}.",
                suffix=".tmp",
                dir=self.kobold_cpp_dir,
                delete=False,
            ) as temp_file:
                temp_path = temp_file.name
            curl_cmd = ["curl", "-k", "-L", "-f", "-o", temp_path, url]
            try:
                if subprocess.run(curl_cmd, cwd=self.kobold_cpp_dir).returncode != 0:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    app_logger.log_error(
                        "kobold_cpp",
                        "model download failed",
                        event="download_model_failed",
                        llm_name=llm_name,
                        url=url,
                        command=curl_cmd,
                    )
                    return f'{llm_name} のダウンロードに失敗しました。\n{" ".join(curl_cmd)}'
                os.replace(temp_path, final_path)
                app_logger.log_operation(
                    "kobold_cpp",
                    "download_model_file_done",
                    llm_name=llm_name,
                    url=url,
                    output_path=final_path,
                )
            except Exception as error:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                app_logger.log_exception(
                    "kobold_cpp",
                    "model download raised exception",
                    error,
                    event="download_model_exception",
                    llm_name=llm_name,
                    url=url,
                    temp_path=temp_path,
                )
                raise
        app_logger.log_operation("kobold_cpp", "download_model_done", llm_name=llm_name)
        return None

    def get_kobold_cpp_executable(self):
        return str(self.platform.kobold_cpp_path(self.kobold_cpp_dir))

    def build_launch_args(self, llm_name, gpu_layer):
        llm = self.ctx.llm[llm_name]
        llm_path = os.path.join(self.kobold_cpp_dir, llm["file_name"])
        context_size = min(llm["context_size"], self.ctx["llm_context_size"])
        args = [self.get_kobold_cpp_executable()]
        args.extend(split_user_args(self.ctx["koboldcpp_arg"], is_windows=self.platform.is_windows()))
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
            app_logger.log_info(
                "kobold_cpp",
                "max_length exceeds context size; shortened",
                event="max_length_shortened",
                max_length=ctx["max_length"],
                max_context_length=max_context_length,
                new_max_length=max_context_length // 2,
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

    def ensure_valid_llm_selection(self):
        if self.ctx["llm_name"] not in self.ctx.llm:
            self.ctx["llm_name"] = "[元祖] LightChatAssistant-TypeB-2x7B-IQ4_XS"
            self.ctx["llm_gpu_layer"] = 0

    def is_managed_server_running(self):
        return self.server_process is not None and self.server_process.poll() is None

    def stop_server(self, timeout=10):
        if not self.is_managed_server_running():
            self.server_process = None
            return False
        app_logger.log_operation("kobold_cpp", "stop_server", pid=getattr(self.server_process, "pid", None))
        self.server_process.terminate()
        try:
            self.server_process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            app_logger.log_error("kobold_cpp", "server did not stop in time; killing", event="stop_server_timeout")
            self.server_process.kill()
            self.server_process.wait(timeout=timeout)
        self.server_process = None
        return True

    def wait_until_model_unloaded(self, timeout=15, interval=0.5):
        deadline = time.perf_counter() + timeout
        while time.perf_counter() < deadline:
            if self.get_model() is None:
                return True
            time.sleep(interval)
        return self.get_model() is None

    def launch_server(self):
        self.ensure_valid_llm_selection()
        llm_name = self.ctx["llm_name"]
        gpu_layer = self.ctx["llm_gpu_layer"]
        llm = self.ctx.llm[llm_name]
        target_file_name = llm["file_name"]

        loaded_model = self.get_model()
        if loaded_model is not None:
            if loaded_model == target_file_name:
                app_logger.log_operation("kobold_cpp", "model_already_loaded", llm_name=llm_name, model=loaded_model)
                return None
            if self.stop_server() and self.wait_until_model_unloaded():
                app_logger.log_operation(
                    "kobold_cpp",
                    "switch_model_after_stop",
                    previous_model=loaded_model,
                    next_model=target_file_name,
                )
            else:
                return (
                    f"{loaded_model} がすでにロード済みです。\n"
                    f"{target_file_name} に切り替えるには、モデルサーバーのコマンドプロンプトを閉じてください。"
                )

        llm_path = os.path.join(self.kobold_cpp_dir, llm["file_name"])

        if not os.path.exists(llm_path):
            result = self.download_model(llm_name)
            if result is not None:
                return result

        if not os.path.exists(llm_path):
            return f"{llm_path} がありません。"

        command = self.build_launch_args(llm_name, gpu_layer)
        app_logger.log_operation(
            "kobold_cpp",
            "launch_server",
            llm_name=llm_name,
            gpu_layer=gpu_layer,
            command=command,
            cwd=self.kobold_cpp_dir,
        )
        self.server_process = self.platform.launch_command(command, cwd=self.kobold_cpp_dir)
        return None

    def generate(self, text):
        args = self.build_generate_payload(text)
        start_time = time.perf_counter()
        app_logger.log_operation(
            "kobold_cpp",
            "generate_request",
            llm_name=self.ctx["llm_name"],
            max_length=args["max_length"],
            max_context_length=args["max_context_length"],
        )
        try:
            response = requests.post(self.generate_url, json=args)
            if response.status_code == 200:
                if self.model_name is not None:
                    args["model_name"] = self.model_name
                args["result"] = response.json()["results"][0]["text"]
                args["elapsed_sec"] = round(time.perf_counter() - start_time, 3)
                app_logger.log_generated("kobold_cpp", args)
                return args["result"]
            app_logger.log_error(
                "kobold_cpp",
                "generate request failed",
                event="generate_failed",
                status_code=response.status_code,
                response_text=response.text,
                payload=args,
            )
        except Exception as e:
            app_logger.log_exception("kobold_cpp", "generate request raised exception", e, payload=args)
        return None

    def check(self):
        try:
            response = requests.get(self.check_url)
            if response.status_code == 200:
                return response.json()["results"][0]["text"]
            app_logger.log_error(
                "kobold_cpp",
                "check request failed",
                event="check_failed",
                status_code=response.status_code,
                response_text=response.text,
            )
        except Exception:
            pass
        return None

    def abort(self):
        try:
            response = requests.post(self.abort_url, timeout=self.ctx["koboldcpp_command_timeout"])
            if response.status_code == 200:
                return response.json()["success"]
            app_logger.log_error(
                "kobold_cpp",
                "abort request failed",
                event="abort_failed",
                status_code=response.status_code,
                response_text=response.text,
            )
        except Exception as e:
            app_logger.log_exception("kobold_cpp", "abort request raised exception", e)
        return None
