"""
Saved Stories tab — Browse, filter, rate, export, and manage saved stories.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Any
import logging

from theme import LEATHER, BRASS, BRASS_DIM, PARCH_BG, PARCH_FG, DARK_BG

logger = logging.getLogger(__name__)


class SavedStoriesTab:
    """Encapsulates the Saved Stories tab UI and handlers."""

    def __init__(self, app) -> None:
        self.app = app
        self._build()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build(self) -> None:
        tab = tk.Frame(self.app.notebook, bg=DARK_BG)
        self.app.notebook.add(tab, text="Saved")
        canvas = tk.Canvas(tab, highlightthickness=0, bg=DARK_BG)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.app._apply_canvas_bg(canvas)
        overlay = tk.Frame(canvas, bg=DARK_BG)
        ow = canvas.create_window(0, 0, window=overlay, anchor='nw')
        canvas.bind('<Configure>', lambda e: (
            overlay.config(width=canvas.winfo_width(), height=canvas.winfo_height()),
            canvas.itemconfig(ow, width=canvas.winfo_width(), height=canvas.winfo_height())
        ))

        # Search bar across top
        search_bar = tk.Frame(overlay, bg=LEATHER)
        search_bar.pack(fill=tk.X, padx=0, pady=0)
        tk.Frame(overlay, bg=BRASS, height=1).pack(fill=tk.X)
        sb_inner = tk.Frame(search_bar, bg=LEATHER)
        sb_inner.pack(fill=tk.X, padx=12, pady=8)
        tk.Label(sb_inner, text="Search the Archive", bg=LEATHER, fg=BRASS,
                 font=('Georgia', 11, 'bold')).pack(side=tk.LEFT, padx=(0, 16))

        row1 = tk.Frame(sb_inner, bg=LEATHER)
        row1.pack(side=tk.LEFT, fill=tk.X)
        tk.Label(row1, text="Search:", bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 4))
        self.search_var = tk.StringVar()
        se = ttk.Entry(row1, textvariable=self.search_var, width=22)
        se.pack(side=tk.LEFT, padx=(0, 6))
        se.bind('<KeyRelease>', lambda e: self.apply_filters())
        ttk.Button(row1, text="Search", command=self.apply_filters).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(row1, text="Clear",  command=self.clear_filters).pack(side=tk.LEFT, padx=(0, 12))
        tk.Label(row1, text="Genre:", bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 2))
        self.genre_filter_var = tk.StringVar()
        gcb = ttk.Combobox(row1, textvariable=self.genre_filter_var,
                           values=["","Fantasy","Science Fiction","Mystery","Romance","Horror","Comedy","Drama","Thriller"],
                           width=12, state="readonly")
        gcb.pack(side=tk.LEFT, padx=(0, 8))
        gcb.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())
        tk.Label(row1, text="Model:", bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 2))
        self.model_filter_var = tk.StringVar()
        self.model_filter_combo = ttk.Combobox(row1, textvariable=self.model_filter_var, values=[""], width=12, state="readonly")
        self.model_filter_combo.pack(side=tk.LEFT, padx=(0, 8))
        self.model_filter_combo.bind('<<ComboboxSelected>>', lambda e: self.apply_filters())
        tk.Label(row1, text="Sort:", bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 2))
        self.sort_var = tk.StringVar(value="date_desc")
        ttk.Combobox(row1, textvariable=self.sort_var,
                     values=["date_desc","date_asc","words_desc","words_asc","model","rating_desc"],
                     width=10, state="readonly").pack(side=tk.LEFT, padx=(0, 8))
        self.min_words_var = tk.StringVar()
        self.max_words_var = tk.StringVar()
        self.min_rating_var = tk.StringVar(value="0")
        self.favorites_only_var = tk.BooleanVar(value=False)

        # Main content area
        content = tk.Frame(overlay, bg=DARK_BG)
        content.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Left — story list
        list_panel = tk.Frame(content, bg=LEATHER, width=380)
        list_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
        list_panel.pack_propagate(False)
        self.results_count_var = tk.StringVar(value="No stories loaded")
        tk.Label(list_panel, textvariable=self.results_count_var, bg=LEATHER,
                 fg=BRASS_DIM, font=('Segoe UI', 8), padx=8).pack(anchor=tk.W, pady=(6, 2))
        tk.Frame(list_panel, bg=BRASS, height=1).pack(fill=tk.X)
        lf = tk.Frame(list_panel, bg=LEATHER)
        lf.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.filtered_stories_listbox = tk.Listbox(lf, font=('Segoe UI', 9),
                                                    bg=PARCH_BG, fg=PARCH_FG,
                                                    selectbackground='#2A1E0A',
                                                    selectforeground='#F2E4C4',
                                                    relief='flat', borderwidth=0)
        self.filtered_stories_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.filtered_stories_listbox.bind('<<ListboxSelect>>', self.on_filtered_story_selected)
        sb2 = ttk.Scrollbar(lf, command=self.filtered_stories_listbox.yview)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)
        self.filtered_stories_listbox.config(yscrollcommand=sb2.set)
        bf = tk.Frame(list_panel, bg=LEATHER)
        bf.pack(fill=tk.X, pady=(4, 6), padx=6)
        ttk.Button(bf, text="Refresh",     command=self.refresh_saved_stories).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(bf, text="Open Folder", command=self.open_stories_folder).pack(side=tk.LEFT)

        # Brass divider
        tk.Frame(content, bg=BRASS, width=2).pack(side=tk.LEFT, fill=tk.Y)

        # Right — story view
        story_panel = tk.Frame(content, bg=LEATHER)
        story_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 0))
        self.saved_story_text = scrolledtext.ScrolledText(story_panel, wrap=tk.WORD, font=('Georgia', 10),
                                                           bg=PARCH_BG, fg='#C4A86A',
                                                           insertbackground=BRASS,
                                                           relief='flat', borderwidth=0)
        self.saved_story_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        meta_f = tk.Frame(story_panel, bg=LEATHER)
        meta_f.pack(fill=tk.X, padx=6, pady=(0, 4))
        self.metadata_var = tk.StringVar(value="Select a story to view details")
        tk.Label(meta_f, textvariable=self.metadata_var, wraplength=500,
                 justify=tk.LEFT, font=('Segoe UI', 8), bg=LEATHER, fg=BRASS_DIM).pack(anchor=tk.W)
        rating_f = tk.Frame(story_panel, bg=LEATHER)
        rating_f.pack(fill=tk.X, padx=6, pady=(0, 4))
        tk.Label(rating_f, text="Rating:", bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=(0, 4))
        self.rating_var = tk.StringVar(value="0")
        rcb2 = ttk.Combobox(rating_f, textvariable=self.rating_var,
                             values=["0 (Unrated)","1 *","2 **","3 ***","4 ****","5 *****"],
                             width=14, state="readonly")
        rcb2.pack(side=tk.LEFT, padx=(0, 10))
        rcb2.bind('<<ComboboxSelected>>', self.on_rating_changed)
        self.favorite_var = tk.BooleanVar(value=False)
        tk.Checkbutton(rating_f, text="Favourite", variable=self.favorite_var,
                       command=self.on_favorite_changed,
                       bg=LEATHER, fg=PARCH_FG, selectcolor=PARCH_BG,
                       activebackground=LEATHER, font=('Segoe UI', 9)).pack(side=tk.LEFT)
        action_f = tk.Frame(story_panel, bg=LEATHER)
        action_f.pack(fill=tk.X, padx=6, pady=(0, 4))
        def _ink(p, t, c, danger=False) -> Any:
            return tk.Button(p, text=t, command=c,
                             bg='#6A1A1A' if danger else '#1A1208',
                             fg='#F0C0C0' if danger else PARCH_FG,
                             font=('Segoe UI', 9), relief='flat', padx=10, pady=4,
                             activebackground='#8A2020' if danger else '#2A1E0A',
                             cursor='hand2', borderwidth=0)
        _ink(action_f, "Copy",   self.copy_saved_story).pack(side=tk.LEFT, padx=(0, 6))
        _ink(action_f, "Delete", self.delete_saved_story, danger=True).pack(side=tk.LEFT)
        exp_f = tk.Frame(story_panel, bg=LEATHER)
        exp_f.pack(fill=tk.X, padx=6, pady=(0, 6))
        tk.Label(exp_f, text="Export:", bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8, 'bold')).pack(side=tk.LEFT, padx=(0, 6))
        for txt, cmd in [("PDF", self.export_story_pdf), ("DOCX", self.export_story_docx), ("TXT", self.export_story_txt)]:
            _ink(exp_f, txt, cmd).pack(side=tk.LEFT, padx=(0, 4))

        self.refresh_saved_stories()
        self.update_model_filter_options()
        self.current_selected_filename = None

    # ── Handlers ──────────────────────────────────────────────────────────────

    def refresh_saved_stories(self) -> None:
        self.update_model_filter_options(); self.apply_filters()

    def update_model_filter_options(self) -> None:
        try:
            stories = self.app.stories_manager.get_all_stories_metadata()
            models = sorted({s['model'] for s in stories if s['model'] and s['model'] != 'Unknown'})
            self.model_filter_combo['values'] = [""] + models
        except Exception as e: logger.error(f"Error updating model filter: {e}")

    def apply_filters(self) -> None:
        try:
            search_term = self.search_var.get().strip() or None
            genre = self.genre_filter_var.get() or None; model = self.model_filter_var.get() or None
            sort_by = self.sort_var.get(); min_words = max_words = None
            try:
                if self.min_words_var.get().strip(): min_words = int(self.min_words_var.get())
                if self.max_words_var.get().strip(): max_words = int(self.max_words_var.get())
            except ValueError: pass
            min_rating = None
            try:
                rv = int(self.min_rating_var.get())
                if rv > 0: min_rating = rv
            except ValueError: pass
            favorites_only = self.favorites_only_var.get()
            filtered = self.app.stories_manager.filter_stories(
                search_term=search_term, genre=genre, model=model,
                min_words=min_words, max_words=max_words,
                min_rating=min_rating, favorites_only=favorites_only, sort_by=sort_by)
            self._last_filtered = filtered
            self.filtered_stories_listbox.delete(0, tk.END)
            for story in filtered:
                stars = "*" * story['rating'] if story['rating'] > 0 else ""
                fav = "[fav] " if story['favorite'] else ""
                dt = story['generated_date'].strftime(' %m/%d %H:%M') if story['generated_date'] else ""
                self.filtered_stories_listbox.insert(tk.END, f"{fav}{story['title']} ({story['word_count']}w) {stars}{dt}")
            n = len(filtered)
            self.results_count_var.set(f"Showing {n} {'tale' if n==1 else 'tales'}")
        except Exception as e:
            messagebox.showerror("Error", f"Filter failed: {e}")

    def clear_filters(self) -> None:
        self.search_var.set(""); self.genre_filter_var.set(""); self.model_filter_var.set("")
        self.min_words_var.set(""); self.max_words_var.set(""); self.min_rating_var.set("0")
        self.favorites_only_var.set(False); self.sort_var.set("date_desc")
        self.apply_filters()

    def on_filtered_story_selected(self, event) -> None:
        sel = self.filtered_stories_listbox.curselection()
        if not sel: return
        cached = getattr(self, '_last_filtered', [])
        if not cached or sel[0] >= len(cached): return
        selected = cached[sel[0]]
        if selected:
            self.current_selected_filename = selected['filename']
            content = self.app.stories_manager.load_story(selected['filename'])
            self.saved_story_text.delete("1.0", tk.END)
            self.saved_story_text.insert("1.0", content)
            parts = []
            if selected['generated_date']: parts.append(f"Date: {selected['generated_date'].strftime('%Y-%m-%d %H:%M')}")
            parts += [f"Model: {selected['model']}"]
            if selected['genre']: parts.append(f"Genre: {selected['genre']}")
            if selected['tone']:  parts.append(f"Tone: {selected['tone']}")
            parts.append(f"Words: {selected['word_count']}")
            self.metadata_var.set("  |  ".join(parts))
            self.rating_var.set(f"{selected['rating']} *" if selected['rating'] > 0 else "0 (Unrated)")
            self.favorite_var.set(selected['favorite'])

    def on_rating_changed(self, *args) -> None:
        if not self.current_selected_filename: return
        try:
            rating = int(self.rating_var.get().split()[0])
            self.app.stories_manager.set_rating(self.current_selected_filename, rating)
            self.apply_filters()
        except Exception as e: logger.error(f"Rating error: {e}")

    def on_favorite_changed(self) -> None:
        if not self.current_selected_filename: return
        try:
            self.app.stories_manager.set_favorite(self.current_selected_filename, self.favorite_var.get())
            self.apply_filters()
        except Exception as e: logger.error(f"Favourite error: {e}")

    def copy_saved_story(self) -> None:
        content = self.saved_story_text.get("1.0", tk.END).strip()
        if content:
            self.app.root.clipboard_clear(); self.app.root.clipboard_append(content)
            messagebox.showinfo("Copied", "Copied to clipboard!")

    def delete_saved_story(self) -> None:
        sel = self.filtered_stories_listbox.curselection()
        if not sel: messagebox.showwarning("Error", "Select a story first."); return
        display = self.filtered_stories_listbox.get(sel[0])
        title = display.split(' (')[0].replace("[fav] ", "").strip()
        filtered = self.app.stories_manager.filter_stories(sort_by=self.sort_var.get())
        selected = next((s for s in filtered if s['title'] == title), None)
        if selected and messagebox.askyesno("Confirm", f"Delete '{selected['title']}'?"):
            try:
                from pathlib import Path
                base = Path(self.app.stories_manager.STORIES_DIR).resolve()
                fp = Path(selected['filepath']).resolve()
                if fp.exists() and fp.is_relative_to(base):
                    fp.unlink(); messagebox.showinfo("Deleted", "Story deleted.")
                    self.refresh_saved_stories()
                else: messagebox.showerror("Error", "Invalid path.")
            except Exception as e: messagebox.showerror("Error", f"Delete failed: {e}")

    def export_story_pdf(self) -> None:
        if not self.current_selected_filename: messagebox.showwarning("Error", "Select a story first."); return
        try: messagebox.showinfo("Exported", f"PDF:\n{self.app.stories_manager.export_to_pdf(self.current_selected_filename)}")
        except Exception as e: messagebox.showerror("Error", f"PDF export failed: {e}")

    def export_story_docx(self) -> None:
        if not self.current_selected_filename: messagebox.showwarning("Error", "Select a story first."); return
        try: messagebox.showinfo("Exported", f"DOCX:\n{self.app.stories_manager.export_to_docx(self.current_selected_filename)}")
        except Exception as e: messagebox.showerror("Error", f"DOCX export failed: {e}")

    def export_story_txt(self) -> None:
        if not self.current_selected_filename: messagebox.showwarning("Error", "Select a story first."); return
        try: messagebox.showinfo("Exported", f"TXT:\n{self.app.stories_manager.export_to_txt(self.current_selected_filename)}")
        except Exception as e: messagebox.showerror("Error", f"TXT export failed: {e}")

    def open_stories_folder(self) -> None:
        import webbrowser; webbrowser.open(self.app.stories_manager.STORIES_DIR)
