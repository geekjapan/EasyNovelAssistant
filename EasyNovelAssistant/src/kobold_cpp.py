import json
import os
import shlex
import subprocess
import webbrowser

import requests
from model_metadata import normalize_llm_map
from path import Path
from platform_support import PlatformSupport


class KoboldCpp:
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

    CURL_TEMPLATE = """if not exist {file_name} (
    start "" {info_url}
    %CURL_CMD% -LO {url}
)
"""

    def __init__(self, ctx, platform_support=None):
        self.ctx = ctx
        self.platform = platform_support or PlatformSupport()
        Path.kobold_cpp = os.path.join(os.getcwd(), "KoboldCpp")
        Path.kobold_cpp_win = os.path.join(Path.kobold_cpp, "koboldcpp.exe")
        Path.kobold_cpp_linux = os.path.join(Path.kobold_cpp, "koboldcpp-linux-x64")
        Path.kobold_cpp_mac_arm64 = os.path.join(Path.kobold_cpp, "koboldcpp-mac-arm64")
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
        webbrowser.open(llm["info_url"])
        for url in llm["urls"]:
            curl_cmd = f"curl -k -LO {url}"
            if subprocess.run(curl_cmd, shell=True, cwd=Path.kobold_cpp).returncode != 0:
                return f"{llm_name} のダウンロードに失敗しました。\n{curl_cmd}"
        return None

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

    def launch_server(self):
        loaded_model = self.get_model()
        if loaded_model is not None:
            return f"{loaded_model} がすでにロード済みです。\nモデルサーバーのコマンドプロンプトを閉じてからロードしてください。"

        if self.ctx["llm_name"] not in self.ctx.llm:
            self.ctx["llm_name"] = "[元祖] LightChatAssistant-TypeB-2x7B-IQ4_XS"
            self.ctx["llm_gpu_layer"] = 0

        llm_name = self.ctx["llm_name"]
        gpu_layer = self.ctx["llm_gpu_layer"]

        llm = self.ctx.llm[llm_name]
        llm_path = os.path.join(Path.kobold_cpp, llm["file_name"])

        if not os.path.exists(llm_path):
            result = self.download_model(llm_name)
            if result is not None:
                return result

        if not os.path.exists(llm_path):
            return f"{llm_path} がありません。"

        command = self.build_launch_args(llm_name, gpu_layer)
        self.platform.launch_command(command, cwd=Path.kobold_cpp)
        return None

    def generate(self, text):
        args = self.build_generate_payload(text)
        print(f"KoboldCpp.generate({args})")
        try:
            response = requests.post(self.generate_url, json=args)
            if response.status_code == 200:
                if self.model_name is not None:
                    args["model_name"] = self.model_name
                args["result"] = response.json()["results"][0]["text"]
                print(f'KoboldCpp.generate(): {args["result"]}')
                with open(Path.generate_log, "a", encoding="utf-8-sig") as f:
                    json.dump(args, f, indent=4, ensure_ascii=False)
                    f.write("\n")
                return args["result"]
            print(f"[失敗] KoboldCpp.generate(): {response.text}")
        except Exception as e:
            print(f"[例外] KoboldCpp.generate(): {e}")
        return None

    def check(self):
        try:
            response = requests.get(self.check_url)
            if response.status_code == 200:
                return response.json()["results"][0]["text"]
            print(f"[失敗] KoboldCpp.check(): {response.text}")
        except Exception as e:
            pass  # print(f"[例外] KoboldCpp.check(): {e}") # 害が無さそう＆利用者が混乱しそう
        return None

    def abort(self):
        try:
            response = requests.post(self.abort_url, timeout=self.ctx["koboldcpp_command_timeout"])
            if response.status_code == 200:
                return response.json()["success"]
            print(f"[失敗] KoboldCpp.abort(): {response.text}")
        except Exception as e:
            print(f"[例外] KoboldCpp.abort(): {e}")
        return None
