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
