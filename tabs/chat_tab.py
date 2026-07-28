"""
Chat tab — Multi-turn conversational story crafting with streaming responses.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any
import threading

from theme import LEATHER, BRASS, BRASS_DIM, PARCH_BG, PARCH_FG, DARK_BG


class ChatTab:
    """Encapsulates the Chat tab UI and all chat-related handlers."""

    def __init__(self, app) -> None:
        self.app = app
        self._chat_history: list = []
        self._chat_stop = threading.Event()
        self._chat_is_sending = False
        self._chat_stream_mark = "1.0"
        self._build()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build(self) -> None:
        tab = tk.Frame(self.app.notebook, bg=DARK_BG)
        self.app.notebook.add(tab, text="Chat")
        canvas = tk.Canvas(tab, highlightthickness=0, bg=DARK_BG)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.app._apply_canvas_bg(canvas)
        overlay = tk.Frame(canvas, bg=DARK_BG)
        ow = canvas.create_window(0, 0, window=overlay, anchor='nw')
        canvas.bind('<Configure>', lambda e: (
            overlay.config(width=canvas.winfo_width(), height=canvas.winfo_height()),
            canvas.itemconfig(ow, width=canvas.winfo_width(), height=canvas.winfo_height())
        ))

        # ── Left panel — model + controls ─────────────────────────────────────
        left = tk.Frame(overlay, bg=LEATHER, width=260)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)
        tk.Frame(overlay, bg=BRASS, width=2).pack(side=tk.LEFT, fill=tk.Y)
        inner = tk.Frame(left, bg=LEATHER)
        inner.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        tk.Label(inner, text="The Scribe's Chamber", bg=LEATHER, fg=BRASS,
                 font=('Georgia', 12, 'bold')).pack(anchor=tk.W, pady=(0, 2))
        tk.Label(inner, text="Converse to craft your story", bg=LEATHER, fg=BRASS_DIM,
                 font=('Segoe UI', 8, 'italic')).pack(anchor=tk.W, pady=(0, 8))
        tk.Frame(inner, bg=BRASS, height=1).pack(fill=tk.X, pady=(0, 10))

        # Model selector
        tk.Label(inner, text="WRITING SPIRIT", bg=LEATHER, fg=BRASS,
                 font=('Segoe UI', 7, 'bold')).pack(anchor=tk.W)
        tk.Label(inner, text="Model", bg=LEATHER, fg=BRASS_DIM,
                 font=('Segoe UI', 8)).pack(anchor=tk.W, pady=(4, 0))
        self.chat_model_var = tk.StringVar(value="llama2")
        self.chat_model_combo = ttk.Combobox(inner, textvariable=self.chat_model_var, state="readonly")
        self.chat_model_combo.pack(fill=tk.X, pady=(2, 8))

        # System prompt (optional)
        tk.Frame(inner, bg=BRASS, height=1).pack(fill=tk.X, pady=(0, 8))
        tk.Label(inner, text="SCRIBE'S DIRECTIVE", bg=LEATHER, fg=BRASS,
                 font=('Segoe UI', 7, 'bold')).pack(anchor=tk.W)
        tk.Label(inner, text="Optional system context", bg=LEATHER, fg=BRASS_DIM,
                 font=('Segoe UI', 8)).pack(anchor=tk.W, pady=(4, 0))
        self.chat_system_var = tk.Text(inner, height=4, wrap=tk.WORD,
                                        font=('Segoe UI', 9), relief='flat',
                                        bg=PARCH_BG, fg=PARCH_FG,
                                        insertbackground=BRASS,
                                        padx=6, pady=4, borderwidth=1,
                                        highlightthickness=1, highlightbackground=BRASS)
        self.chat_system_var.insert("1.0", "You are a world-class novelist. Write immersive, vivid fiction.")
        self.chat_system_var.pack(fill=tk.X, pady=(2, 8))

        # Load story button
        tk.Frame(inner, bg=BRASS, height=1).pack(fill=tk.X, pady=(0, 8))
        tk.Label(inner, text="LOAD FROM ARCHIVE", bg=LEATHER, fg=BRASS,
                 font=('Segoe UI', 7, 'bold')).pack(anchor=tk.W)
        tk.Label(inner, text="Seed chat with existing story", bg=LEATHER, fg=BRASS_DIM,
                 font=('Segoe UI', 8)).pack(anchor=tk.W, pady=(4, 0))
        self.chat_load_var = tk.StringVar()
        self.chat_load_combo = ttk.Combobox(inner, textvariable=self.chat_load_var, state="readonly")
        self.chat_load_combo.pack(fill=tk.X, pady=(2, 4))

        tk.Button(inner, text="Load into Chat", command=self._load_story_to_chat,
                  bg='#1A1208', fg=PARCH_FG, font=('Segoe UI', 9), relief='flat',
                  padx=10, pady=4, activebackground='#2A1E0A',
                  cursor='hand2', borderwidth=0).pack(fill=tk.X, pady=(0, 8))

        # Clear conversation
        tk.Frame(inner, bg=BRASS, height=1).pack(fill=tk.X, pady=(0, 8))
        tk.Button(inner, text="Clear Conversation", command=self._clear_chat,
                  bg='#2A1A1A', fg='#C09090', font=('Segoe UI', 9), relief='flat',
                  padx=10, pady=4, activebackground='#3A2020',
                  cursor='hand2', borderwidth=0).pack(fill=tk.X, pady=(0, 4))

        # Save latest response
        tk.Button(inner, text="Save to Archive", command=self._save_chat_response,
                  bg='#6A4A18', fg='#F2E4C4', font=('Segoe UI', 9, 'bold'), relief='flat',
                  padx=10, pady=5, activebackground='#8A6230',
                  cursor='hand2', borderwidth=0).pack(fill=tk.X, pady=(0, 4))

        # Status
        self.chat_status_var = tk.StringVar(value="Ready to write")
        tk.Label(inner, textvariable=self.chat_status_var, bg=LEATHER, fg=BRASS_DIM,
                 font=('Segoe UI', 8), wraplength=220).pack(anchor=tk.W, pady=(8, 0))

        # ── Right — chat display + input ───────────────────────────────────────
        right = tk.Frame(overlay, bg=DARK_BG)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Header
        hdr = tk.Frame(right, bg=LEATHER)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Story Conversation", bg=LEATHER, fg=BRASS,
                 font=('Georgia', 13, 'bold'), padx=12, pady=8).pack(side=tk.LEFT)
        tk.Frame(hdr, bg=BRASS, height=1).pack(side=tk.BOTTOM, fill=tk.X)

        # Chat display
        display_frame = tk.Frame(right, bg=DARK_BG)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.chat_display = tk.Text(display_frame, wrap=tk.WORD,
                                     font=('Georgia', 10),
                                     bg='#16100A', fg=PARCH_FG,
                                     state=tk.DISABLED, relief='flat',
                                     padx=12, pady=8,
                                     insertbackground=BRASS,
                                     borderwidth=0)
        chat_scroll = ttk.Scrollbar(display_frame, command=self.chat_display.yview)
        self.chat_display.config(yscrollcommand=chat_scroll.set)
        chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Text tags for styling
        self.chat_display.tag_configure("user_label",   foreground=BRASS,      font=('Segoe UI', 8, 'bold'))
        self.chat_display.tag_configure("user_text",    foreground='#D4C9A8',  font=('Segoe UI', 10))
        self.chat_display.tag_configure("model_label",  foreground='#C4953A',  font=('Segoe UI', 8, 'bold'))
        self.chat_display.tag_configure("model_text",   foreground=PARCH_FG,   font=('Georgia', 10))
        self.chat_display.tag_configure("system_note",  foreground=BRASS_DIM,  font=('Segoe UI', 8, 'italic'))

        # Input area
        input_frame = tk.Frame(right, bg=LEATHER)
        input_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        tk.Frame(input_frame, bg=BRASS, height=1).pack(fill=tk.X)
        input_inner = tk.Frame(input_frame, bg=LEATHER)
        input_inner.pack(fill=tk.X, padx=8, pady=6)

        self.chat_input = tk.Text(input_inner, height=4, wrap=tk.WORD,
                                   font=('Segoe UI', 10), relief='flat',
                                   bg=PARCH_BG, fg=PARCH_FG,
                                   insertbackground=BRASS,
                                   padx=8, pady=6, borderwidth=1,
                                   highlightthickness=1, highlightbackground=BRASS)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.chat_input.bind("<Return>",       lambda e: (self._send_chat(), "break")[1])
        self.chat_input.bind("<Shift-Return>", lambda e: None)  # allow newline

        btn_col = tk.Frame(input_inner, bg=LEATHER)
        btn_col.pack(side=tk.RIGHT)
        self.chat_send_btn = tk.Button(btn_col, text="Send",
                                        command=self._send_chat,
                                        bg='#6A4A18', fg='#F2E4C4',
                                        font=('Segoe UI', 10, 'bold'),
                                        relief='flat', padx=16, pady=8,
                                        activebackground='#8A6230',
                                        cursor='hand2', borderwidth=0)
        self.chat_send_btn.pack(fill=tk.X, pady=(0, 4))
        self.chat_stop_btn = tk.Button(btn_col, text="Stop",
                                        command=lambda: self._chat_stop.set(),
                                        bg='#6A1A1A', fg='#F0C0C0',
                                        font=('Segoe UI', 10, 'bold'),
                                        relief='flat', padx=16, pady=8,
                                        activebackground='#8A2020',
                                        cursor='hand2', borderwidth=0)
        # stop btn shown only during generation

        # Populate model combo (shared with generate tab)
        def _sync_chat_models(*_) -> None:
            vals = self.app.model_combo['values'] if hasattr(self.app, 'model_combo') else []
            if vals:
                self.chat_model_combo['values'] = vals
                if not self.chat_model_var.get() or self.chat_model_var.get() not in vals:
                    self.chat_model_var.set(vals[0])
        self.chat_model_combo.bind("<Button-1>", _sync_chat_models)
        self.app.root.after(2000, _sync_chat_models)

        # Populate load combo
        def _refresh_chat_load() -> None:
            stories = self.app.stories_manager.get_all_stories_metadata()
            self.chat_load_combo['values'] = [
                f"{s['filename']} | {s.get('title','Untitled')}" for s in stories
            ]
        self.app.root.after(1500, _refresh_chat_load)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _load_story_to_chat(self) -> None:
        choice = self.chat_load_var.get()
        if not choice or ' | ' not in choice:
            return
        fname = choice.split(' | ')[0]
        content = self.app.stories_manager.load_story(fname)
        if not content:
            return
        seed = f"Here is a story I want to work on together:\n\n{content}\n\nI'd like your help refining and developing it."
        self._append_message("user", seed, display_text="[Story loaded from archive — ready to refine]")
        self._chat_history.append({"role": "user", "content": seed})
        self.chat_status_var.set(f"Loaded: {fname}")

    def _clear_chat(self) -> None:
        self._chat_history.clear()
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_status_var.set("Conversation cleared")

    def _save_chat_response(self) -> None:
        content = self.chat_display.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Empty", "Nothing to save yet.")
            return
        last_assist = ""
        for msg in reversed(self._chat_history):
            if msg["role"] == "assistant":
                last_assist = msg["content"]
                break
        if not last_assist:
            messagebox.showwarning("Empty", "No model response to save yet.")
            return
        model = self.chat_model_var.get()
        try:
            self.app.stories_manager.save_story(last_assist, model)
            self.chat_status_var.set("Saved to archive")
            self.app.refresh_saved_stories()
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")

    def _send_chat(self) -> None:
        user_text = self.chat_input.get("1.0", tk.END).strip()
        if not user_text or self._chat_is_sending:
            return
        model = self.chat_model_var.get()
        if not model:
            return

        # Clear input, show message
        self.chat_input.delete("1.0", tk.END)
        self._append_message("user", user_text)

        # Build message list
        sys_text = self.chat_system_var.get("1.0", tk.END).strip()
        messages: list = []
        if sys_text:
            messages.append({"role": "system", "content": sys_text})
        messages.extend(self._chat_history)
        messages.append({"role": "user", "content": user_text})
        self._chat_history.append({"role": "user", "content": user_text})

        # Swap Send → Stop
        self._chat_is_sending = True
        self._chat_stop.clear()
        self.chat_send_btn.pack_forget()
        self.chat_stop_btn.pack(fill=tk.X, pady=(0, 4))
        self.chat_status_var.set(f"Writing with {model}...")

        # Prepare response slot
        self._append_message("model_start", "")
        full_response: list = []
        root = self.app.root

        def _stream() -> None:
            try:
                for chunk in self.app.generator.chat_streaming(model, messages, self._chat_stop):
                    full_response.append(chunk)
                    root.after(0, lambda c=chunk: self._append_chunk(c))
                resp = "".join(full_response)
                self._chat_history.append({"role": "assistant", "content": resp})
                root.after(0, lambda: self.chat_status_var.set("Ready to write"))
            except Exception as e:
                root.after(0, lambda err=e: self.chat_status_var.set(f"Error: {err}"))
            finally:
                self._chat_is_sending = False
                self._chat_stop.clear()
                root.after(0, lambda: self.chat_stop_btn.pack_forget())
                root.after(0, lambda: self.chat_send_btn.pack(fill=tk.X, pady=(0, 4)))

        threading.Thread(target=_stream, daemon=True).start()

    def _append_message(self, role: str, text: str, display_text: str = None) -> None:
        """Append a full message block to the chat display."""
        self.chat_display.config(state=tk.NORMAL)
        show = display_text or text
        if role == "user":
            self.chat_display.insert(tk.END, "\n  You\n", "user_label")
            self.chat_display.insert(tk.END, f"  {show}\n", "user_text")
        elif role == "model_start":
            self.chat_display.insert(tk.END, "\n  Scribe\n", "model_label")
            self._chat_stream_mark = self.chat_display.index(tk.END)
        elif role == "system_note":
            self.chat_display.insert(tk.END, f"  {show}\n", "system_note")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def _append_chunk(self, chunk: str) -> None:
        """Append a streaming chunk to the current model response."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, chunk, "model_text")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
