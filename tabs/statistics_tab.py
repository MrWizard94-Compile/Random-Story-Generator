"""
Statistics tab — Charts, metrics, and overview of all generated stories.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from theme import LEATHER, BRASS, BRASS_DIM, PARCH_BG, PARCH_FG, DARK_BG


class StatisticsTab:
    """Encapsulates the Statistics tab UI and all chart/refresh handlers."""

    def __init__(self, app) -> None:
        self.app = app
        self._stats_figures: list = []
        self._stats_factories: list = []
        self._build()

    def _stats(self) -> dict:
        return self.app.stories_manager.get_generation_statistics()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build(self) -> None:
        tab = tk.Frame(self.app.notebook, bg=DARK_BG)
        self.app.notebook.add(tab, text="Stats")
        hdr = tk.Frame(tab, bg=LEATHER)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Chronicle of Tales", bg=LEATHER, fg=BRASS,
                 font=('Georgia', 12, 'bold'), padx=12, pady=8).pack(side=tk.LEFT)
        tk.Frame(hdr, bg=BRASS, height=1).pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(hdr, text="Refresh Annals", command=self.refresh_statistics).pack(side=tk.RIGHT, padx=10, pady=6)
        self.stats_nb = ttk.Notebook(tab)
        self.stats_nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._stats_factories = [
            ("Overview",    self._create_overview),
            ("Models",      self._create_models_chart),
            ("Performance", self._create_performance_chart),
            ("Genres",      self._create_genres_chart),
            ("Timeline",    self._create_timeline_chart),
            ("Ratings",     self._create_ratings_chart),
            ("Engagement",  self._create_engagement),
        ]
        for title, factory in self._stats_factories:
            t = ttk.Frame(self.stats_nb)
            self.stats_nb.add(t, text=title)
            factory(t)

    # ── Chart helpers ─────────────────────────────────────────────────────────

    def _embed_chart(self, parent, fig) -> None:
        self._stats_figures.append(fig)
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _no_data(self, parent, msg: str = "No data yet.") -> None:
        tk.Label(parent, text=msg, bg=LEATHER, fg=BRASS_DIM).pack(pady=40)

    def _chart_axes(self, fig) -> Any:
        ax = fig.add_subplot(111)
        ax.set_facecolor('#16100A')
        ax.tick_params(colors='#C4A86A')
        ax.title.set_color('#C4A86A')
        for spine in ax.spines.values():
            spine.set_edgecolor('#3A2810')
        return ax

    # ── Chart factories ───────────────────────────────────────────────────────

    def _create_overview(self, parent) -> None:
        stats = self._stats()
        info = tk.Frame(parent, bg=LEATHER)
        info.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        tk.Label(info, text="Overview", bg=LEATHER, fg=BRASS, font=('Georgia', 11, 'bold'), padx=8, pady=4).pack(anchor=tk.W)
        tk.Frame(info, bg=BRASS, height=1).pack(fill=tk.X, padx=8, pady=(0, 8))
        grid = tk.Frame(info, bg=LEATHER)
        grid.pack(fill=tk.BOTH, expand=True, padx=8)
        data = [("Tales Generated", stats['total_stories']), ("Total Words", f"{stats['total_words']:,}"),
                ("Avg Words/Tale", f"{stats['average_words']:.0f}"), ("Models Used", len(stats['models'])),
                ("Genres", len(stats['genres'])), ("Avg Rating", f"{stats['rating_stats']['average']:.1f} / 5.0"),
                ("Rated Tales", stats['rating_stats']['total_rated']), ("Favourites", stats['rating_stats']['favorites'])]
        for i, (lbl, val) in enumerate(data):
            r, c = divmod(i, 3)
            f = tk.Frame(grid, bg='#16100A', relief='flat', padx=12, pady=10)
            f.grid(row=r, column=c, padx=6, pady=6, sticky=tk.NSEW)
            tk.Label(f, text=lbl, bg='#16100A', fg=BRASS_DIM, font=('Segoe UI', 8)).pack(anchor=tk.W)
            tk.Label(f, text=str(val), bg='#16100A', fg=BRASS, font=('Georgia', 16, 'bold')).pack(anchor=tk.W)
        for c in range(3):
            grid.grid_columnconfigure(c, weight=1)

    def _create_models_chart(self, parent) -> None:
        stats = self._stats()
        if not stats['models']:
            self._no_data(parent); return
        fig = Figure(figsize=(8, 5), dpi=100, facecolor='#1A0D06')
        ax = self._chart_axes(fig)
        ax.bar(list(stats['models'].keys()), list(stats['models'].values()), color='#8A6E2A')
        ax.set_title("Tales by Spirit", fontweight='bold'); ax.set_ylabel("Count"); ax.grid(axis='y', alpha=0.2)
        fig.tight_layout(); self._embed_chart(parent, fig)

    def _create_performance_chart(self, parent) -> None:
        stats = self._stats()
        mp = stats.get('model_performance', {})
        if not mp:
            self._no_data(parent, "No performance data yet."); return
        models = list(mp.keys())
        fig = Figure(figsize=(9, 5), dpi=100, facecolor='#1A0D06')
        ax1 = fig.add_subplot(111); ax1.set_facecolor('#16100A'); ax1.tick_params(colors='#C4A86A')
        ax1.bar(models, [mp[m]['count'] for m in models], color='#8A6E2A', alpha=0.8)
        ax1.set_ylabel("Count"); ax1.set_title("Spirit Performance", fontweight='bold')
        ax2 = ax1.twinx()
        ax2.plot(models, [mp[m]['avg_rating'] for m in models], color='#C4953A', marker='o', linewidth=2)
        ax2.set_ylabel("Avg Rating"); ax2.set_ylim(0, 5)
        fig.tight_layout(); self._embed_chart(parent, fig)

    def _create_genres_chart(self, parent) -> None:
        stats = self._stats()
        if not stats['genres']:
            self._no_data(parent, "No genre data yet."); return
        fig = Figure(figsize=(7, 5), dpi=100, facecolor='#1A0D06')
        ax = fig.add_subplot(111); ax.set_facecolor('#16100A')
        ax.pie(list(stats['genres'].values()), labels=list(stats['genres'].keys()),
               autopct='%1.1f%%', colors=plt.cm.Pastel1(range(len(stats['genres']))), startangle=90)
        ax.set_title("Realms Explored", fontweight='bold')
        fig.tight_layout(); self._embed_chart(parent, fig)

    def _create_timeline_chart(self, parent) -> None:
        stats = self._stats()
        if not stats['generation_timeline']:
            self._no_data(parent, "No timeline data yet."); return
        dates = sorted(stats['generation_timeline'].keys())
        counts = [stats['generation_timeline'][d] for d in dates]
        dobjs = [datetime.strptime(d, '%Y-%m-%d') for d in dates]
        fig = Figure(figsize=(10, 5), dpi=100, facecolor='#1A0D06')
        ax = self._chart_axes(fig)
        ax.plot(dobjs, counts, marker='o', linewidth=2, color='#C4953A')
        ax.fill_between(dobjs, counts, alpha=0.2, color='#C4953A')
        ax.set_title("Chronicle Timeline", fontweight='bold'); ax.set_ylabel("Tales"); ax.grid(True, alpha=0.15)
        fig.autofmt_xdate(); fig.tight_layout(); self._embed_chart(parent, fig)

    def _create_ratings_chart(self, parent) -> None:
        stats = self._stats()
        dist = stats['rating_stats']['distribution']
        if sum(dist.values()) == 0:
            self._no_data(parent, "No ratings yet."); return
        fig = Figure(figsize=(7, 5), dpi=100, facecolor='#1A0D06')
        ax = self._chart_axes(fig)
        bars = ax.bar([f"{i}*" for i in dist], list(dist.values()),
                      color=['#4A2020', '#6A3020', '#8A6E2A', '#4A7C59', '#2A5C39'])
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), str(int(b.get_height())),
                    ha='center', va='bottom', fontweight='bold', color='#C4A86A')
        ax.set_title("Tale Ratings", fontweight='bold'); ax.set_ylabel("Count"); ax.grid(axis='y', alpha=0.15)
        fig.tight_layout(); self._embed_chart(parent, fig)

    def _create_engagement(self, parent) -> None:
        ps = self.app.queue_manager.get_performance_stats()
        info = tk.Frame(parent, bg=LEATHER)
        info.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        tk.Label(info, text="Engagement", bg=LEATHER, fg=BRASS, font=('Georgia', 11, 'bold'), padx=8, pady=4).pack(anchor=tk.W)
        tk.Frame(info, bg=BRASS, height=1).pack(fill=tk.X, padx=8, pady=(0, 8))
        grid = tk.Frame(info, bg=LEATHER)
        grid.pack(fill=tk.BOTH, expand=True, padx=8)
        data = [("Total Posts", ps['total_posts']), ("Total Views", f"{ps['total_views']:,}"),
                ("Total Likes", f"{ps['total_likes']:,}"), ("Total Shares", f"{ps['total_shares']:,}"),
                ("Total Comments", f"{ps['total_comments']:,}"), ("Avg Engagement", f"{ps['avg_engagement']:.1f}")]
        for i, (lbl, val) in enumerate(data):
            r, c = divmod(i, 3)
            f = tk.Frame(grid, bg='#16100A', padx=12, pady=10)
            f.grid(row=r, column=c, padx=6, pady=6, sticky=tk.NSEW)
            tk.Label(f, text=lbl, bg='#16100A', fg=BRASS_DIM, font=('Segoe UI', 8)).pack(anchor=tk.W)
            tk.Label(f, text=str(val), bg='#16100A', fg=BRASS, font=('Georgia', 16, 'bold')).pack(anchor=tk.W)
        for c in range(3):
            grid.grid_columnconfigure(c, weight=1)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh_statistics(self) -> None:
        """Destroy all stats tabs and rebuild with fresh data."""
        for fig in self._stats_figures:
            try:
                plt.close(fig)
            except Exception:
                pass
        self._stats_figures.clear()
        for tab_id in self.stats_nb.tabs():
            self.stats_nb.forget(tab_id)
        for title, factory in self._stats_factories:
            t = ttk.Frame(self.stats_nb)
            self.stats_nb.add(t, text=title)
            factory(t)
        self.app.status_var.set("Statistics refreshed.")
