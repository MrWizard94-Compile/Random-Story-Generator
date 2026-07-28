"""
Queue Manager tab — Schedule and manage story posting queue.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any
from datetime import datetime

from theme import LEATHER, BRASS, BRASS_DIM, PARCH_BG, PARCH_FG, DARK_BG


class QueueTab:
    """Encapsulates the Queue Manager tab UI and handlers."""

    def __init__(self, app) -> None:
        self.app = app
        self._build()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build(self) -> None:
        tab = tk.Frame(self.app.notebook, bg=DARK_BG)
        self.app.notebook.add(tab, text="Queue")
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
        left = tk.Frame(main, bg=LEATHER)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 2))
        tk.Label(left, text="Posting Queue", bg=LEATHER, fg=BRASS,
                 font=('Georgia', 12, 'bold'), padx=8).pack(anchor=tk.W, pady=(8, 4))
        tk.Frame(left, bg=BRASS, height=1).pack(fill=tk.X, padx=8)
        lf = tk.Frame(left, bg=LEATHER)
        lf.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.queue_listbox = tk.Listbox(lf, font=('Segoe UI', 9),
                                         bg=PARCH_BG, fg=PARCH_FG, relief='flat',
                                         selectbackground='#2A1E0A', selectforeground='#F2E4C4',
                                         borderwidth=0)
        self.queue_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.queue_listbox.bind('<<ListboxSelect>>', self.on_queue_item_selected)
        sb4 = ttk.Scrollbar(lf, command=self.queue_listbox.yview)
        sb4.pack(side=tk.RIGHT, fill=tk.Y)
        self.queue_listbox.config(yscrollcommand=sb4.set)
        tk.Frame(main, bg=BRASS, width=2).pack(side=tk.LEFT, fill=tk.Y)
        right = tk.Frame(main, bg=LEATHER, width=420)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(2, 0))
        right.pack_propagate(False)
        tk.Label(right, text="Schedule Post", bg=LEATHER, fg=BRASS,
                 font=('Georgia', 12, 'bold'), padx=8).pack(anchor=tk.W, pady=(8, 4))
        tk.Frame(right, bg=BRASS, height=1).pack(fill=tk.X, padx=8)
        form = tk.Frame(right, bg=LEATHER)
        form.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        def rfield(row, label, widget_factory) -> Any:
            tk.Label(form, text=label, bg=LEATHER, fg=BRASS, font=('Segoe UI', 9, 'bold')
                     ).grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 8))
            w = widget_factory(); w.grid(row=row, column=1, sticky=tk.W, pady=5)
            return w

        self.queue_story_var = tk.StringVar()
        self.queue_story_combo = rfield(0, "Story:", lambda: ttk.Combobox(form, textvariable=self.queue_story_var, state='readonly', width=36))
        self.queue_time_var = tk.StringVar()
        rfield(1, "Schedule (YYYY-MM-DD HH:MM):", lambda: ttk.Entry(form, textvariable=self.queue_time_var, width=38))
        self.queue_platform_var = tk.StringVar(value="X")
        rfield(2, "Platform:", lambda: ttk.Combobox(form, textvariable=self.queue_platform_var,
                                                     values=["X","Facebook","Threads","Instagram"],
                                                     width=36, state='readonly'))
        self.queue_status_var = tk.StringVar(value="Ready")
        rfield(3, "Status:", lambda: tk.Label(form, textvariable=self.queue_status_var,
                                               bg=LEATHER, fg=PARCH_FG, font=('Segoe UI', 9)))
        bf = tk.Frame(form, bg=LEATHER)
        bf.grid(row=4, column=0, columnspan=2, pady=12, sticky=tk.W)
        def _ink(p, t, c, accent=False, danger=False) -> Any:
            return tk.Button(p, text=t, command=c,
                             bg='#6A4A18' if accent else '#6A1A1A' if danger else '#1A1208',
                             fg='#F2E4C4' if accent else '#F0C0C0' if danger else PARCH_FG,
                             font=('Segoe UI', 9), relief='flat', padx=10, pady=4,
                             cursor='hand2', borderwidth=0)
        _ink(bf, "Add",        self.add_queue_item).pack(side=tk.LEFT, padx=(0, 4))
        _ink(bf, "Update",     self.update_queue_item).pack(side=tk.LEFT, padx=(0, 4))
        _ink(bf, "Remove",     self.delete_queue_item, danger=True).pack(side=tk.LEFT, padx=(0, 4))
        _ink(bf, "Execute Now",self.execute_selected_queue_item, accent=True).pack(side=tk.LEFT)
        self.refresh_queue_list()
        self.refresh_queue_story_options()
        self.app.root.after(60000, self.check_queue_worker)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def refresh_queue_story_options(self) -> None:
        stories = self.app.stories_manager.get_all_stories_metadata()
        self.queue_story_combo['values'] = [f"{s['filename']} | {s.get('title','Untitled')}" for s in stories]

    def refresh_queue_list(self) -> None:
        self.queue_listbox.delete(0, tk.END); self.refresh_queue_story_options()
        for item in self.app.queue_manager.get_queue():
            when = item['scheduled_time'].strftime('%Y-%m-%d %H:%M') if isinstance(item['scheduled_time'], datetime) else str(item['scheduled_time'])
            self.queue_listbox.insert(tk.END, f"{when} | {item.get('platform','?')} | {item.get('story_title','?')} | {item.get('status','?')}")

    def on_queue_item_selected(self, event) -> None:
        sel = self.queue_listbox.curselection()
        if not sel: return
        item = self.app.queue_manager.get_queue()[sel[0]]
        self.queue_story_var.set(f"{item['story_id']} | {item['story_title']}")
        self.queue_time_var.set(item['scheduled_time'].strftime('%Y-%m-%d %H:%M'))
        self.queue_platform_var.set(item.get('platform', 'X'))
        self.queue_status_var.set(item.get('status', 'Scheduled'))

    def _parse_queue_form(self) -> Any:
        sv = self.queue_story_var.get().strip(); tv = self.queue_time_var.get().strip(); pv = self.queue_platform_var.get().strip()
        if not sv or not tv: messagebox.showwarning("Error", "Select a story and set a scheduled time."); return None
        try: st = datetime.fromisoformat(tv)
        except ValueError: messagebox.showwarning("Error", "Time must be YYYY-MM-DD HH:MM."); return None
        if ' | ' not in sv: messagebox.showwarning("Error", "Invalid story selection."); return None
        sid, stitle = sv.split(' | ', 1)
        return {'story_id': sid, 'story_title': stitle, 'scheduled_time': st, 'platform': pv or 'X', 'status': 'Scheduled'}

    def add_queue_item(self) -> None:
        item = self._parse_queue_form()
        if item: self.app.queue_manager.add_to_queue(item); self.refresh_queue_list(); messagebox.showinfo("Queued", "Added to queue.")

    def update_queue_item(self) -> None:
        sel = self.queue_listbox.curselection()
        if not sel: messagebox.showwarning("Error", "Select an item first."); return
        item = self._parse_queue_form()
        if item:
            existing = self.app.queue_manager.get_queue()[sel[0]]
            item['status'] = existing.get('status', 'Scheduled')
            self.app.queue_manager.update_queue_item(existing['id'], item)
            self.refresh_queue_list(); messagebox.showinfo("Updated", "Queue item updated.")

    def delete_queue_item(self) -> None:
        sel = self.queue_listbox.curselection()
        if not sel: messagebox.showwarning("Error", "Select an item first."); return
        item = self.app.queue_manager.get_queue()[sel[0]]
        if self.app.queue_manager.remove_from_queue(item['id']): self.refresh_queue_list(); messagebox.showinfo("Removed", "Item removed.")
        else: messagebox.showerror("Error", "Remove failed.")

    def execute_selected_queue_item(self) -> None:
        sel = self.queue_listbox.curselection()
        if not sel: messagebox.showwarning("Error", "Select an item first."); return
        item = self.app.queue_manager.get_queue()[sel[0]]
        self.app.queue_manager.execute_queue_item(item['id'], self.app.stories_manager)
        self.refresh_queue_list(); messagebox.showinfo("Executed", f"Executed: {item['story_title']}")

    def check_queue_worker(self) -> None:
        due = self.app.queue_manager.get_scheduled_items(datetime.now())
        for item in due: self.app.queue_manager.execute_queue_item(item['id'], self.app.stories_manager)
        if due: self.refresh_queue_list()
        self.app.root.after(60000, self.check_queue_worker)
