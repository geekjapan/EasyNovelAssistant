from dataclasses import dataclass
import json
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

import requests


HF_HOST = "huggingface.co"
HF_API_BASE = "https://huggingface.co/api/models"
DEFAULT_CONTEXT_SIZE = 131072
DEFAULT_MAX_GPU_LAYER = 99


@dataclass(frozen=True)
class HfGgufReference:
    repo_id: str
    file_path: str | None = None
    revision: str = "main"

    @property
    def url(self):
        if self.file_path is None:
            return None
        return build_hf_resolve_url(self.repo_id, self.file_path, self.revision)

    @property
    def info_url(self):
        return f"https://{HF_HOST}/{quote(self.repo_id, safe='/')}"


def parse_hf_gguf_reference(text):
    value = text.strip()
    if not value:
        raise ValueError("Hugging Face のモデル名またはGGUF URLを入力してください。")

    if value.startswith("http://") or value.startswith("https://"):
        return parse_hf_gguf_url(value)

    if " " in value or value.count("/") != 1:
        raise ValueError("Hugging Face のモデル名は owner/repo 形式で入力してください。")
    return HfGgufReference(repo_id=value)


def parse_hf_gguf_url(url):
    parsed = urlparse(url.strip())
    if parsed.netloc != HF_HOST:
        raise ValueError("huggingface.co のURLを入力してください。")

    parts = [unquote(part) for part in parsed.path.split("/") if part]
    if len(parts) == 2:
        return HfGgufReference(repo_id="/".join(parts))
    if len(parts) == 4 and parts[2] == "tree":
        return HfGgufReference(repo_id="/".join(parts[:2]), revision=parts[3])
    if len(parts) < 5 or parts[2] not in ("blob", "resolve"):
        raise ValueError("Hugging Face のGGUFファイルURLを入力してください。")

    repo_id = "/".join(parts[:2])
    revision = parts[3]
    file_path = "/".join(parts[4:])
    if not file_path.lower().endswith(".gguf"):
        raise ValueError("GGUFファイルのURLを入力してください。")
    return HfGgufReference(repo_id=repo_id, file_path=file_path, revision=revision)


def build_hf_resolve_url(repo_id, file_path, revision="main"):
    return (
        f"https://{HF_HOST}/{quote(repo_id, safe='/')}/resolve/"
        f"{quote(revision, safe='')}/{quote(file_path, safe='/')}"
    )


def fetch_hf_model_payload(repo_id, timeout=15):
    url = f"{HF_API_BASE}/{quote(repo_id, safe='/')}"
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def gguf_siblings_from_api_payload(payload):
    files = []
    for sibling in payload.get("siblings", []):
        file_path = sibling.get("rfilename")
        if file_path and file_path.lower().endswith(".gguf"):
            files.append(file_path)
    return sorted(files, key=str.lower)


def build_gguf_llm_entry(repo_id, file_path, revision="main"):
    return {
        "urls": [build_hf_resolve_url(repo_id, file_path, revision)],
        "context_size": DEFAULT_CONTEXT_SIZE,
        "max_gpu_layer": DEFAULT_MAX_GPU_LAYER,
        "launch_args": ["--jinja"],
        "generate_args": {},
    }


def build_custom_llm_name(repo_id, file_path):
    file_name = Path(file_path).name
    stem = file_name[:-5] if file_name.lower().endswith(".gguf") else file_name
    repo_label = repo_id.replace("/", " - ")
    return f"Hugging Face/{repo_label} {stem}"


def save_custom_llm_entry(llm_path, llm_name, entry):
    path = Path(llm_path)
    if path.exists():
        with path.open("r", encoding="utf-8-sig") as f:
            llms = json.load(f)
    else:
        llms = {}
    llms[llm_name] = entry
    with path.open("w", encoding="utf-8-sig") as f:
        json.dump(llms, f, indent=4, ensure_ascii=False)
        f.write("\n")
