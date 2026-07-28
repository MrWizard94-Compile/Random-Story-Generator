#!/usr/bin/env python3
"""
Tests for GUI tab modularization — verifies imports, class structure,
cross-tab bridges, and proxy methods after extracting 10 tabs from gui_app.py.
"""
import unittest
import sys
import os
import importlib

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Phase 1: Import Tests (no display needed) ────────────────────────────────

class TestTabImports(unittest.TestCase):
    """Verify every tab module imports without syntax or import errors."""

    def test_import_generate_tab(self) -> None:
        mod = importlib.import_module("tabs.generate_tab")
        self.assertTrue(hasattr(mod, "GenerateTab"))

    def test_import_batch_tab(self) -> None:
        mod = importlib.import_module("tabs.batch_tab")
        self.assertTrue(hasattr(mod, "BatchTab"))

    def test_import_models_tab(self) -> None:
        mod = importlib.import_module("tabs.models_tab")
        self.assertTrue(hasattr(mod, "ModelsTab"))

    def test_import_saved_stories_tab(self) -> None:
        mod = importlib.import_module("tabs.saved_stories_tab")
        self.assertTrue(hasattr(mod, "SavedStoriesTab"))

    def test_import_statistics_tab(self) -> None:
        mod = importlib.import_module("tabs.statistics_tab")
        self.assertTrue(hasattr(mod, "StatisticsTab"))

    def test_import_presets_tab(self) -> None:
        mod = importlib.import_module("tabs.presets_tab")
        self.assertTrue(hasattr(mod, "PresetsTab"))
        self.assertTrue(hasattr(mod, "PresetDialog"))

    def test_import_queue_tab(self) -> None:
        mod = importlib.import_module("tabs.queue_tab")
        self.assertTrue(hasattr(mod, "QueueTab"))

    def test_import_thread_tab(self) -> None:
        mod = importlib.import_module("tabs.thread_tab")
        self.assertTrue(hasattr(mod, "ThreadFormatterTab"))

    def test_import_chat_tab(self) -> None:
        mod = importlib.import_module("tabs.chat_tab")
        self.assertTrue(hasattr(mod, "ChatTab"))

    def test_import_novel_tab(self) -> None:
        mod = importlib.import_module("tabs.novel_tab")
        self.assertTrue(hasattr(mod, "NovelTab"))

    def test_import_gui_app(self) -> None:
        mod = importlib.import_module("gui_app")
        self.assertTrue(hasattr(mod, "StoryGeneratorApp"))
        self.assertTrue(hasattr(mod, "ScrollCanvas"))
        self.assertTrue(hasattr(mod, "main"))

    def test_import_theme(self) -> None:
        mod = importlib.import_module("theme")
        for name in ("CAVE", "LIGHT", "LEATHER", "BRASS", "BRASS_DIM",
                      "PARCH_BG", "PARCH_FG", "DARK_BG"):
            self.assertTrue(hasattr(mod, name), f"theme missing {name}")


class TestTabClassStructure(unittest.TestCase):
    """Verify each tab class has the expected methods."""

    def _check_class(self, module_name: str, class_name: str,
                     expected_methods: list) -> None:
        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)
        for method in expected_methods:
            self.assertTrue(
                hasattr(cls, method),
                f"{class_name} missing method: {method}"
            )

    def test_generate_tab_methods(self) -> None:
        self._check_class("tabs.generate_tab", "GenerateTab", [
            "_build", "generate_single_story", "_display_story",
            "_append_to_story", "_show_validation_report",
            "save_single_story", "copy_story", "clear_story",
            "_stop_generation",
        ])

    def test_batch_tab_methods(self) -> None:
        self._check_class("tabs.batch_tab", "BatchTab", [
            "_build", "generate_batch", "_display_batch_results",
            "compare_batch_stories", "save_all_batch_stories",
        ])

    def test_models_tab_methods(self) -> None:
        self._check_class("tabs.models_tab", "ModelsTab", [
            "_build", "pull_model",
        ])

    def test_saved_stories_tab_methods(self) -> None:
        self._check_class("tabs.saved_stories_tab", "SavedStoriesTab", [
            "_build", "refresh_saved_stories", "apply_filters",
            "clear_filters", "on_filtered_story_selected",
            "on_rating_changed", "on_favorite_changed",
            "copy_saved_story", "delete_saved_story",
            "export_story_pdf", "export_story_docx", "export_story_txt",
            "open_stories_folder", "update_model_filter_options",
        ])

    def test_presets_tab_methods(self) -> None:
        self._check_class("tabs.presets_tab", "PresetsTab", [
            "_build", "refresh_presets", "on_preset_selected",
            "create_new_preset", "edit_preset", "delete_preset",
            "apply_preset_to_generate",
        ])

    def test_preset_dialog_methods(self) -> None:
        self._check_class("tabs.presets_tab", "PresetDialog", [
            "save",
        ])

    def test_queue_tab_methods(self) -> None:
        self._check_class("tabs.queue_tab", "QueueTab", [
            "_build", "refresh_queue_list", "refresh_queue_story_options",
            "on_queue_item_selected", "_parse_queue_form",
            "add_queue_item", "update_queue_item", "delete_queue_item",
            "execute_selected_queue_item", "check_queue_worker",
        ])

    def test_statistics_tab_methods(self) -> None:
        self._check_class("tabs.statistics_tab", "StatisticsTab", [
            "_build",
        ])

    def test_thread_tab_methods(self) -> None:
        self._check_class("tabs.thread_tab", "ThreadFormatterTab", [
            "_build",
        ])

    def test_chat_tab_methods(self) -> None:
        self._check_class("tabs.chat_tab", "ChatTab", [
            "_build",
        ])

    def test_novel_tab_methods(self) -> None:
        self._check_class("tabs.novel_tab", "NovelTab", [
            "_build",
        ])


class TestScrollCanvasStructure(unittest.TestCase):
    """Verify ScrollCanvas class is properly defined in gui_app."""

    def test_scrollcanvas_exists(self) -> None:
        from gui_app import ScrollCanvas
        import tkinter as tk
        self.assertTrue(issubclass(ScrollCanvas, tk.Canvas))

    def test_scrollcanvas_methods(self) -> None:
        from gui_app import ScrollCanvas
        self.assertTrue(hasattr(ScrollCanvas, "restore_placeholder"))
        self.assertTrue(hasattr(ScrollCanvas, "_redraw"))


class TestAppClassStructure(unittest.TestCase):
    """Verify StoryGeneratorApp has expected methods and no leftover tab methods."""

    def test_app_has_shared_methods(self) -> None:
        from gui_app import StoryGeneratorApp
        expected = [
            "setup_styles", "_apply_theme", "toggle_dark_mode",
            "on_font_change", "_setup_background_image", "_apply_canvas_bg",
            "create_widgets", "create_status_bar",
            "check_ollama_status", "refresh_models", "_update_models",
            "refresh_saved_stories", "_display_story", "_stats",
        ]
        for method in expected:
            self.assertTrue(
                hasattr(StoryGeneratorApp, method),
                f"StoryGeneratorApp missing: {method}"
            )

    def test_app_no_leftover_tab_methods(self) -> None:
        """Methods that should NOT exist on app after modularization."""
        from gui_app import StoryGeneratorApp
        removed = [
            "create_single_story_tab", "create_batch_tab",
            "create_model_management_tab", "create_saved_stories_tab",
            "create_presets_tab", "create_queue_manager_tab",
            # Handler methods that moved to tabs
            "generate_single_story", "generate_batch",
            "_display_batch_results", "compare_batch_stories",
            "save_all_batch_stories", "save_single_story",
            "copy_story", "clear_story", "_stop_generation",
            "_append_to_story", "_show_validation_report",
            "pull_model",
            "apply_filters", "clear_filters", "on_filtered_story_selected",
            "on_rating_changed", "on_favorite_changed",
            "copy_saved_story", "delete_saved_story",
            "export_story_pdf", "export_story_docx", "export_story_txt",
            "open_stories_folder", "update_model_filter_options",
            "refresh_presets", "on_preset_selected",
            "create_new_preset", "edit_preset", "delete_preset",
            "apply_preset_to_generate",
            "refresh_queue_list", "refresh_queue_story_options",
            "on_queue_item_selected", "_parse_queue_form",
            "add_queue_item", "update_queue_item", "delete_queue_item",
            "execute_selected_queue_item", "check_queue_worker",
        ]
        for method in removed:
            self.assertFalse(
                hasattr(StoryGeneratorApp, method),
                f"StoryGeneratorApp still has leftover method: {method}"
            )

    def test_no_preset_dialog_in_gui_app(self) -> None:
        """PresetDialog should have moved to tabs.presets_tab."""
        import gui_app
        self.assertFalse(hasattr(gui_app, "PresetDialog"))


# ── Phase 2: Instantiation & Bridge Tests (requires display) ─────────────────

def _can_create_tk_root() -> bool:
    """Check if we can create a Tk root (needs display server)."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        return True
    except Exception:
        return False


@unittest.skipUnless(_can_create_tk_root(), "No display available for tkinter")
class TestAppInstantiation(unittest.TestCase):
    """Test that the app creates all tabs and wires bridges correctly."""

    def setUp(self) -> None:
        import tkinter as tk
        self.root = tk.Tk()
        self.root.withdraw()  # don't show window

    def tearDown(self) -> None:
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_app_creates_without_error(self) -> None:
        from gui_app import StoryGeneratorApp
        app = StoryGeneratorApp(self.root)
        self.assertIsNotNone(app)

    def test_all_tab_instances_created(self) -> None:
        from gui_app import StoryGeneratorApp
        app = StoryGeneratorApp(self.root)
        tab_attrs = [
            "_generate_tab", "_batch_tab", "_models_tab", "_saved_tab",
            "_statistics_tab", "_presets_tab", "_queue_tab",
            "_thread_tab", "_chat_tab", "_novel_tab",
        ]
        for attr in tab_attrs:
            self.assertTrue(
                hasattr(app, attr),
                f"App missing tab instance: {attr}"
            )
            self.assertIsNotNone(
                getattr(app, attr),
                f"Tab instance is None: {attr}"
            )

    def test_notebook_has_correct_tab_count(self) -> None:
        from gui_app import StoryGeneratorApp
        app = StoryGeneratorApp(self.root)
        tab_count = app.notebook.index("end")
        self.assertEqual(tab_count, 10, f"Expected 10 tabs, got {tab_count}")

    def test_generate_tab_bridges(self) -> None:
        """Generate tab should bridge key widgets back to app."""
        from gui_app import StoryGeneratorApp
        import tkinter as tk
        app = StoryGeneratorApp(self.root)
        # model_var, model_combo, genre_var, tone_var, template_var,
        # word_count_var, custom_prompt, story_text, scroll_canvas
        self.assertIsInstance(app.model_var, tk.StringVar)
        self.assertIsNotNone(app.model_combo)
        self.assertIsInstance(app.genre_var, tk.StringVar)
        self.assertIsInstance(app.tone_var, tk.StringVar)
        self.assertIsInstance(app.template_var, tk.StringVar)
        self.assertIsInstance(app.word_count_var, tk.IntVar)
        self.assertIsNotNone(app.custom_prompt)
        self.assertIsNotNone(app.story_text)
        self.assertIsNotNone(app.scroll_canvas)

    def test_batch_tab_bridges(self) -> None:
        """Batch tab should bridge models_listbox back to app."""
        from gui_app import StoryGeneratorApp
        import tkinter as tk
        app = StoryGeneratorApp(self.root)
        self.assertIsInstance(app.models_listbox, tk.Listbox)

    def test_models_tab_bridges(self) -> None:
        """Models tab should bridge models_display back to app."""
        from gui_app import StoryGeneratorApp
        import tkinter as tk
        app = StoryGeneratorApp(self.root)
        self.assertIsInstance(app.models_display, tk.Listbox)

    def test_status_bar_created(self) -> None:
        from gui_app import StoryGeneratorApp
        import tkinter as tk
        app = StoryGeneratorApp(self.root)
        self.assertIsInstance(app.status_var, tk.StringVar)
        self.assertIsNotNone(app.dark_mode_button)
        self.assertIsNotNone(app.font_combo)

    def test_shared_state_initialized(self) -> None:
        from gui_app import StoryGeneratorApp
        import threading
        app = StoryGeneratorApp(self.root)
        self.assertIsInstance(app.current_stories, list)
        self.assertFalse(app.is_generating)
        self.assertIsInstance(app._stop_event, threading.Event)
        self.assertTrue(app.dark_mode)

    def test_managers_initialized(self) -> None:
        from gui_app import StoryGeneratorApp
        from story_generator import (
            StoryGenerator, StoriesManager, PresetsManager,
            ContentQueueManager, NovelManager
        )
        app = StoryGeneratorApp(self.root)
        self.assertEqual(app.generator, StoryGenerator)
        self.assertIsInstance(app.stories_manager, StoriesManager)
        self.assertIsInstance(app.presets_manager, PresetsManager)
        self.assertIsInstance(app.queue_manager, ContentQueueManager)
        self.assertIsInstance(app.novel_manager, NovelManager)


@unittest.skipUnless(_can_create_tk_root(), "No display available for tkinter")
class TestProxyMethods(unittest.TestCase):
    """Test that proxy methods on app correctly delegate to tab instances."""

    def setUp(self) -> None:
        import tkinter as tk
        self.root = tk.Tk()
        self.root.withdraw()
        from gui_app import StoryGeneratorApp
        self.app = StoryGeneratorApp(self.root)

    def tearDown(self) -> None:
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_display_story_proxy(self) -> None:
        """app._display_story should delegate to generate tab."""
        test_text = "Once upon a time in a test."
        self.app._display_story(test_text)
        # Verify story_text widget contains the text
        content = self.app.story_text.get("1.0", "end-1c")
        self.assertIn("Once upon a time", content)

    def test_refresh_saved_stories_proxy(self) -> None:
        """app.refresh_saved_stories should not crash."""
        # Just verify it doesn't raise
        self.app.refresh_saved_stories()

    def test_stats_proxy(self) -> None:
        """app._stats should return a dict."""
        stats = self.app._stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("total_stories", stats)


@unittest.skipUnless(_can_create_tk_root(), "No display available for tkinter")
class TestThemeToggle(unittest.TestCase):
    """Test theme toggle still works after modularization."""

    def setUp(self) -> None:
        import tkinter as tk
        self.root = tk.Tk()
        self.root.withdraw()
        from gui_app import StoryGeneratorApp
        self.app = StoryGeneratorApp(self.root)

    def tearDown(self) -> None:
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_toggle_dark_mode(self) -> None:
        from theme import CAVE, LIGHT
        self.assertTrue(self.app.dark_mode)
        self.assertEqual(self.app.C, CAVE)

        self.app.toggle_dark_mode()
        self.assertFalse(self.app.dark_mode)
        self.assertEqual(self.app.C, LIGHT)

        self.app.toggle_dark_mode()
        self.assertTrue(self.app.dark_mode)
        self.assertEqual(self.app.C, CAVE)


if __name__ == "__main__":
    unittest.main()
