"""
Models tab — View available Ollama models and pull new ones.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

from theme import LEATHER, BRASS, BRASS_DIM, PARCH_BG, PARCH_FG, DARK_BG


class ModelsTab:
    """Encapsulates the Model Management tab UI and handlers."""

    def __init__(self, app) -> None:
        self.app = app
        self._build()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build(self) -> None:
        tab = tk.Frame(self.app.notebook, bg=DARK_BG)
        self.app.notebook.add(tab, text="Models")
        canvas = tk.Canvas(tab, highlightthickness=0, bg=DARK_BG)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.app._apply_canvas_bg(canvas)
        overlay = tk.Frame(canvas, bg=DARK_BG)
        ow = canvas.create_window(0, 0, window=overlay, anchor='nw')
        canvas.bind('<Configure>', lambda e: (
            overlay.config(width=canvas.winfo_width(), height=canvas.winfo_height()),
            canvas.itemconfig(ow, width=canvas.winfo_width(), height=canvas.winfo_height())
        ))
        left = tk.Frame(overlay, bg=LEATHER)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 6), pady=12)
        tk.Label(left, text="Known Spirits", bg=LEATHER, fg=BRASS,
                 font=('Georgia', 12, 'bold')).pack(anchor=tk.W, pady=(0, 4))
        tk.Frame(left, bg=BRASS, height=1).pack(fill=tk.X, pady=(0, 6))
        lf = tk.Frame(left, bg=LEATHER)
        lf.pack(fill=tk.BOTH, expand=True)
        self.models_display = tk.Listbox(lf, height=20, bg=PARCH_BG, fg=PARCH_FG,
                                          relief='flat', font=('Segoe UI', 10),
                                          selectbackground='#2A1E0A', selectforeground='#F2E4C4',
                                          borderwidth=0)
        self.models_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(lf, command=self.models_display.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.models_display.config(yscrollcommand=sb.set)
        ttk.Button(left, text="Summon Models", command=self.app.refresh_models).pack(fill=tk.X, pady=(8, 0))
        tk.Frame(overlay, bg=BRASS, width=2).pack(side=tk.LEFT, fill=tk.Y, pady=12)
        right = tk.Frame(overlay, bg=LEATHER, width=280)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 12), pady=12)
        right.pack_propagate(False)
        tk.Label(right, text="Bind New Spirit", bg=LEATHER, fg=BRASS,
                 font=('Georgia', 12, 'bold')).pack(anchor=tk.W, pady=(0, 4))
        tk.Frame(right, bg=BRASS, height=1).pack(fill=tk.X, pady=(0, 8))
        tk.Label(right, text="Spirit name:", bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8)).pack(anchor=tk.W)
        self.new_model_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.new_model_var).pack(fill=tk.X, pady=(2, 8))
        tk.Frame(right, bg='#3A2810', height=1).pack(fill=tk.X, pady=(0, 6))
        tk.Label(right, text="Common spirits:", bg=LEATHER, fg=BRASS_DIM,
                 font=('Segoe UI', 8, 'italic')).pack(anchor=tk.W, pady=(0, 4))
        for model in ["llama2","mistral","neural-chat","starling-lm","openchat","dolphin-mixtral"]:
            tk.Button(right, text=model, command=lambda m=model: self.new_model_var.set(m),
                      bg='#1A1208', fg=PARCH_FG, font=('Segoe UI', 9), relief='flat',
                      padx=8, pady=3, activebackground='#2A1E0A', cursor='hand2',
                      borderwidth=0).pack(fill=tk.X, pady=2)
        tk.Frame(right, bg='#3A2810', height=1).pack(fill=tk.X, pady=(6, 0))
        tk.Button(right, text="Bind to Library", command=self.pull_model,
                  bg='#6A4A18', fg='#F2E4C4', font=('Segoe UI', 10, 'bold'), relief='flat', pady=7,
                  activebackground='#8A6230', cursor='hand2', borderwidth=0).pack(fill=tk.X, pady=(6, 0))
        self.model_status_var = tk.StringVar(value="Ready")
        tk.Label(right, textvariable=self.model_status_var, bg=LEATHER, fg=BRASS,
                 wraplength=240, justify=tk.LEFT, font=('Segoe UI', 8)).pack(pady=8)

        # Bridge: _update_models in gui_app.py references app.models_display
        self.app.models_display = self.models_display

    # ── Handlers ──────────────────────────────────────────────────────────────

    def pull_model(self) -> None:
        model_name = self.new_model_var.get().strip()
        if not model_name: messagebox.showerror("Error", "Enter a model name."); return
        def pull() -> None:
            import subprocess, shutil
            if not shutil.which("ollama"):
                self.app.root.after(0, lambda: self.model_status_var.set("Error: ollama not in PATH")); return
            self.model_status_var.set(f"Binding {model_name}...")
            try:
                r = subprocess.run(["ollama", "pull", model_name], capture_output=True, text=True, timeout=600, encoding="utf-8", errors="replace")
                if r.returncode == 0:
                    self.app.root.after(0, lambda: self.model_status_var.set(f"{model_name} bound!"))
                    self.app.root.after(1000, self.app.refresh_models)
                else: self.app.root.after(0, lambda: self.model_status_var.set(f"Failed to bind {model_name}"))
            except Exception as e: self.app.root.after(0, lambda err=e: self.model_status_var.set(f"Error: {err}"))
        threading.Thread(target=pull, daemon=True).start()
