"""
theme.py — Shared theme constants for the Story Generator GUI.

Both gui_app.py and tab modules import from here to avoid circular imports.
"""

# Grimoire theme — dark leather, brass accents, warm parchment text
CAVE = {
    "bg":        "#0D0A08",   # DARK_BG
    "panel":     "#1A0D06",   # LEATHER
    "fg":        "#C4A86A",   # PARCH_FG
    "fg_muted":  "#5A4820",   # BRASS_DIM
    "accent":    "#8A6E2A",   # BRASS
    "accent_hi": "#C4953A",   # bright accent (selected tabs, headers)
    "accent2":   "#4A7C59",
    "danger":    "#6A1A1A",
    "border":    "#3A2810",
    "entry_bg":  "#16100A",   # PARCH_BG
    "select":    "#2A1E0A",
    "btn_bg":    "#6A4A18",   # accent button background
    "btn_fg":    "#F2E4C4",   # accent button text
}

LIGHT = {
    "bg":        "#F0EBE0",
    "panel":     "#E8E0D0",
    "fg":        "#3A2810",
    "fg_muted":  "#8C7B5E",
    "accent":    "#8A6E2A",
    "accent_hi": "#A07828",
    "accent2":   "#3A6B48",
    "danger":    "#9B3535",
    "border":    "#C8B898",
    "entry_bg":  "#FAFAF5",
    "select":    "#DDD4C0",
    "btn_bg":    "#8A6E2A",
    "btn_fg":    "#FFF8E8",
}

# Module-level aliases for convenience in widget construction
LEATHER   = CAVE["panel"]
BRASS     = CAVE["accent"]
BRASS_DIM = CAVE["fg_muted"]
PARCH_BG  = CAVE["entry_bg"]
PARCH_FG  = CAVE["fg"]
DARK_BG   = CAVE["bg"]
