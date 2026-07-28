"""
Novel tab — Long-form novel workshop with Story Bible, chapter generation,
and bible auto-update.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any
import threading
import os

from story_generator import NovelManager
from banned_content import validate_story
from theme import LEATHER, BRASS, BRASS_DIM, PARCH_BG, PARCH_FG, DARK_BG


class NovelTab:
    """Encapsulates the Novel tab UI and all novel-related handlers."""

    def __init__(self, app) -> None:
        self.app = app
        self._active_bible = None
        self._novel_list_cache: list = []
        self._novel_chapter_cache: list = []
        self._novel_is_generating = False
        self._novel_stop_event = threading.Event()
        self._build()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build(self) -> None:
        tab = tk.Frame(self.app.notebook, bg=DARK_BG)
        self.app.notebook.add(tab, text="Novel")
        canvas = tk.Canvas(tab, highlightthickness=0, bg=DARK_BG)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.app._apply_canvas_bg(canvas)
        overlay = tk.Frame(canvas, bg=DARK_BG)
        ow = canvas.create_window(0, 0, window=overlay, anchor='nw')
        canvas.bind('<Configure>', lambda e: (
            overlay.config(width=canvas.winfo_width(), height=canvas.winfo_height()),
            canvas.itemconfig(ow, width=canvas.winfo_width(), height=canvas.winfo_height())
        ))

        # ── Left panel — novel controls ───────────────────────────────────────
        left = tk.Frame(overlay, bg=LEATHER, width=280)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)
        tk.Frame(overlay, bg=BRASS, width=2).pack(side=tk.LEFT, fill=tk.Y)
        inner = tk.Frame(left, bg=LEATHER)
        inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(inner, text="The Grand Chronicle", bg=LEATHER, fg=BRASS,
                 font=('Georgia', 12, 'bold')).pack(anchor=tk.W, pady=(0, 2))
        tk.Label(inner, text="Long-form novel workshop", bg=LEATHER, fg=BRASS_DIM,
                 font=('Segoe UI', 8, 'italic')).pack(anchor=tk.W, pady=(0, 8))
        tk.Frame(inner, bg=BRASS, height=1).pack(fill=tk.X, pady=(0, 10))

        def sect(text) -> None:
            tk.Frame(inner, bg=BRASS, height=1).pack(fill=tk.X, pady=(10, 4))
            tk.Label(inner, text=text.upper(), bg=LEATHER, fg=BRASS,
                     font=('Segoe UI', 7, 'bold')).pack(anchor=tk.W)

        def lbl(text) -> None:
            tk.Label(inner, text=text, bg=LEATHER, fg=BRASS_DIM,
                     font=('Segoe UI', 8)).pack(anchor=tk.W, pady=(4, 0))

        # Novel selector / creator
        sect("Active Novel")
        self.novel_select_var = tk.StringVar()
        self.novel_select_combo = ttk.Combobox(inner, textvariable=self.novel_select_var,
                                                state="readonly")
        self.novel_select_combo.pack(fill=tk.X, pady=(4, 4))
        self.novel_select_combo.bind('<<ComboboxSelected>>', lambda e: self._load_selected())

        self._refresh_novel_list()

        tk.Button(inner, text="Refresh List", command=self._refresh_novel_list,
                  bg='#1A1208', fg=PARCH_FG, font=('Segoe UI', 8), relief='flat',
                  padx=8, pady=3, cursor='hand2', borderwidth=0).pack(fill=tk.X, pady=(0, 6))

        # New novel form
        sect("Create New Novel")
        lbl("Title:")
        self.novel_title_var = tk.StringVar()
        ttk.Entry(inner, textvariable=self.novel_title_var).pack(fill=tk.X, pady=(2, 4))
        lbl("Genre:")
        self.novel_genre_var = tk.StringVar()
        ttk.Combobox(inner, textvariable=self.novel_genre_var,
                     values=["Fantasy", "Science Fiction", "Mystery", "Romance",
                             "Horror", "Thriller", "Literary", "Adventure"]).pack(fill=tk.X, pady=(2, 4))
        lbl("Tone:")
        self.novel_tone_var = tk.StringVar()
        ttk.Combobox(inner, textvariable=self.novel_tone_var,
                     values=["Dark", "Lighthearted", "Serious", "Whimsical",
                             "Suspenseful", "Romantic", "Gritty", "Lyrical"]).pack(fill=tk.X, pady=(2, 4))
        lbl("Premise (one paragraph):")
        self.novel_premise_text = tk.Text(inner, height=4, wrap=tk.WORD,
                                           font=('Segoe UI', 9), relief='flat',
                                           bg=PARCH_BG, fg=PARCH_FG,
                                           insertbackground=BRASS,
                                           padx=6, pady=4, borderwidth=1,
                                           highlightthickness=1, highlightbackground=BRASS)
        self.novel_premise_text.pack(fill=tk.X, pady=(2, 6))

        tk.Button(inner, text="Create Novel", command=self._create_novel,
                  bg='#6A4A18', fg='#F2E4C4', font=('Segoe UI', 9, 'bold'),
                  relief='flat', padx=10, pady=5, activebackground='#8A6230',
                  cursor='hand2', borderwidth=0).pack(fill=tk.X, pady=(0, 4))

        # Model + chapter settings
        sect("Generation Settings")
        lbl("Model:")
        self.novel_model_var = tk.StringVar(value="llama2")
        self.novel_model_combo = ttk.Combobox(inner, textvariable=self.novel_model_var,
                                               state="readonly")
        self.novel_model_combo.pack(fill=tk.X, pady=(2, 4))
        self.novel_model_combo.bind("<Button-1>", lambda e: self._sync_models())

        lbl("Words per chapter:")
        self.novel_words_var = tk.IntVar(value=2000)
        ttk.Spinbox(inner, from_=500, to=6000, increment=500,
                    textvariable=self.novel_words_var).pack(fill=tk.X, pady=(2, 6))

        # Export
        sect("Export")
        tk.Button(inner, text="Export Full Novel (.txt)", command=self._export_novel,
                  bg='#1A1208', fg=PARCH_FG, font=('Segoe UI', 9), relief='flat',
                  padx=10, pady=5, activebackground='#2A1E0A',
                  cursor='hand2', borderwidth=0).pack(fill=tk.X, pady=(4, 0))

        self.novel_status_var = tk.StringVar(value="No novel loaded")
        tk.Label(inner, textvariable=self.novel_status_var, bg=LEATHER, fg=BRASS_DIM,
                 font=('Segoe UI', 8), wraplength=230).pack(anchor=tk.W, pady=(8, 0))

        # ── Right area ────────────────────────────────────────────────────────
        right = tk.Frame(overlay, bg=DARK_BG)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Header
        hdr = tk.Frame(right, bg=LEATHER)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Novel Workshop", bg=LEATHER, fg=BRASS,
                 font=('Georgia', 13, 'bold'), padx=12, pady=8).pack(side=tk.LEFT)
        tk.Frame(hdr, bg=BRASS, height=1).pack(side=tk.BOTTOM, fill=tk.X)

        # Paned: top=chapter list+controls, bottom=chapter text
        paned = tk.PanedWindow(right, orient=tk.VERTICAL,
                                bg=DARK_BG, sashwidth=6, sashrelief='flat')
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ── Top pane: chapter list + bible summary ────────────────────────────
        top_frame = tk.Frame(paned, bg=DARK_BG)
        paned.add(top_frame, minsize=180)

        # Chapter list (left of top pane)
        ch_panel = tk.Frame(top_frame, bg=LEATHER, width=320)
        ch_panel.pack(side=tk.LEFT, fill=tk.BOTH)
        ch_panel.pack_propagate(False)
        tk.Label(ch_panel, text="Chapters", bg=LEATHER, fg=BRASS,
                 font=('Segoe UI', 9, 'bold'), padx=8, pady=4).pack(anchor=tk.W)
        tk.Frame(ch_panel, bg=BRASS, height=1).pack(fill=tk.X, padx=8)
        ch_lf = tk.Frame(ch_panel, bg=LEATHER)
        ch_lf.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.novel_ch_listbox = tk.Listbox(ch_lf, bg=PARCH_BG, fg=PARCH_FG,
                                            font=('Segoe UI', 9), relief='flat',
                                            selectbackground='#2A1E0A',
                                            selectforeground='#F2E4C4',
                                            borderwidth=0)
        ch_sb = ttk.Scrollbar(ch_lf, command=self.novel_ch_listbox.yview)
        self.novel_ch_listbox.config(yscrollcommand=ch_sb.set)
        ch_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.novel_ch_listbox.pack(fill=tk.BOTH, expand=True)
        self.novel_ch_listbox.bind('<<ListboxSelect>>', self._chapter_selected)

        # Bible summary (right of top pane)
        tk.Frame(top_frame, bg=BRASS, width=2).pack(side=tk.LEFT, fill=tk.Y)
        bible_panel = tk.Frame(top_frame, bg=LEATHER)
        bible_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        bible_hdr = tk.Frame(bible_panel, bg=LEATHER)
        bible_hdr.pack(fill=tk.X)
        tk.Label(bible_hdr, text="Story Bible", bg=LEATHER, fg=BRASS,
                 font=('Segoe UI', 9, 'bold'), padx=8, pady=4).pack(side=tk.LEFT)
        ttk.Button(bible_hdr, text="Refresh",
                   command=self._refresh_bible_display).pack(side=tk.RIGHT, padx=6, pady=3)
        tk.Frame(bible_panel, bg=BRASS, height=1).pack(fill=tk.X, padx=8)
        bible_lf = tk.Frame(bible_panel, bg=LEATHER)
        bible_lf.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.novel_bible_text = tk.Text(bible_lf, wrap=tk.WORD,
                                         font=('Segoe UI', 9),
                                         bg=PARCH_BG, fg=PARCH_FG,
                                         state=tk.DISABLED, relief='flat',
                                         padx=8, pady=6, borderwidth=0)
        bsb = ttk.Scrollbar(bible_lf, command=self.novel_bible_text.yview)
        self.novel_bible_text.config(yscrollcommand=bsb.set)
        bsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.novel_bible_text.pack(fill=tk.BOTH, expand=True)

        # ── Bottom pane: chapter generation + text ────────────────────────────
        bot_frame = tk.Frame(paned, bg=DARK_BG)
        paned.add(bot_frame, minsize=280)

        # Chapter brief + generate controls
        ctrl = tk.Frame(bot_frame, bg=LEATHER)
        ctrl.pack(fill=tk.X)
        ctrl_inner = tk.Frame(ctrl, bg=LEATHER)
        ctrl_inner.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(ctrl_inner, text="Chapter Brief:", bg=LEATHER, fg=BRASS,
                 font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 6))
        self.novel_brief_var = tk.StringVar()
        tk.Entry(ctrl_inner, textvariable=self.novel_brief_var,
                 bg=PARCH_BG, fg=PARCH_FG, insertbackground=BRASS,
                 relief='flat', font=('Segoe UI', 9),
                 highlightthickness=1, highlightbackground=BRASS).pack(
                 side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        def _ink(t, c, accent=False, danger=False) -> Any:
            return tk.Button(ctrl_inner, text=t, command=c,
                             bg='#6A4A18' if accent else '#6A1A1A' if danger else '#1A1208',
                             fg='#F2E4C4' if accent else '#F0C0C0' if danger else PARCH_FG,
                             font=('Segoe UI', 9, 'bold' if accent else 'normal'),
                             relief='flat', padx=10, pady=4,
                             cursor='hand2', borderwidth=0)

        self.novel_gen_btn = _ink("Generate Next Chapter", self._generate_chapter, accent=True)
        self.novel_gen_btn.pack(side=tk.LEFT, padx=(0, 4))
        self.novel_stop_btn = _ink("Stop", self._stop, danger=True)
        # not packed yet
        tk.Frame(ctrl, bg=BRASS, height=1).pack(fill=tk.X)

        # Bible update progress
        self.novel_update_var = tk.StringVar(value="")
        tk.Label(bot_frame, textvariable=self.novel_update_var, bg=DARK_BG, fg=BRASS_DIM,
                 font=('Segoe UI', 8)).pack(anchor=tk.W, padx=10)

        # Chapter text display
        txt_frame = tk.Frame(bot_frame, bg=DARK_BG)
        txt_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))
        self.novel_ch_text = tk.Text(txt_frame, wrap=tk.WORD,
                                      font=('Georgia', 11),
                                      bg='#16100A', fg=PARCH_FG,
                                      insertbackground=BRASS,
                                      relief='flat', padx=12, pady=8,
                                      borderwidth=0)
        txt_sb = ttk.Scrollbar(txt_frame, command=self.novel_ch_text.yview)
        self.novel_ch_text.config(yscrollcommand=txt_sb.set)
        txt_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.novel_ch_text.pack(fill=tk.BOTH, expand=True)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _refresh_novel_list(self) -> None:
        novels = self.app.novel_manager.list_novels()
        self.novel_select_combo['values'] = [
            f"{n['slug']} | {n['title']} ({n['chapter_count']} ch)" for n in novels
        ]
        self._novel_list_cache = novels

    def _create_novel(self) -> None:
        title = self.novel_title_var.get().strip()
        genre = self.novel_genre_var.get().strip()
        tone = self.novel_tone_var.get().strip()
        premise = self.novel_premise_text.get("1.0", tk.END).strip()
        if not title:
            messagebox.showwarning("Missing", "Enter a title first.")
            return
        bible = self.app.novel_manager.create_novel(title, genre, tone, premise)
        self._active_bible = bible
        self._refresh_novel_list()
        self._refresh_ui()
        self.novel_status_var.set(f"Created: {title}")

    def _export_novel(self) -> None:
        if not self._active_bible:
            messagebox.showwarning("No novel", "Load or create a novel first.")
            return
        try:
            path = self.app.novel_manager.export_novel_txt(self._active_bible)
            self.novel_status_var.set(f"Exported: {os.path.basename(path)}")
            os.startfile(os.path.dirname(path))
        except Exception as ex:
            messagebox.showerror("Export failed", str(ex))

    def _sync_models(self) -> None:
        vals = self.app.model_combo['values'] if hasattr(self.app, 'model_combo') else []
        if vals:
            self.novel_model_combo['values'] = vals
            if not self.novel_model_var.get() or self.novel_model_var.get() not in vals:
                self.novel_model_var.set(vals[0])

    def _load_selected(self) -> None:
        idx = self.novel_select_combo.current()
        if idx < 0 or idx >= len(self._novel_list_cache):
            return
        novel = self._novel_list_cache[idx]
        try:
            self._active_bible = self.app.novel_manager.load_novel(novel['slug'])
            self._refresh_ui()
            self.novel_status_var.set(f"Loaded: {novel['title']}")
        except Exception as e:
            self.novel_status_var.set(f"Error: {e}")

    def _refresh_ui(self) -> None:
        self._refresh_chapter_list()
        self._refresh_bible_display()

    def _refresh_chapter_list(self) -> None:
        self.novel_ch_listbox.delete(0, tk.END)
        if not self._active_bible:
            return
        chapters = self.app.novel_manager.list_chapters(self._active_bible)
        self._novel_chapter_cache = chapters
        for ch in chapters:
            self.novel_ch_listbox.insert(
                tk.END,
                f"Ch {ch['num']:02d}  {ch['title'][:35]}  ({ch['word_count']}w)"
            )

    def _refresh_bible_display(self) -> None:
        self.novel_bible_text.config(state=tk.NORMAL)
        self.novel_bible_text.delete("1.0", tk.END)
        if self._active_bible:
            self.novel_bible_text.insert("1.0",
                self._active_bible.render_for_context(max_chars=8000))
        self.novel_bible_text.config(state=tk.DISABLED)

    def _chapter_selected(self, event=None) -> None:
        sel = self.novel_ch_listbox.curselection()
        if not sel or not self._active_bible:
            return
        idx = sel[0]
        if idx >= len(self._novel_chapter_cache):
            return
        ch = self._novel_chapter_cache[idx]
        text = self.app.novel_manager.load_chapter(self._active_bible, ch['num'])
        self.novel_ch_text.delete("1.0", tk.END)
        self.novel_ch_text.insert("1.0", text)

    def _stop(self) -> None:
        self._novel_stop_event.set()
        self.novel_status_var.set("Stopping...")

    def _generate_chapter(self) -> None:
        if not self._active_bible:
            messagebox.showwarning("No novel", "Create or load a novel first.")
            return
        if self._novel_is_generating:
            return
        model = self.novel_model_var.get()
        word_count = self.novel_words_var.get()
        brief = self.novel_brief_var.get().strip()
        chapter_num = self._active_bible.get("chapter_count", 0) + 1

        if not model:
            messagebox.showwarning("No model", "Select a model first.")
            return
        if not brief:
            messagebox.showwarning("No brief", "Enter a chapter brief first.")
            return

        self._novel_is_generating = True
        self._novel_stop_event.clear()
        self.novel_gen_btn.pack_forget()
        self.novel_stop_btn.pack(side=tk.LEFT, padx=(0, 4))
        self.novel_status_var.set(f"Writing Chapter {chapter_num}...")
        self.novel_update_var.set("")

        # Clear text area for new chapter
        self.novel_ch_text.delete("1.0", tk.END)

        full_text: list = []
        root = self.app.root

        def _generate() -> None:
            try:
                prompt = NovelManager.build_chapter_prompt(
                    self._active_bible, chapter_num, brief, word_count
                )
                for chunk in self.app.generator.generate_story_streaming(
                    model, custom_prompt=prompt
                ):
                    if self._novel_stop_event.is_set():
                        break
                    full_text.append(chunk)
                    root.after(0, lambda c=chunk: (
                        self.novel_ch_text.insert(tk.END, c),
                        self.novel_ch_text.see(tk.END)
                    ))

                chapter_text = "".join(full_text)

                # Save the chapter
                self.app.novel_manager.save_chapter(
                    self._active_bible, chapter_num, chapter_text
                )
                root.after(0, lambda: self.novel_status_var.set(
                    f"Chapter {chapter_num} written ({len(chapter_text.split())} words). Updating bible..."
                ))

                # Extract bible update
                if not self._novel_stop_event.is_set() and chapter_text.strip():
                    root.after(0, lambda: self.novel_update_var.set(
                        "Extracting new facts for Story Bible..."
                    ))
                    try:
                        update_prompt = NovelManager.build_bible_update_prompt(
                            self._active_bible, chapter_num, chapter_text
                        )
                        update_response, _ = self.app.generator.generate_story(
                            model, custom_prompt=update_prompt
                        )
                        added = NovelManager.apply_bible_update(
                            self._active_bible, chapter_num, update_response
                        )
                        summary = ", ".join(added[:5]) if added else "No new facts"
                        root.after(0, lambda s=summary: self.novel_update_var.set(
                            f"Bible updated: {s}"
                        ))
                        root.after(0, self._refresh_bible_display)
                    except Exception as ex:
                        root.after(0, lambda e=ex: self.novel_update_var.set(
                            f"Bible update skipped: {e}"
                        ))

                root.after(0, self._refresh_chapter_list)
                root.after(0, lambda: self.novel_brief_var.set(""))

                # Validate chapter against constitution
                ch_report = validate_story(chapter_text)
                if ch_report["clean"]:
                    root.after(0, lambda: self.novel_status_var.set(
                        f"Chapter {chapter_num} complete. ({len(chapter_text.split())} words) No violations."
                    ))
                else:
                    v_count = ch_report["total_violations"]
                    root.after(0, lambda vc=v_count: self.novel_status_var.set(
                        f"Chapter {chapter_num} complete. ({len(chapter_text.split())} words) {vc} violation(s) detected."
                    ))
                    root.after(0, lambda r=ch_report: self.app._show_validation_report(r))

            except Exception as e:
                root.after(0, lambda err=e: self.novel_status_var.set(f"Error: {err}"))
            finally:
                self._novel_is_generating = False
                self._novel_stop_event.clear()
                root.after(0, lambda: self.novel_stop_btn.pack_forget())
                root.after(0, lambda: self.novel_gen_btn.pack(side=tk.LEFT, padx=(0, 4)))

        threading.Thread(target=_generate, daemon=True).start()
