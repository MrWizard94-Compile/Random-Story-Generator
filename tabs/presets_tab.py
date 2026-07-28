"""
Presets tab — Manage story generation presets and apply them to the Generate tab.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any

from story_generator import DEFAULT_WORD_COUNT
from theme import LEATHER, BRASS, BRASS_DIM, PARCH_BG, PARCH_FG, DARK_BG


class PresetsTab:
    """Encapsulates the Presets tab UI and handlers."""

    def __init__(self, app) -> None:
        self.app = app
        self._build()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build(self) -> None:
        tab = tk.Frame(self.app.notebook, bg=DARK_BG)
        self.app.notebook.add(tab, text="Presets")
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

        left = tk.Frame(main, bg=LEATHER, width=280)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
        left.pack_propagate(False)
        tk.Label(left, text="Spell Presets", bg=LEATHER, fg=BRASS,
                 font=('Georgia', 12, 'bold'), padx=8).pack(anchor=tk.W, pady=(8, 4))
        tk.Frame(left, bg=BRASS, height=1).pack(fill=tk.X, padx=8)
        lf = tk.Frame(left, bg=LEATHER)
        lf.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.presets_listbox = tk.Listbox(lf, font=('Segoe UI', 9),
                                           bg=PARCH_BG, fg=PARCH_FG, relief='flat',
                                           selectbackground='#2A1E0A', selectforeground='#F2E4C4',
                                           borderwidth=0)
        self.presets_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.presets_listbox.bind('<<ListboxSelect>>', self.on_preset_selected)
        sb3 = ttk.Scrollbar(lf, command=self.presets_listbox.yview)
        sb3.pack(side=tk.RIGHT, fill=tk.Y)
        self.presets_listbox.config(yscrollcommand=sb3.set)
        cf = tk.Frame(left, bg=LEATHER)
        cf.pack(fill=tk.X, padx=8, pady=(0, 8))
        def _ink(p, t, c, danger=False) -> Any:
            return tk.Button(p, text=t, command=c,
                             bg='#6A1A1A' if danger else '#1A1208',
                             fg='#F0C0C0' if danger else PARCH_FG,
                             font=('Segoe UI', 9), relief='flat', padx=10, pady=4,
                             activebackground='#8A2020' if danger else '#2A1E0A',
                             cursor='hand2', borderwidth=0)
        _ink(cf, "New",  self.create_new_preset).pack(side=tk.LEFT, padx=(0, 4))
        _ink(cf, "Edit", self.edit_preset).pack(side=tk.LEFT, padx=(0, 4))
        _ink(cf, "Del",  self.delete_preset, danger=True).pack(side=tk.LEFT)

        tk.Frame(main, bg=BRASS, width=2).pack(side=tk.LEFT, fill=tk.Y)

        right = tk.Frame(main, bg=LEATHER)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2, 0))
        tk.Label(right, text="Preset Details", bg=LEATHER, fg=BRASS,
                 font=('Georgia', 12, 'bold'), padx=8).pack(anchor=tk.W, pady=(8, 4))
        tk.Frame(right, bg=BRASS, height=1).pack(fill=tk.X, padx=8)
        details = tk.Frame(right, bg=LEATHER)
        details.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        rows = [("Name:","preset_name_var"),("Genre:","preset_genre_var"),
                ("Tone:","preset_tone_var"),("Words:","preset_words_var"),("Prompt:","preset_prompt_var")]
        for i, (lbl_txt, attr) in enumerate(rows):
            tk.Label(details, text=lbl_txt, bg=LEATHER, fg=BRASS, font=('Segoe UI', 9, 'bold')
                     ).grid(row=i, column=0, sticky=tk.NW, pady=4, padx=(0, 10))
            var = tk.StringVar(value="--")
            setattr(self, attr, var)
            tk.Label(details, textvariable=var, wraplength=400, justify=tk.LEFT,
                     bg=LEATHER, fg=PARCH_FG, font=('Segoe UI', 9)
                     ).grid(row=i, column=1, sticky=tk.W, pady=4)
        af = tk.Frame(details, bg=LEATHER)
        af.grid(row=len(rows), column=0, columnspan=2, pady=(16, 0), sticky=tk.W)
        tk.Button(af, text="Apply to Generate", command=self.apply_preset_to_generate,
                  bg='#6A4A18', fg='#F2E4C4', font=('Segoe UI', 9, 'bold'), relief='flat',
                  padx=12, pady=5, activebackground='#8A6230', cursor='hand2',
                  borderwidth=0).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(af, text="Refresh", command=self.refresh_presets).pack(side=tk.LEFT)
        self.refresh_presets()

    # ── Handlers ──────────────────────────────────────────────────────────────

    def refresh_presets(self) -> None:
        self.presets_listbox.delete(0, tk.END)
        presets = self.app.presets_manager.get_presets()
        if not presets:
            self.presets_listbox.insert(tk.END, "No presets yet")
            self.presets_listbox.config(state=tk.DISABLED)
        else:
            self.presets_listbox.config(state=tk.NORMAL)
            for p in presets:
                self.presets_listbox.insert(tk.END, p['name'] + (f" ({p['genre']})" if p.get('genre') else ""))

    def on_preset_selected(self, event) -> None:
        sel = self.presets_listbox.curselection()
        if not sel: return
        p = self.app.presets_manager.get_preset(self.presets_listbox.get(sel[0]).split(' (')[0])
        if p:
            self.preset_name_var.set(p['name']); self.preset_genre_var.set(p.get('genre') or '--')
            self.preset_tone_var.set(p.get('tone') or '--')
            self.preset_words_var.set(str(p.get('word_count', DEFAULT_WORD_COUNT)))
            self.preset_prompt_var.set(p.get('custom_prompt') or '--')

    def create_new_preset(self) -> None:
        d = PresetDialog(self.app.root, "Create Preset", self.app.presets_manager)
        self.app.root.wait_window(d.top)
        if d.result: self.refresh_presets(); messagebox.showinfo("Created", f"Preset '{d.result['name']}' created!")

    def edit_preset(self) -> None:
        sel = self.presets_listbox.curselection()
        if not sel: messagebox.showwarning("Error", "Select a preset first."); return
        p = self.app.presets_manager.get_preset(self.presets_listbox.get(sel[0]).split(' (')[0])
        if p:
            d = PresetDialog(self.app.root, "Edit Preset", self.app.presets_manager, p)
            self.app.root.wait_window(d.top)
            if d.result: self.refresh_presets(); messagebox.showinfo("Updated", f"Preset '{d.result['name']}' updated!")

    def delete_preset(self) -> None:
        sel = self.presets_listbox.curselection()
        if not sel: messagebox.showwarning("Error", "Select a preset first."); return
        name = self.presets_listbox.get(sel[0]).split(' (')[0]
        if messagebox.askyesno("Confirm", f"Delete preset '{name}'?"):
            if self.app.presets_manager.delete_preset(name): self.refresh_presets()
            else: messagebox.showerror("Error", "Delete failed.")

    def apply_preset_to_generate(self) -> None:
        sel = self.presets_listbox.curselection()
        if not sel: messagebox.showwarning("Error", "Select a preset first."); return
        p = self.app.presets_manager.get_preset(self.presets_listbox.get(sel[0]).split(' (')[0])
        if p:
            self.app.notebook.select(0)
            if p.get('genre'):       self.app.genre_var.set(p['genre'])
            if p.get('tone'):        self.app.tone_var.set(p['tone'])
            if p.get('word_count'):  self.app.word_count_var.set(p['word_count'])
            if p.get('custom_prompt'):
                self.app.custom_prompt.delete(1.0, tk.END); self.app.custom_prompt.insert(1.0, p['custom_prompt'])
            messagebox.showinfo("Applied", f"Preset '{p['name']}' applied!")


class PresetDialog:
    """Dialog for creating/editing a story generation preset."""

    def __init__(self, parent, title, presets_manager, preset=None) -> None:
        self.top = tk.Toplevel(parent); self.top.title(title)
        self.top.geometry("480x440"); self.top.resizable(False, False)
        self.top.transient(parent); self.top.grab_set()
        self.top.configure(bg=LEATHER)
        self.top.geometry(f"+{parent.winfo_rootx()+60}+{parent.winfo_rooty()+60}")
        self.presets_manager = presets_manager; self.preset = preset; self.result = None
        main = tk.Frame(self.top, bg=LEATHER, padx=20, pady=20)
        main.pack(fill=tk.BOTH, expand=True)
        tk.Label(main, text=title, bg=LEATHER, fg=BRASS, font=('Georgia', 13, 'bold')).pack(pady=(0, 4))
        tk.Frame(main, bg=BRASS, height=1).pack(fill=tk.X, pady=(0, 14))

        def field(lbl, var, values=None, height=None) -> Any:
            tk.Label(main, text=lbl, bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8, 'bold')).pack(anchor=tk.W)
            if height:
                w = tk.Text(main, height=height, width=48, font=('Segoe UI', 9),
                            bg=PARCH_BG, fg=PARCH_FG, relief='flat', padx=6, pady=4,
                            insertbackground=BRASS, borderwidth=1, highlightthickness=1,
                            highlightbackground=BRASS)
                w.pack(fill=tk.X, pady=(2, 8)); return w
            if values is not None:
                w = ttk.Combobox(main, textvariable=var, values=values, width=46)
            else:
                w = ttk.Entry(main, textvariable=var, width=48)
            w.pack(fill=tk.X, pady=(2, 8)); return w

        self.name_var = tk.StringVar(value=preset['name'] if preset else "")
        field("Preset Name *", self.name_var).focus()
        self.genre_var = tk.StringVar(value=preset.get('genre','') if preset else "")
        field("Genre (optional)", self.genre_var, values=["","Fantasy","Science Fiction","Mystery","Romance","Horror","Comedy","Drama","Thriller"])
        self.tone_var = tk.StringVar(value=preset.get('tone','') if preset else "")
        field("Tone (optional)", self.tone_var, values=["","Dark","Light","Humorous","Serious","Mysterious","Romantic","Action-packed","Reflective"])
        self.words_var = tk.StringVar(value=str(preset.get('word_count', DEFAULT_WORD_COUNT)) if preset else str(DEFAULT_WORD_COUNT))
        field("Word Count", self.words_var)
        self.prompt_text = field("Custom Prompt (optional)", None, height=4)
        if preset and preset.get('custom_prompt'): self.prompt_text.insert(1.0, preset['custom_prompt'])
        bf = tk.Frame(main, bg=LEATHER); bf.pack(fill=tk.X, pady=(6, 0))
        tk.Button(bf, text="Save",   command=self.save,
                  bg='#6A4A18', fg='#F2E4C4', font=('Segoe UI', 9, 'bold'), relief='flat',
                  padx=12, pady=5, activebackground='#8A6230', cursor='hand2', borderwidth=0).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(bf, text="Cancel", command=self.top.destroy,
                  bg='#1A1208', fg=PARCH_FG, font=('Segoe UI', 9), relief='flat',
                  padx=12, pady=5, activebackground='#2A1E0A', cursor='hand2', borderwidth=0).pack(side=tk.LEFT)

    def save(self) -> None:
        name = self.name_var.get().strip()
        if not name: messagebox.showerror("Error", "Name required."); return
        try:
            wc = int(self.words_var.get())
            if wc <= 0: raise ValueError
        except ValueError: messagebox.showerror("Error", "Word count must be a positive number."); return
        genre = self.genre_var.get().strip() or None; tone = self.tone_var.get().strip() or None
        prompt = self.prompt_text.get(1.0, tk.END).strip() or None
        if not self.preset:
            if self.presets_manager.get_preset(name): messagebox.showerror("Error", f"'{name}' already exists."); return
            if not self.presets_manager.save_preset(name, genre, tone, wc, prompt): messagebox.showerror("Error", "Save failed."); return
        else:
            if self.preset['name'] != name and self.presets_manager.get_preset(name): messagebox.showerror("Error", f"'{name}' already exists."); return
            self.presets_manager.update_preset(self.preset['name'], genre, tone, wc, prompt)
            if self.preset['name'] != name:
                self.presets_manager.delete_preset(self.preset['name'])
                self.presets_manager.save_preset(name, genre, tone, wc, prompt)
        self.result = {'name': name, 'genre': genre, 'tone': tone, 'word_count': wc, 'custom_prompt': prompt}
        self.top.destroy()
