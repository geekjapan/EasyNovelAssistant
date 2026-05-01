import sys
from types import SimpleNamespace
from unittest.mock import Mock

sys.modules.setdefault(
    "tkinter",
    SimpleNamespace(Menu=Mock(), BooleanVar=Mock(), END="end"),
)

import menu.speech_menu as speech_menu
from menu.speech_menu import SpeechMenu


class FakeBooleanVar:
    def __init__(self, value=False):
        self.value = value
        self.callbacks = []

    def get(self):
        return self.value

    def set(self, value):
        self.value = value
        for callback in self.callbacks:
            callback()

    def trace_add(self, _mode, callback):
        self.callbacks.append(callback)


class FakeMenu:
    def __init__(self):
        self.items = []

    def delete(self, *_args):
        self.items.clear()

    def add_checkbutton(self, **kwargs):
        self.items.append(("checkbutton", kwargs))

    def add_command(self, **kwargs):
        self.items.append(("command", kwargs))

    def add_separator(self):
        self.items.append(("separator", {}))

    def add_cascade(self, **kwargs):
        self.items.append(("cascade", kwargs))


class FakeContext(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.style_bert_vits2 = Mock()
        self.form = Mock()


def test_speech_menu_only_exposes_global_enable_toggle(monkeypatch):
    monkeypatch.setattr(speech_menu.tk, "BooleanVar", FakeBooleanVar)
    menu = SpeechMenu.__new__(SpeechMenu)
    menu.menu = FakeMenu()
    menu.ctx = FakeContext(
        speech_enabled=True,
        style_bert_vits2_gpu=True,
        middle_click_speech=True,
        auto_speech_char=True,
        auto_speech_user=True,
        auto_speech_other=True,
        char_name="さくら",
        user_name="俺くん",
    )

    menu.on_menu_open()

    assert [(kind, item["label"]) for kind, item in menu.menu.items] == [("checkbutton", "読み上げ機能")]


def test_speech_menu_toggle_updates_context(monkeypatch):
    monkeypatch.setattr(speech_menu.tk, "BooleanVar", FakeBooleanVar)
    menu = SpeechMenu.__new__(SpeechMenu)
    menu.menu = FakeMenu()
    menu.ctx = {"speech_enabled": True}

    menu.on_menu_open()
    _, item = menu.menu.items[0]
    item["variable"].set(False)

    assert menu.ctx["speech_enabled"] is False
