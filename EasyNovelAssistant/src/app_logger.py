import json
import os
import threading
import time
import traceback

from path import Path


_config = {}
_lock = threading.Lock()
_RESERVED_KEYS = {"timestamp", "component", "event", "level", "message", "payload_conflicts"}


def configure(config):
    global _config
    _config = config or {}


def _enabled(key):
    return _config.get(key, True)


def _timestamp():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


def _write_jsonl(path, record):
    with _lock:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False)
                f.write("\n")
        except Exception:
            pass


def _base_record(component, event, level=None, message=None):
    record = {
        "timestamp": _timestamp(),
        "component": component,
        "event": event,
    }
    if level is not None:
        record["level"] = level
    if message is not None:
        record["message"] = message
    return record


def _add_details(record, details):
    conflicts = {}
    for key, value in details.items():
        if key in _RESERVED_KEYS:
            conflicts[key] = value
        else:
            record[key] = value
    if conflicts:
        record["payload_conflicts"] = conflicts
    return record


def log_generated(component, payload):
    if not _enabled("log_generated_text"):
        return
    record = _base_record(component, "generated_text")
    _add_details(record, payload)
    _write_jsonl(Path.generated_log, record)


def log_operation(component, event, message=None, **details):
    if not _enabled("log_operations"):
        return
    record = _base_record(component, event, level="OPERATION", message=message)
    _add_details(record, details)
    _write_jsonl(Path.operation_log, record)


def log_info(component, message, event="info", **details):
    if not _enabled("log_info"):
        return
    record = _base_record(component, event, level="INFO", message=message)
    _add_details(record, details)
    _write_jsonl(Path.info_log, record)


def log_error(component, message, event="error", **details):
    if not _enabled("log_errors"):
        return
    record = _base_record(component, event, level="ERROR", message=message)
    _add_details(record, details)
    _write_jsonl(Path.error_log, record)


def log_exception(component, message, error, event="exception", **details):
    details.update(
        {
            "error_type": type(error).__name__,
            "error": str(error),
            "traceback": "".join(traceback.format_exception(type(error), error, error.__traceback__)),
        }
    )
    log_error(component, message, event=event, **details)
