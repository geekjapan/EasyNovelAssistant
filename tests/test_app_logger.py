import json

import app_logger


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines()]


def test_app_logger_writes_separate_structured_logs(tmp_path, monkeypatch):
    generated_log = tmp_path / "generated.jsonl"
    operations_log = tmp_path / "operations.log"
    info_log = tmp_path / "info.log"
    errors_log = tmp_path / "errors.log"
    monkeypatch.setattr(app_logger.Path, "generated_log", str(generated_log))
    monkeypatch.setattr(app_logger.Path, "operation_log", str(operations_log))
    monkeypatch.setattr(app_logger.Path, "info_log", str(info_log))
    monkeypatch.setattr(app_logger.Path, "error_log", str(errors_log))

    app_logger.log_generated("kobold", {"prompt": "hello", "result": "world"})
    app_logger.log_operation("ui", "toggle_speech", enabled=False)
    app_logger.log_info("speech", "queue full", text="line")
    app_logger.log_error("speech", "request failed", status_code=500, response_text="bad")

    assert read_jsonl(generated_log)[0]["event"] == "generated_text"
    assert read_jsonl(generated_log)[0]["prompt"] == "hello"
    assert read_jsonl(operations_log)[0]["event"] == "toggle_speech"
    assert read_jsonl(info_log)[0]["level"] == "INFO"
    assert read_jsonl(errors_log)[0]["level"] == "ERROR"


def test_app_logger_records_exception_traceback(tmp_path, monkeypatch):
    error_log = tmp_path / "errors.log"
    monkeypatch.setattr(app_logger.Path, "error_log", str(error_log))

    try:
        raise RuntimeError("boom")
    except RuntimeError as error:
        app_logger.log_exception("kobold", "generate crashed", error)

    record = read_jsonl(error_log)[0]
    assert record["message"] == "generate crashed"
    assert record["error_type"] == "RuntimeError"
    assert "Traceback" in record["traceback"]


def test_app_logger_respects_config_flags(tmp_path, monkeypatch):
    info_log = tmp_path / "info.log"
    monkeypatch.setattr(app_logger.Path, "info_log", str(info_log))

    app_logger.configure({"log_info": False})
    app_logger.log_info("speech", "hidden")
    app_logger.configure({})

    assert not info_log.exists()
