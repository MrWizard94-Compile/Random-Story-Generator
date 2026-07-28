"""
Thread Formatter tab — Split stories into social media threads and quick-post formats.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any
from datetime import datetime, timedelta

from story_generator import StoryGenerator, DEFAULT_MAX_CHARS, THREAD_POST_INTERVAL_MINUTES
from theme import LEATHER, BRASS, BRASS_DIM, PARCH_BG, PARCH_FG, DARK_BG


class ThreadFormatterTab:
    """Encapsulates the Thread Formatter tab UI and handlers."""

    def __init__(self, app) -> None:
        self.app = app
        self.thread_segments: list = []
        self._build()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build(self) -> None:
        tab = tk.Frame(self.app.notebook, bg=DARK_BG)
        self.app.notebook.add(tab, text="Thread")
        canvas = tk.Canvas(tab, highlightthickness=0, bg=DARK_BG)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.app._apply_canvas_bg(canvas)
        overlay = tk.Frame(canvas, bg=DARK_BG)
        ow = canvas.create_window(0, 0, window=overlay, anchor='nw')
        canvas.bind('<Configure>', lambda e: (
            overlay.config(width=canvas.winfo_width(), height=canvas.winfo_height()),
            canvas.itemconfig(ow, width=canvas.winfo_width(), height=canvas.winfo_height())
        ))
        main = tk.Frame(overlay, bg=DARK_BG)
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        top_panel = tk.Frame(main, bg=LEATHER)
        top_panel.pack(fill=tk.X, pady=(0, 6))
        tk.Label(top_panel, text="Thread Formatter", bg=LEATHER, fg=BRASS,
                 font=('Georgia', 12, 'bold'), padx=8, pady=6).pack(side=tk.LEFT)
        tk.Frame(top_panel, bg=BRASS, height=1).pack(side=tk.BOTTOM, fill=tk.X)

        sel_f = tk.Frame(main, bg=LEATHER)
        sel_f.pack(fill=tk.X, pady=(0, 4))
        sel_inner = tk.Frame(sel_f, bg=LEATHER)
        sel_inner.pack(fill=tk.X, padx=10, pady=8)
        tk.Label(sel_inner, text="Source Tale:", bg=LEATHER, fg=BRASS, font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 6))
        self.thread_story_var = tk.StringVar()
        self.thread_story_combo = ttk.Combobox(sel_inner, textvariable=self.thread_story_var, width=60, state='readonly')
        self.thread_story_combo.pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(sel_inner, text="Refresh", command=self.refresh_story_options).pack(side=tk.LEFT)

        opts_f = tk.Frame(main, bg=LEATHER)
        opts_f.pack(fill=tk.X, pady=(0, 6))
        opts_inner = tk.Frame(opts_f, bg=LEATHER)
        opts_inner.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(opts_inner, text="Max chars/post:", bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 4))
        self.thread_max_chars_var = tk.IntVar(value=DEFAULT_MAX_CHARS)
        ttk.Spinbox(opts_inner, from_=60, to=1000, textvariable=self.thread_max_chars_var, width=7).pack(side=tk.LEFT, padx=(0, 12))
        tk.Label(opts_inner, text="Platform:", bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 4))
        self.thread_platform_var = tk.StringVar(value="X")
        ttk.Combobox(opts_inner, textvariable=self.thread_platform_var,
                     values=["X", "Facebook", "Threads", "Instagram"],
                     width=10, state='readonly').pack(side=tk.LEFT, padx=(0, 16))

        def _ink(t, c, accent=False) -> Any:
            return tk.Button(opts_inner, text=t, command=c,
                             bg='#6A4A18' if accent else '#1A1208',
                             fg='#F2E4C4' if accent else PARCH_FG,
                             font=('Segoe UI', 9), relief='flat', padx=10, pady=4,
                             activebackground='#8A6230' if accent else '#2A1E0A',
                             cursor='hand2', borderwidth=0)
        _ink("Generate Thread", self._generate_thread, accent=True).pack(side=tk.LEFT, padx=(0, 6))
        _ink("Copy Full Thread", self._copy_thread).pack(side=tk.LEFT)

        res_f = tk.Frame(main, bg=LEATHER)
        res_f.pack(fill=tk.BOTH, expand=True)
        tk.Label(res_f, text="Thread Segments", bg=LEATHER, fg=BRASS,
                 font=('Segoe UI', 9, 'bold'), padx=8, pady=4).pack(anchor=tk.W)
        tk.Frame(res_f, bg=BRASS, height=1).pack(fill=tk.X, padx=8)
        lf2 = tk.Frame(res_f, bg=LEATHER)
        lf2.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.thread_listbox = tk.Listbox(lf2, font=('Segoe UI', 10),
                                          bg=PARCH_BG, fg=PARCH_FG, relief='flat',
                                          selectbackground='#2A1E0A', selectforeground='#F2E4C4',
                                          borderwidth=0)
        self.thread_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb5 = ttk.Scrollbar(lf2, command=self.thread_listbox.yview)
        sb5.pack(side=tk.RIGHT, fill=tk.Y)
        self.thread_listbox.config(yscrollcommand=sb5.set)
        qf = tk.Frame(main, bg=LEATHER)
        qf.pack(fill=tk.X, pady=(4, 0))
        qf_inner = tk.Frame(qf, bg=LEATHER)
        qf_inner.pack(padx=8, pady=6)
        _ink("Enqueue (10m intervals)", self._enqueue_thread).pack(side=tk.LEFT, padx=(0, 6))
        _ink("Quick Post Format", self._apply_quick_post).pack(side=tk.LEFT)

        self.refresh_story_options()

    # ── Handlers ──────────────────────────────────────────────────────────────

    def refresh_story_options(self) -> None:
        stories = self.app.stories_manager.get_all_stories_metadata()
        self.thread_story_combo['values'] = [f"{s['filename']} | {s.get('title','Untitled')}" for s in stories]

    def _generate_thread(self) -> None:
        choice = self.thread_story_var.get().strip()
        if not choice or ' | ' not in choice:
            messagebox.showwarning("Error", "Select a valid story first."); return
        text = self.app.stories_manager.load_story(choice.split(' | ')[0])
        if not text:
            messagebox.showerror("Error", "Could not load story."); return
        from story_generator import ContentQueueManager
        self.thread_segments = ContentQueueManager.format_story_as_thread(
            text, self.thread_max_chars_var.get() or DEFAULT_MAX_CHARS
        )
        self.thread_listbox.delete(0, tk.END)
        for seg in self.thread_segments:
            self.thread_listbox.insert(tk.END, seg)
        self.app.status_var.set(f"Thread: {len(self.thread_segments)} posts.")

    def _copy_thread(self) -> None:
        if not self.thread_segments:
            messagebox.showwarning("Error", "No thread yet."); return
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append("\n\n".join(self.thread_segments))
        messagebox.showinfo("Copied", "Thread copied!")

    def _enqueue_thread(self) -> None:
        if not self.thread_segments:
            messagebox.showwarning("Error", "No thread segments."); return
        choice = self.thread_story_var.get().strip()
        if not choice or ' | ' not in choice:
            messagebox.showwarning("Error", "Select a story."); return
        fname = choice.split(' | ')[0]
        base = datetime.now()
        for idx, seg in enumerate(self.thread_segments):
            st = base + timedelta(minutes=THREAD_POST_INTERVAL_MINUTES * idx)
            self.app.queue_manager.add_to_queue({
                'id': f"{fname}_t{idx}_{int(st.timestamp())}", 'story_id': fname,
                'story_title': f"Thread {idx+1}/{len(self.thread_segments)}",
                'scheduled_time': st, 'platform': 'X', 'status': 'scheduled', 'content': seg})
        self.app.refresh_queue_list()
        messagebox.showinfo("Enqueued", f"{len(self.thread_segments)} posts queued.")

    def _apply_quick_post(self) -> None:
        choice = self.thread_story_var.get().strip()
        if not choice:
            messagebox.showwarning("Error", "Select a story."); return
        text = self.app.stories_manager.load_story(choice.split(' | ')[0])
        if not text:
            messagebox.showerror("Error", "Could not load story."); return
        platform = self.thread_platform_var.get() or 'X'
        formatted = StoryGenerator.format_story_for_platform(text, platform=platform)
        self.thread_listbox.delete(0, tk.END)
        for line in formatted.splitlines():
            self.thread_listbox.insert(tk.END, line)
        self.app.status_var.set(f"Quick post format ({platform}) ready.")
