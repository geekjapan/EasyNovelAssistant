def display_name_from_llm_name(llm_name):
    name = llm_name
    if "/" in name:
        _, name = name.rsplit("/", 1)
    if " " in name:
        name = name.split(" ")[-1]
    return name


def info_url_from_model_url(url):
    marker = "/resolve/main/"
    if marker in url:
        return url.split(marker, 1)[0]
    return url.rsplit("/", 1)[0]


def normalize_llm_entry(llm_name, llm):
    urls = llm.get("urls", [])
    if not urls:
        raise ValueError(f"{llm_name} has no urls")

    llm["name"] = display_name_from_llm_name(llm_name)
    llm["file_names"] = [url.split("/")[-1] for url in urls]
    llm["file_name"] = llm["file_names"][0]
    llm["info_url"] = info_url_from_model_url(urls[0])
    llm.setdefault("launch_args", [])
    llm.setdefault("generate_args", {})
    llm.setdefault("default_params", {})
    llm.setdefault("instruct_sequence", None)
    llm.setdefault("stop_sequence", None)
    llm.setdefault("notes", "")
    return llm


def normalize_llm_map(llms):
    for llm_name, llm in llms.items():
        normalize_llm_entry(llm_name, llm)
    return llms
