import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkFont
import threading
import logging
from story_generator import (
    StoryGenerator, StoriesManager, PresetsManager,
    ContentQueueManager, NovelManager
)
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
from theme import CAVE, LIGHT, LEATHER, BRASS, BRASS_DIM, PARCH_BG, PARCH_FG, DARK_BG
from tabs.generate_tab import GenerateTab
from tabs.batch_tab import BatchTab
from tabs.novel_tab import NovelTab
from tabs.chat_tab import ChatTab
from tabs.statistics_tab import StatisticsTab
from tabs.thread_tab import ThreadFormatterTab
from tabs.queue_tab import QueueTab
from tabs.presets_tab import PresetsTab
from tabs.models_tab import ModelsTab
from tabs.saved_stories_tab import SavedStoriesTab


class ScrollCanvas(tk.Canvas):
    """A parchment scroll widget with curled ends."""

    PARCHMENT   = "#F2E4C4"
    ROLL_SHADOW = "#8A6E3A"
    BORDER_COL  = "#C9A96E"

    def __init__(self, parent, C, **kwargs) -> None:
        super().__init__(parent, bg=DARK_BG, highlightthickness=0, **kwargs)
        self.C = C
        self._placeholder = True
        PLACEHOLDER = (
            "Your story will appear here.\n\n"
            "Choose a model, set a genre and tone,\n"
            "then press Inscribe the Story."
        )
        self.text_widget = tk.Text(
            self, wrap=tk.WORD, font=('Georgia', 11), relief='flat', borderwidth=0,
            bg=self.PARCHMENT, fg='#3A2410', insertbackground='#8A4A10',
            selectbackground='#D4B06A', selectforeground='#1A0E06',
            spacing1=3, spacing3=3, padx=14, pady=10
        )
        self.text_widget.insert("1.0", PLACEHOLDER)
        self.text_widget.config(fg='#A08860')

        def _clear_ph(event=None) -> None:
            if self._placeholder:
                self.text_widget.delete("1.0", tk.END)
                self.text_widget.config(fg='#3A2410')
                self._placeholder = False
        self.text_widget.bind("<FocusIn>", _clear_ph)
        self.text_widget.bind("<Key>",     _clear_ph)
        self._tw_id = self.create_window(0, 0, window=self.text_widget, anchor='nw')
        self.bind('<Configure>', self._redraw)

    def restore_placeholder(self) -> None:
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0",
            "Your story will appear here.\n\n"
            "Choose a model, set a genre and tone,\n"
            "then press Inscribe the Story.")
        self.text_widget.config(fg='#A08860')
        self._placeholder = True

    def _redraw(self, event=None) -> None:
        w = self.winfo_width(); h = self.winfo_height()
        if w < 10 or h < 10: return
        self.delete('scroll_art')
        roll_h = 36; overhang = 22
        body_x1 = overhang; body_x2 = w - overhang
        body_y1 = roll_h;   body_y2 = h - roll_h
        for s in range(8, 0, -1):
            shade = 10 + s * 3
            self.create_rectangle(body_x1+s, body_y1+s, body_x2+s, body_y2+s,
                                   fill=f'#{shade:02x}{shade//2:02x}{0:02x}', outline='', tags='scroll_art')
        strips = 10
        for i in range(strips):
            t = i / (strips - 1); shade_t = abs(t - 0.5) * 0.18
            r = int(242 - shade_t * 40); g = int(228 - shade_t * 35); b = int(196 - shade_t * 30)
            sx = body_x1 + i * (body_x2 - body_x1) // strips
            ex = body_x1 + (i+1) * (body_x2 - body_x1) // strips
            self.create_rectangle(sx, body_y1, ex, body_y2, fill=f'#{r:02x}{g:02x}{b:02x}', outline='', tags='scroll_art')
        self.create_rectangle(body_x1, body_y1, body_x2, body_y2, fill='', outline=self.BORDER_COL, width=2, tags='scroll_art')
        self.create_oval(0, 4, w, roll_h*2+4, fill='#6A4818', outline='', tags='scroll_art')
        for i, col in enumerate(['#C8A86E','#D4B880','#BEA068']):
            off = i*3; self.create_oval(off, off, w-off, roll_h*2-off, fill=col, outline='', tags='scroll_art')
        self.create_oval(8,5,w-8,roll_h-4,fill='#E0C090',outline='',tags='scroll_art')
        self.create_oval(12,7,w-12,roll_h-8,fill='#E8CC9C',outline='',tags='scroll_art')
        self.create_oval(0,0,w,roll_h*2,fill='',outline=self.ROLL_SHADOW,width=1,tags='scroll_art')
        self.create_oval(0,h-roll_h*2-4,w,h+4,fill='#6A4818',outline='',tags='scroll_art')
        for i, col in enumerate(['#C8A86E','#D4B880','#BEA068']):
            off = i*3; self.create_oval(off,h-roll_h*2+off,w-off,h-off,fill=col,outline='',tags='scroll_art')
        self.create_oval(8,h-roll_h+4,w-8,h-5,fill='#E0C090',outline='',tags='scroll_art')
        self.create_oval(12,h-roll_h+6,w-12,h-8,fill='#E8CC9C',outline='',tags='scroll_art')
        self.create_oval(0,h-roll_h*2,w,h,fill='',outline=self.ROLL_SHADOW,width=1,tags='scroll_art')
        self.coords(self._tw_id, body_x1+2, body_y1+2)
        self.itemconfig(self._tw_id, width=body_x2-body_x1-4, height=body_y2-body_y1-4)


class StoryGeneratorApp:
    """Main GUI application for the story generator."""

    def __init__(self, root) -> None:
        self.root = root
        self.root.title("Story Generator")
        self.root.geometry("1280x820")
        self.root.minsize(900, 600)
        self.generator      = StoryGenerator
        self.stories_manager = StoriesManager()
        self.presets_manager = PresetsManager()
        self.queue_manager   = ContentQueueManager()
        self.novel_manager   = NovelManager(self.stories_manager.STORIES_DIR)
        self.current_stories: list = []
        self.is_generating   = False
        self._stop_event     = threading.Event()
        self.dark_mode       = True
        self.C               = CAVE
        self.setup_styles()
        self.create_widgets()
        self.check_ollama_status()

    def setup_styles(self) -> None:
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._apply_theme()

    def _apply_theme(self) -> None:
        C = self.C
        s = self.style
        s.configure('TFrame',      background=C['bg'])
        s.configure('TLabel',      background=C['bg'], foreground=C['fg'], font=('Segoe UI', 9))
        s.configure('TLabelframe', background=C['panel'], foreground=C['fg'],
                    bordercolor=C['fg_muted'], relief='groove')
        s.configure('TLabelframe.Label', background=C['panel'], foreground=C['accent'],
                    font=('Segoe UI', 9, 'bold'))
        s.configure('TNotebook', background=C['bg'], borderwidth=0)
        s.configure('TNotebook.Tab', background=C['bg'], foreground=C['fg_muted'],
                    padding=[14, 6], font=('Segoe UI', 9), borderwidth=0)
        s.map('TNotebook.Tab',
              background=[('selected', C['panel']), ('active', C['panel'])],
              foreground=[('selected', C['accent_hi']), ('active', C['accent'])])
        s.configure('TButton', background=C['panel'], foreground=C['accent'],
                    padding=[10, 5], relief='flat', font=('Segoe UI', 9), borderwidth=0)
        s.map('TButton', background=[('active', C['select'])], foreground=[('active', C['fg'])])
        s.configure('Accent.TButton', background=C['btn_bg'], foreground=C['btn_fg'],
                    padding=[12, 6], relief='flat', font=('Segoe UI', 9, 'bold'), borderwidth=0)
        s.map('Accent.TButton', background=[('active', C['accent'])], foreground=[('active', C['btn_fg'])])
        s.configure('Danger.TButton', background=C['danger'], foreground='#F0C0C0',
                    padding=[8, 4], relief='flat', font=('Segoe UI', 9), borderwidth=0)
        s.map('Danger.TButton', background=[('active', '#8A2020')])
        s.configure('TEntry',    fieldbackground=C['entry_bg'], foreground=C['fg'], bordercolor=C['border'])
        s.configure('TCombobox', fieldbackground=C['entry_bg'], foreground=C['fg'],
                    selectbackground=C['select'], selectforeground=C['btn_fg'], arrowcolor=C['fg_muted'])
        s.map('TCombobox', fieldbackground=[('readonly', C['entry_bg'])], foreground=[('readonly', C['fg'])])
        s.configure('TSpinbox',  fieldbackground=C['entry_bg'], foreground=C['fg'], arrowcolor=C['fg_muted'])
        s.configure('TScrollbar', background=C['panel'], troughcolor=C['bg'],
                    bordercolor=C['bg'], arrowcolor=C['fg_muted'])
        s.configure('Horizontal.TProgressbar', background=C['accent'], troughcolor=C['panel'])
        s.configure('TCheckbutton', background=C['panel'], foreground=C['fg'], focuscolor=C['panel'])
        self.root.configure(background=C['bg'])
        if hasattr(self, 'main_container'):
            try: self.main_container.config(bg=C['bg'])
            except Exception: pass

    def toggle_dark_mode(self) -> None:
        self.dark_mode = not self.dark_mode
        self.C = CAVE if self.dark_mode else LIGHT
        self._apply_theme()
        btn_text = "Day Mode" if self.dark_mode else "Night Mode"
        self.dark_mode_button.config(text=btn_text, bg='#1A1208', fg='#5A4820')
        self.status_var.set("Night mode" if self.dark_mode else "Day mode")

    def on_font_change(self, event=None) -> None:
        font_name = self.font_var.get()
        try:
            new_font = tkFont.Font(family=font_name, size=11)
            if hasattr(self, 'story_text'):
                self.story_text.config(font=new_font)
            self.status_var.set(f"Font: {font_name}")
        except Exception as e:
            self.status_var.set(f"Font error: {e}")

    def _setup_background_image(self, image_path) -> None:
        self.background_label = None
        self._bg_pil = None
        if not os.path.exists(image_path):
            return
        try:
            from PIL import Image
            self._bg_pil = Image.open(image_path)
        except Exception:
            pass

    def _apply_canvas_bg(self, canvas) -> None:
        """Attach resizing background image to any canvas."""
        ref = [None]
        def _resize(event=None) -> None:
            if not self._bg_pil: return
            w = canvas.winfo_width(); h = canvas.winfo_height()
            if w < 10 or h < 10: return
            try:
                from PIL import ImageTk
                try:    rs = __import__('PIL').Image.Resampling.LANCZOS
                except: rs = __import__('PIL').Image.LANCZOS
                img = self._bg_pil.resize((w, h), rs)
                ref[0] = ImageTk.PhotoImage(img)
                canvas.delete('tab_bg')
                canvas.create_image(0, 0, image=ref[0], anchor='nw', tags='tab_bg')
                canvas.tag_lower('tab_bg')
            except Exception: pass
        canvas.bind('<Configure>', _resize)
        canvas._bg_ref = ref

    def create_widgets(self) -> None:
        self._setup_background_image("background.png")
        self.main_container = tk.Frame(self.root, bg='#0D0A08')
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self._generate_tab = GenerateTab(self, ScrollCanvas)
        self._batch_tab = BatchTab(self)
        self._models_tab = ModelsTab(self)
        self._saved_tab = SavedStoriesTab(self)
        self._statistics_tab = StatisticsTab(self)
        self._presets_tab = PresetsTab(self)
        self._queue_tab = QueueTab(self)
        self._thread_tab = ThreadFormatterTab(self)
        self._chat_tab = ChatTab(self)
        self._novel_tab = NovelTab(self)
        self.create_status_bar()

    def create_status_bar(self) -> None:
        bar = tk.Frame(self.root, bg=LEATHER, height=28)
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Frame(self.root, bg=BRASS, height=1).pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var = tk.StringVar(value="Ready | Ollama: checking...")
        tk.Label(bar, textvariable=self.status_var, bg=LEATHER,
                 fg=BRASS_DIM, font=('Segoe UI', 8), anchor=tk.W).pack(
                 side=tk.LEFT, padx=12, fill=tk.X, expand=True)
        self.dark_mode_button = tk.Button(
            bar, text="Day Mode", command=self.toggle_dark_mode,
            bg='#2A1A0A', fg=BRASS_DIM, relief='flat',
            font=('Segoe UI', 8), padx=10, pady=2,
            activebackground='#3A2A10', activeforeground=PARCH_FG,
            cursor='hand2', borderwidth=0)
        self.dark_mode_button.pack(side=tk.RIGHT, padx=(4, 10), pady=3)
        tk.Label(bar, text="Font:", bg=LEATHER, fg=BRASS_DIM, font=('Segoe UI', 8)).pack(side=tk.RIGHT, padx=(0, 2))
        available_fonts = sorted(tkFont.families())
        self.font_var = tk.StringVar(value="Georgia")
        self.font_combo = ttk.Combobox(bar, textvariable=self.font_var,
                                        values=available_fonts, width=14, state='readonly')
        self.font_combo.pack(side=tk.RIGHT, padx=(0, 6), pady=3)
        self.font_combo.bind('<<ComboboxSelected>>', self.on_font_change)

    # ── Shared methods (cross-tab proxies and model management) ───────────

    def check_ollama_status(self) -> None:
        def check() -> None:
            if self.generator.check_ollama_running():
                self.status_var.set("Ready | Ollama: Connected")
                self.refresh_models()
            else:
                self.status_var.set("Ollama: Not Connected -- run 'ollama serve'")
                messagebox.showwarning("Ollama Not Found",
                    "Ollama service is not running.\nPlease start it by running 'ollama serve'.")
        threading.Thread(target=check, daemon=True).start()

    def refresh_models(self) -> None:
        def fetch() -> None:
            self.status_var.set("Fetching models...")
            try:
                models = self.generator.get_available_models()
                self.root.after(0, lambda: self._update_models(models))
            except Exception as e:
                self.root.after(0, lambda err=e: messagebox.showerror("Error", f"Failed to fetch models: {err}"))
                self.root.after(0, lambda: self.status_var.set("Error fetching models"))
        threading.Thread(target=fetch, daemon=True).start()

    def _update_models(self, models) -> None:
        EMBED_KEYWORDS = ("embed", "embedding", "nomic-embed", "bge-", "e5-", "all-minilm")
        models = [m for m in models if not any(kw in m.lower() for kw in EMBED_KEYWORDS)]
        if not models:
            self.status_var.set("No text-generation models found."); return
        self.model_combo['values'] = models
        self.model_var.set(models[0])
        self.models_display.delete(0, tk.END)
        self.models_listbox.delete(0, tk.END)
        for m in models:
            self.models_display.insert(tk.END, m)
            self.models_listbox.insert(tk.END, m)
        self.status_var.set(f"Ready | Ollama: Connected ({len(models)} models)")

    def refresh_saved_stories(self) -> None:
        """Proxy for saved stories tab refresh — called by save/batch methods."""
        if hasattr(self, '_saved_tab'):
            self._saved_tab.refresh_saved_stories()

    def _display_story(self, story) -> None:
        """Proxy for generate tab's _display_story — called by batch compare."""
        if hasattr(self, '_generate_tab'):
            self._generate_tab._display_story(story)

    def _stats(self) -> dict: return self.stories_manager.get_generation_statistics()


def main() -> None:
    root = tk.Tk()
    StoryGeneratorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
