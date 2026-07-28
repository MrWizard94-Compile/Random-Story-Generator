"""
Batch tab — Generate multiple stories at once across models and variants.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any
import threading
import logging
from datetime import datetime

from story_generator import (
    StoryGenerator, StoryMetrics, DEFAULT_WORD_COUNT, RAPID_MODE_WORD_COUNT
)
from theme import LEATHER, BRASS, BRASS_DIM, PARCH_BG, PARCH_FG, DARK_BG

logger = logging.getLogger(__name__)


class BatchTab:
    """Encapsulates the Batch tab UI and handlers."""

    def __init__(self, app) -> None:
        self.app = app
        self._build()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build(self) -> None:
        tab = tk.Frame(self.app.notebook, bg=DARK_BG)
        self.app.notebook.add(tab, text="Batch")
        canvas = tk.Canvas(tab, highlightthickness=0, bg=DARK_BG)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.app._apply_canvas_bg(canvas)
        overlay = tk.Frame(canvas, bg=DARK_BG)
        ow = canvas.create_window(0, 0, window=overlay, anchor='nw')
        canvas.bind('<Configure>', lambda e: (
            overlay.config(width=canvas.winfo_width(), height=canvas.winfo_height()),
            canvas.itemconfig(ow, width=canvas.winfo_width(), height=canvas.winfo_height())
        ))
        left = tk.Frame(overlay, bg=LEATHER, width=270)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)
        tk.Frame(overlay, bg=BRASS, width=2).pack(side=tk.LEFT, fill=tk.Y)
        inner = tk.Frame(left, bg=LEATHER)
        inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        tk.Label(inner, text="Batch Forge", bg=LEATHER, fg=BRASS,
                 font=('Georgia', 12, 'bold')).pack(anchor=tk.W, pady=(0, 2))
        tk.Label(inner, text="Generate multiple tales at once", bg=LEATHER, fg=BRASS_DIM,
                 font=('Segoe UI', 8, 'italic')).pack(anchor=tk.W, pady=(0, 4))

        def sect(text) -> None:
            tk.Frame(inner, bg=BRASS, height=1).pack(fill=tk.X, pady=(10, 4))
            tk.Label(inner, text=text.upper(), bg=LEATHER, fg=BRASS, font=('Segoe UI', 7, 'bold')).pack(anchor=tk.W)
        def lbl(text) -> None:
            tk.Label(inner, text=text, bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8)).pack(anchor=tk.W, pady=(6, 0))

        sect("Volume")
        lbl("Stories per run:")
        self.batch_count_var = tk.IntVar(value=3)
        ttk.Spinbox(inner, from_=1, to=100, textvariable=self.batch_count_var).pack(fill=tk.X, pady=(2, 0))

        sect("Models")
        lbl("Select spirits (multi):")
        lf = tk.Frame(inner, bg=LEATHER)
        lf.pack(fill=tk.BOTH, expand=True, pady=(2, 0))
        self.models_listbox = tk.Listbox(lf, height=6, selectmode=tk.MULTIPLE,
                                          bg=PARCH_BG, fg=PARCH_FG, relief='flat',
                                          selectbackground='#2A1E0A', selectforeground='#F2E4C4',
                                          font=('Segoe UI', 9), borderwidth=0)
        self.models_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(lf, command=self.models_listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.models_listbox.config(yscrollcommand=sb.set)
        ttk.Button(inner, text="Summon Models", command=self.app.refresh_models).pack(fill=tk.X, pady=(5, 0))

        sect("Story Nature")
        lbl("Realm (Genre):")
        self.batch_genre_var = tk.StringVar()
        ttk.Combobox(inner, textvariable=self.batch_genre_var,
                     values=["Fantasy","Science Fiction","Mystery","Romance","Horror","Comedy"]).pack(fill=tk.X, pady=(2, 0))
        lbl("Variety Engine:")
        self.batch_variety_mode_var = tk.StringVar(value="Off")
        self.batch_variety_combo = ttk.Combobox(inner, textvariable=self.batch_variety_mode_var,
                                                 values=["Off","Creative","Balanced","High Diversity"], state='readonly')
        self.batch_variety_combo.pack(fill=tk.X, pady=(2, 0))
        lbl("Variants per model:")
        self.batch_variants_var = tk.IntVar(value=3)
        ttk.Spinbox(inner, from_=1, to=6, textvariable=self.batch_variants_var).pack(fill=tk.X, pady=(2, 0))
        self.rapid_mode_var = tk.BooleanVar(value=False)
        tk.Checkbutton(inner, text="Rapid Mode (shorter)", variable=self.rapid_mode_var,
                       bg=LEATHER, fg=PARCH_FG, selectcolor=PARCH_BG,
                       activebackground=LEATHER, font=('Segoe UI', 9)).pack(anchor=tk.W, pady=(8, 0))

        sect("Summon")
        self.batch_generate_btn = tk.Button(inner, text="Forge the Batch", command=self.generate_batch,
                                             bg='#6A4A18', fg='#F2E4C4', font=('Segoe UI', 10, 'bold'),
                                             relief='flat', pady=7, activebackground='#8A6230',
                                             cursor='hand2', borderwidth=0)
        self.batch_generate_btn.pack(fill=tk.X, pady=(4, 6))
        self.batch_progress_var = tk.DoubleVar()
        ttk.Progressbar(inner, variable=self.batch_progress_var, maximum=100).pack(fill=tk.X)
        self.batch_progress_label_var = tk.StringVar(value="Ready")
        tk.Label(inner, textvariable=self.batch_progress_label_var, bg=LEATHER,
                 fg=BRASS_DIM, font=('Segoe UI', 8)).pack(pady=(2, 0))

        right = tk.Frame(overlay, bg=DARK_BG)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=16, pady=12)
        hdr = tk.Frame(right, bg=DARK_BG)
        hdr.pack(fill=tk.X, pady=(0, 8))
        tk.Label(hdr, text="Inscribed Tales", bg=DARK_BG, fg='#C4953A',
                 font=('Georgia', 13, 'bold')).pack(side=tk.LEFT)
        btn_r = tk.Frame(hdr, bg=DARK_BG)
        btn_r.pack(side=tk.RIGHT)
        def _ink(p, t, c) -> tk.Button: return tk.Button(p, text=t, command=c, bg='#1A1208', fg='#C4A86A',
            font=('Segoe UI', 9), relief='flat', padx=10, pady=4,
            activebackground='#2A1E0A', cursor='hand2', borderwidth=0)
        _ink(btn_r, "Find Best", self.compare_batch_stories).pack(side=tk.LEFT, padx=(0, 6))
        _ink(btn_r, "Save All",  self.save_all_batch_stories).pack(side=tk.LEFT)
        self.batch_results_frame = tk.Frame(right, bg=DARK_BG)
        self.batch_results_frame.pack(fill=tk.BOTH, expand=True)
        self.batch_canvas = tk.Canvas(self.batch_results_frame, bg=DARK_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.batch_results_frame, command=self.batch_canvas.yview)
        self.batch_scrollable_frame = tk.Frame(self.batch_canvas, bg=DARK_BG)
        self.batch_scrollable_frame.bind("<Configure>",
            lambda e: self.batch_canvas.configure(scrollregion=self.batch_canvas.bbox("all")))
        self.batch_canvas.create_window((0, 0), window=self.batch_scrollable_frame, anchor="nw")
        self.batch_canvas.configure(yscrollcommand=scrollbar.set)
        self.batch_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bridge: _update_models in gui_app.py references app.models_listbox
        self.app.models_listbox = self.models_listbox

    # ── Handlers ──────────────────────────────────────────────────────────────

    def generate_batch(self) -> None:
        if self.app.is_generating:
            messagebox.showwarning("Busy", "Already generating. Please wait."); return
        selected_indices = self.models_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "Please select at least one model."); return
        selected_models = [self.models_listbox.get(i) for i in selected_indices]
        genre = self.batch_genre_var.get() or None
        variety_mode = self.batch_variety_mode_var.get() != "Off"
        variants = self.batch_variants_var.get() if variety_mode else 1
        rapid_mode = self.rapid_mode_var.get()
        def generate() -> None:
            self.app.is_generating = True
            self.app._stop_event.clear()
            self.app.root.after(0, lambda: self.batch_generate_btn.config(state=tk.DISABLED))
            self.app.current_stories = []; total, current = len(selected_models) * variants, 0
            try:
                for model in selected_models:
                    for i in range(variants):
                        if self.app._stop_event.is_set():
                            break
                        current += 1
                        self.app.root.after(0, lambda c=current, t=total: (
                            self.batch_progress_var.set((c / t) * 100),
                            self.batch_progress_label_var.set(f"Forging {c}/{t}...")
                        ))
                        try:
                            if variety_mode:
                                story, _ = self.app.generator.generate_story_varied(model, genre, variant=i)
                                self.app.current_stories.append((story, model, i+1))
                            else:
                                wc = RAPID_MODE_WORD_COUNT if rapid_mode else DEFAULT_WORD_COUNT
                                story, _ = self.app.generator.generate_story(model, genre, word_count=wc)
                                self.app.current_stories.append((story, model, 0))
                        except Exception as e: logger.error(f"Error: {e}")
                    if self.app._stop_event.is_set():
                        break
                if self.app._stop_event.is_set():
                    self.app.root.after(0, lambda: self.batch_progress_label_var.set(
                        f"Stopped - {len(self.app.current_stories)} tales forged"))
                else:
                    self.app.root.after(0, lambda: self.batch_progress_var.set(100))
                    self.app.root.after(0, lambda: self.batch_progress_label_var.set(
                        f"Done - {len(self.app.current_stories)} tales"))
                if self.app.current_stories:
                    self.app.root.after(0, self._display_batch_results)
            finally:
                self.app.is_generating = False
                self.app._stop_event.clear()
                self.app.root.after(0, lambda: self.batch_generate_btn.config(state=tk.NORMAL))
        threading.Thread(target=generate, daemon=True).start()

    def _display_batch_results(self) -> None:
        for w in self.batch_scrollable_frame.winfo_children(): w.destroy()
        for idx, (story, model, variant) in enumerate(self.app.current_stories, 1):
            title = f"Tale {idx} ({model})" + (f" — Variant {variant}" if variant else "")
            frame = tk.Frame(self.batch_scrollable_frame, bg=LEATHER, pady=4)
            frame.pack(fill=tk.BOTH, expand=False, pady=4, padx=4)
            tk.Label(frame, text=title, bg=LEATHER, fg=BRASS, font=('Georgia', 10, 'bold')).pack(anchor=tk.W, padx=6, pady=(4, 2))
            tk.Frame(frame, bg=BRASS, height=1).pack(fill=tk.X, padx=6)
            tw = tk.Text(frame, height=5, wrap=tk.WORD, font=('Segoe UI', 9),
                         bg=PARCH_BG, fg=PARCH_FG, relief='flat', padx=6, pady=4)
            tw.insert("1.0", story[:400] + ("..." if len(story) > 400 else ""))
            tw.config(state=tk.DISABLED)
            tw.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
            metrics = StoryMetrics.calculate_metrics(story)
            mf = tk.Frame(frame, bg=LEATHER); mf.pack(fill=tk.X, padx=6, pady=(0, 4))
            for i, txt in enumerate([f"Words: {metrics['word_count']}", f"Sentences: {metrics['sentence_count']}",
                                      f"Readability: {metrics['readability_score']}", f"Variety: {metrics['word_variety']}%",
                                      f"Complex: {metrics['complex_word_ratio']}%", f"Dialogue: {metrics['dialogue_ratio']}%"]):
                tk.Label(mf, text=txt, bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8)
                         ).grid(row=i%3, column=i//3, sticky=tk.W, padx=8)

    def compare_batch_stories(self) -> None:
        if not self.app.current_stories: messagebox.showwarning("Empty", "No stories to compare."); return
        stories = [s for s, *_ in self.app.current_stories]
        all_metrics = [StoryMetrics.calculate_metrics(s) for s in stories]
        scores = []
        for metrics in all_metrics:
            score = 0; wcs = [m['word_count'] for m in all_metrics]; median = sorted(wcs)[len(wcs)//2]
            score += (1 - abs(metrics['word_count'] - median) / (median or 1)) * 20
            score += max(0, 10 - abs(metrics['readability_score'] - 7.5)) * 15
            score += max(0, 20 - abs(metrics['word_variety'] - 35)) * 15
            score += metrics['sentence_variety'] * 10
            score += max(0, 20 - abs(metrics['complex_word_ratio'] - 20)) * 10
            score += min(5, metrics['dialogue_ratio'] / 20) * 10
            scores.append(score)
        best_idx = scores.index(max(scores))
        story, model, _ = self.app.current_stories[best_idx]; bm = all_metrics[best_idx]
        messagebox.showinfo("Best Tale",
            f"Best: Tale #{best_idx+1} ({model})\n\n"
            f"Words: {bm['word_count']}  |  Sentences: {bm['sentence_count']}\n"
            f"Readability: {bm['readability_score']}  |  Variety: {bm['word_variety']}%\n"
            f"Score: {max(scores):.1f}/100")
        self.app._display_story(story)

    def save_all_batch_stories(self) -> None:
        if not self.app.current_stories: messagebox.showwarning("Empty", "No stories to save."); return
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        for idx, (story, model, _) in enumerate(self.app.current_stories, 1):
            safe_model = model.replace(':', '-').replace('/', '-')
            try: self.app.stories_manager.save_story(story, model, filename=f"batch_{ts}_{idx}_{safe_model}.md")
            except Exception as e: logger.error(f"Error saving story {idx}: {e}")
        messagebox.showinfo("Saved", f"Saved {len(self.app.current_stories)} stories!")
        self.app.refresh_saved_stories()
