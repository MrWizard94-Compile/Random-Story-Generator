"""
Generate tab — Single story generation with streaming output on a parchment scroll.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any
import threading
import os

from story_generator import (
    StoryGenerator, DEFAULT_WORD_COUNT, SPINBOX_MIN_WORDS, SPINBOX_MAX_WORDS
)
from banned_content import validate_story
from theme import LEATHER, BRASS, BRASS_DIM, PARCH_BG, PARCH_FG, DARK_BG


class GenerateTab:
    """Encapsulates the Generate (single story) tab UI and handlers."""

    def __init__(self, app, scroll_canvas_class) -> None:
        self.app = app
        self.ScrollCanvas = scroll_canvas_class
        self._build()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build(self) -> None:
        tab = ttk.Frame(self.app.notebook)
        self.app.notebook.add(tab, text="Generate")
        self._tab_canvas = tk.Canvas(tab, highlightthickness=0, bg=DARK_BG)
        self._tab_canvas.pack(fill=tk.BOTH, expand=True)
        left = tk.Frame(self._tab_canvas, width=295, bg=LEATHER)
        left.pack_propagate(False)
        inner = tk.Frame(left, bg=LEATHER)
        inner.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        def grimoire_section(parent, text) -> None:
            tk.Frame(parent, bg=BRASS, height=1).pack(fill=tk.X, pady=(12, 4))
            tk.Label(parent, text=text.upper(), bg=LEATHER, fg=BRASS, font=('Segoe UI', 7, 'bold')).pack(anchor=tk.W)

        def grimoire_field(parent, label, widget_factory) -> Any:
            tk.Label(parent, text=label, bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8)).pack(anchor=tk.W, pady=(6, 0))
            w = widget_factory(parent); w.pack(fill=tk.X, pady=(2, 0)); return w

        tk.Label(inner, text="The Tome of Tales", bg=LEATHER, fg=BRASS, font=('Georgia', 13, 'bold')).pack(anchor=tk.W, pady=(2, 0))
        tk.Label(inner, text="Configure your story below", bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8, 'italic')).pack(anchor=tk.W, pady=(0, 2))

        grimoire_section(inner, "Scribe")
        self.model_var = tk.StringVar(value="llama2")
        self.model_combo = grimoire_field(inner, "Writing Spirit (Model)",
                           lambda p: ttk.Combobox(p, textvariable=self.model_var, state="readonly"))
        ttk.Button(inner, text="Summon Models", command=self.app.refresh_models).pack(fill=tk.X, pady=(5, 0))

        grimoire_section(inner, "Story Nature")
        self.genre_var = tk.StringVar()
        grimoire_field(inner, "Realm (Genre)",
                       lambda p: ttk.Combobox(p, textvariable=self.genre_var,
                                              values=["Fantasy","Science Fiction","Mystery","Romance","Horror","Comedy","Drama","Thriller"]))
        self.tone_var = tk.StringVar()
        grimoire_field(inner, "Mood (Tone)",
                       lambda p: ttk.Combobox(p, textvariable=self.tone_var,
                                              values=["Dark","Lighthearted","Serious","Whimsical","Suspenseful","Romantic"]))
        self.template_var = tk.StringVar(value="None")
        grimoire_field(inner, "Story Structure",
                       lambda p: ttk.Combobox(p, textvariable=self.template_var,
                                              values=["None","Hero's Journey","Three-Act Structure","Five-Act Structure","Character Arc","Mystery Detective"],
                                              state="readonly"))
        self.word_count_var = tk.IntVar(value=DEFAULT_WORD_COUNT)
        grimoire_field(inner, "Length (Words)",
                       lambda p: ttk.Spinbox(p, from_=SPINBOX_MIN_WORDS, to=SPINBOX_MAX_WORDS, textvariable=self.word_count_var))

        grimoire_section(inner, "Incantation")
        tk.Label(inner, text="Whisper your intent to the scribe...", bg=LEATHER, fg=BRASS_DIM,
                 font=('Segoe UI', 8, 'italic'), wraplength=255).pack(anchor=tk.W, pady=(0, 3))
        self.custom_prompt = tk.Text(inner, height=6, wrap=tk.WORD, font=('Segoe UI', 9), relief='flat',
                                     bg=PARCH_BG, fg=PARCH_FG, insertbackground=BRASS,
                                     selectbackground='#2A1E0A', padx=8, pady=6, borderwidth=1,
                                     highlightthickness=1, highlightbackground=BRASS)
        self.custom_prompt.pack(fill=tk.X, pady=(0, 8))
        self.generate_btn = tk.Button(inner, text="Inscribe the Story", command=self.generate_single_story,
                                      bg='#6A4A18', fg='#F2E4C4', font=('Segoe UI', 10, 'bold'),
                                      relief='flat', pady=8, activebackground='#8A6230',
                                      activeforeground='#FFF8E8', cursor='hand2', borderwidth=0)
        self.generate_btn.pack(fill=tk.X, pady=(2, 0))

        self.stop_btn = tk.Button(
            inner, text="Stop Inscribing",
            command=self._stop_generation,
            bg='#6A1A1A', fg='#F0C0C0',
            font=('Segoe UI', 10, 'bold'),
            relief='flat', pady=8,
            activebackground='#8A2020',
            activeforeground='#FFE0E0',
            cursor='hand2', borderwidth=0
        )
        # not packed yet -- only shown during generation

        brass_sep = tk.Frame(self._tab_canvas, width=2, bg=BRASS)
        scroll_container = tk.Frame(self._tab_canvas, bg=DARK_BG)
        hdr = tk.Frame(scroll_container, bg=DARK_BG)
        hdr.pack(fill=tk.X, pady=(0, 6))
        tk.Label(hdr, text="The Unwritten Scroll", bg=DARK_BG, fg='#C4953A',
                 font=('Georgia', 13, 'bold')).pack(side=tk.LEFT)
        self.scroll_canvas = self.ScrollCanvas(scroll_container, self.app.C)
        self.scroll_canvas.pack(fill=tk.BOTH, expand=True)
        self.story_text = self.scroll_canvas.text_widget
        self._story_has_placeholder = True
        btn_row = tk.Frame(scroll_container, bg=DARK_BG)
        btn_row.pack(fill=tk.X, pady=(8, 0))

        def _ink_btn(parent, text, cmd) -> Any:
            return tk.Button(parent, text=text, command=cmd, bg='#1A1208', fg='#C4A86A',
                             font=('Segoe UI', 9), relief='flat', padx=14, pady=5,
                             activebackground='#2A1E0A', activeforeground='#F2E4C4',
                             cursor='hand2', borderwidth=0)

        _ink_btn(btn_row, "Save to Archive", self.save_single_story).pack(side=tk.LEFT, padx=(0, 8))
        _ink_btn(btn_row, "Copy Scroll",     self.copy_story).pack(side=tk.LEFT, padx=(0, 8))
        _ink_btn(btn_row, "Clear",           self.clear_story).pack(side=tk.LEFT)

        left_win  = self._tab_canvas.create_window(0, 0, window=left, anchor='nw')
        sep_win   = self._tab_canvas.create_window(295, 0, window=brass_sep, anchor='nw')
        right_win = self._tab_canvas.create_window(297, 0, window=scroll_container, anchor='nw')
        self._tab_bg_img_ref = None

        def _on_tab_resize(event=None) -> None:
            w = self._tab_canvas.winfo_width(); h = self._tab_canvas.winfo_height()
            if w < 10 or h < 10: return
            left.config(height=h); brass_sep.config(height=h)
            right_w = max(100, w - 297)
            self._tab_canvas.itemconfig(left_win, height=h)
            self._tab_canvas.itemconfig(sep_win, height=h)
            self._tab_canvas.itemconfig(right_win, width=right_w, height=h)
            scroll_container.config(width=right_w, height=h)
            if hasattr(self.app, '_bg_pil') and self.app._bg_pil:
                try:
                    from PIL import ImageTk
                    try:    rs = __import__('PIL').Image.Resampling.LANCZOS
                    except: rs = __import__('PIL').Image.LANCZOS
                    bg_img = self.app._bg_pil.resize((w, h), rs)
                    self._tab_bg_img_ref = ImageTk.PhotoImage(bg_img)
                    self._tab_canvas.delete('tab_bg')
                    self._tab_canvas.create_image(0, 0, image=self._tab_bg_img_ref, anchor='nw', tags='tab_bg')
                    self._tab_canvas.tag_lower('tab_bg')
                except Exception: pass

        self._tab_canvas.bind('<Configure>', _on_tab_resize)

        # Bridge: cross-tab access to Generate's widgets
        self.app.model_var = self.model_var
        self.app.model_combo = self.model_combo
        self.app.genre_var = self.genre_var
        self.app.tone_var = self.tone_var
        self.app.template_var = self.template_var
        self.app.word_count_var = self.word_count_var
        self.app.custom_prompt = self.custom_prompt
        self.app.story_text = self.story_text
        self.app.scroll_canvas = self.scroll_canvas
        self.app.generate_btn = self.generate_btn
        self.app.stop_btn = self.stop_btn
        self.app._story_has_placeholder = self._story_has_placeholder

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _stop_generation(self) -> None:
        self.app._stop_event.set()
        self.app.status_var.set("Stopping...")

    def generate_single_story(self) -> None:
        if self.app.is_generating:
            messagebox.showwarning("Busy", "Already generating. Please wait."); return
        model = self.model_var.get()
        if not model:
            messagebox.showerror("Error", "Please select a model."); return
        def generate() -> None:
            self.app.is_generating = True
            self.app._stop_event.clear()
            self.generate_btn.config(state=tk.DISABLED)
            self.app.status_var.set(f"Generating with {model}...")
            self._story_has_placeholder = False
            self.app._story_has_placeholder = False
            self.app.root.after(0, lambda: self.generate_btn.pack_forget())
            self.app.root.after(0, lambda: self.stop_btn.pack(fill=tk.X, pady=(2, 0)))
            self.scroll_canvas._placeholder = False
            self.app.root.after(0, lambda: (self.story_text.delete("1.0", tk.END), self.story_text.config(fg='#3A2410')))
            try:
                genre = self.genre_var.get() or None; tone = self.tone_var.get() or None
                template = self.template_var.get() or "None"
                wc_raw = self.word_count_var.get()
                try:
                    word_count = int(str(wc_raw).strip())
                    if word_count <= 0: raise ValueError
                except (ValueError, TypeError): word_count = DEFAULT_WORD_COUNT
                custom_prompt = self.custom_prompt.get("1.0", tk.END).strip() or None
                collected_chunks = []
                for chunk in self.app.generator.generate_story_streaming(model, genre, tone, word_count, custom_prompt, template):
                    if self.app._stop_event.is_set():
                        break
                    collected_chunks.append(chunk)
                    self.app.root.after(0, lambda c=chunk: self._append_to_story(c))
                if self.app._stop_event.is_set():
                    self.app.root.after(0, lambda: self.app.status_var.set("Generation stopped."))
                else:
                    full_text = "".join(collected_chunks)
                    report = validate_story(full_text)
                    if report["clean"]:
                        self.app.root.after(0, lambda: self.app.status_var.set("Story inscribed. No violations found."))
                    else:
                        msg = f"Story inscribed with {report['total_violations']} violation(s) detected."
                        self.app.root.after(0, lambda m=msg: self.app.status_var.set(m))
                        self.app.root.after(0, lambda r=report: self._show_validation_report(r))
            except Exception as e:
                self.app.root.after(0, lambda err=e: messagebox.showerror("Error", f"Failed: {err}"))
            finally:
                self.app.is_generating = False
                self.app._stop_event.clear()
                self.app.root.after(0, lambda: self.stop_btn.pack_forget())
                self.app.root.after(0, lambda: self.generate_btn.pack(fill=tk.X, pady=(2, 0)))
                self.app.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL))
                self.app.root.after(2000, lambda: self.app.status_var.set("Ready"))
        threading.Thread(target=generate, daemon=True).start()

    def _display_story(self, story) -> None:
        self._story_has_placeholder = False
        self.app._story_has_placeholder = False
        self.scroll_canvas._placeholder = False
        self.story_text.config(fg='#3A2410')
        self.story_text.delete("1.0", tk.END)
        self.story_text.insert("1.0", story)

    def _append_to_story(self, chunk) -> None:
        self.story_text.insert(tk.END, chunk); self.story_text.see(tk.END)

    def _show_validation_report(self, report) -> None:
        """Show a popup with constitution violation details."""
        if report["clean"]:
            return
        win = tk.Toplevel(self.app.root)
        win.title("Constitution Violations Detected")
        win.geometry("520x400")
        win.configure(bg=LEATHER)
        win.transient(self.app.root)

        tk.Label(win, text="Story Validation Report",
                 bg=LEATHER, fg=BRASS, font=('Georgia', 13, 'bold')).pack(pady=(12, 4))

        summary = f"{report['total_violations']} violation(s) found"
        if report['high_severity_count'] > 0:
            summary += f"  ({report['high_severity_count']} high severity)"
        tk.Label(win, text=summary, bg=LEATHER, fg='#C07040',
                 font=('Segoe UI', 10)).pack(pady=(0, 8))

        tk.Frame(win, bg=BRASS, height=1).pack(fill=tk.X, padx=16)

        text_frame = tk.Frame(win, bg=LEATHER)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        txt = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 9),
                      bg=PARCH_BG, fg=PARCH_FG, relief='flat',
                      insertbackground=BRASS, padx=10, pady=8)
        sb = tk.Scrollbar(text_frame, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        txt.tag_configure("high", foreground="#E05050", font=('Consolas', 9, 'bold'))
        txt.tag_configure("medium", foreground="#C08040")
        txt.tag_configure("low", foreground="#808060")

        for v in report["violations"]:
            sev = v["severity"]
            cat_label = v["category"].replace("_", " ").upper()
            line = f"[{sev.upper()}] {cat_label}: {v['item']}"
            if v["count"] > 1:
                line += f"  (x{v['count']})"
            txt.insert(tk.END, line + "\n", sev)

        txt.configure(state=tk.DISABLED)

        btn_frame = tk.Frame(win, bg=LEATHER)
        btn_frame.pack(fill=tk.X, padx=16, pady=(0, 12))
        ttk.Button(btn_frame, text="Dismiss", command=win.destroy,
                   style='TButton').pack(side=tk.RIGHT)

    def save_single_story(self) -> None:
        story = self.story_text.get("1.0", tk.END).strip()
        ph = self._story_has_placeholder or self.scroll_canvas._placeholder
        if not story or ph:
            messagebox.showwarning("Empty", "No story to save."); return
        filename = filedialog.asksaveasfilename(defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
            initialdir=self.app.stories_manager.STORIES_DIR)
        if filename:
            try:
                self.app.stories_manager.save_story(story, self.model_var.get(),
                                                self.genre_var.get() or None, self.tone_var.get() or None,
                                                os.path.basename(filename))
                messagebox.showinfo("Saved", "Story saved to the archive!")
                self.app.refresh_saved_stories()
            except Exception as e: messagebox.showerror("Error", f"Failed: {e}")

    def copy_story(self) -> None:
        story = self.story_text.get("1.0", tk.END).strip()
        ph = self._story_has_placeholder or self.scroll_canvas._placeholder
        if story and not ph:
            self.app.root.clipboard_clear(); self.app.root.clipboard_append(story)
            messagebox.showinfo("Copied", "Scroll copied to clipboard!")

    def clear_story(self) -> None:
        self.scroll_canvas.restore_placeholder()
        self._story_has_placeholder = True
        self.app._story_has_placeholder = True
