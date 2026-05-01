import tkinter as tk


class SpeechMenu:

    def __init__(self, form, ctx):
        self.form = form
        self.ctx = ctx

        self.menu = tk.Menu(form.win, tearoff=False)
        self.form.menu_bar.add_cascade(label="読み上げ", menu=self.menu)
        self.menu.configure(postcommand=self.on_menu_open)

    def on_menu_open(self):
        self.menu.delete(0, tk.END)

        def set_speech_enabled(*args):
            self.ctx["speech_enabled"] = self.speech_enabled_var.get()

        self.speech_enabled_var = tk.BooleanVar(value=self.ctx["speech_enabled"])
        self.speech_enabled_var.trace_add("write", set_speech_enabled)
        self.menu.add_checkbutton(label="読み上げ機能", variable=self.speech_enabled_var)
