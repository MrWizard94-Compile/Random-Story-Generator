#!/usr/bin/env python3
"""
Unit tests for presets functionality.
"""
import unittest
import os
import tempfile
from story_generator import PresetsManager


class TestPresetsFunctionality(unittest.TestCase):
    """Test preset management functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.manager = PresetsManager(presets_dir=self.test_dir)

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_preset(self):
        """Test saving a preset."""
        success = self.manager.save_preset(
            name="Mystery Thriller",
            genre="Mystery",
            tone="Dark",
            word_count=800,
            custom_prompt="Write a suspenseful mystery story with unexpected twists."
        )
        self.assertTrue(success)

    def test_get_presets(self):
        """Test getting all presets."""
        # Initially empty
        presets = self.manager.get_presets()
        self.assertEqual(len(presets), 0)

        # Add a preset
        self.manager.save_preset("Test Preset", genre="Test", tone="Neutral", word_count=500)
        presets = self.manager.get_presets()
        self.assertEqual(len(presets), 1)
        self.assertEqual(presets[0]['name'], "Test Preset")

    def test_get_preset(self):
        """Test getting a specific preset."""
        # Preset doesn't exist
        preset = self.manager.get_preset("Nonexistent")
        self.assertIsNone(preset)

        # Add and retrieve preset
        self.manager.save_preset(
            name="Mystery Thriller",
            genre="Mystery",
            tone="Dark",
            word_count=800,
            custom_prompt="Write a suspenseful mystery story."
        )

        preset = self.manager.get_preset("Mystery Thriller")
        self.assertIsNotNone(preset)
        self.assertEqual(preset['name'], "Mystery Thriller")
        self.assertEqual(preset['genre'], "Mystery")
        self.assertEqual(preset['tone'], "Dark")
        self.assertEqual(preset['word_count'], 800)
        self.assertEqual(preset['custom_prompt'], "Write a suspenseful mystery story.")

    def test_get_preset_exact_name(self):
        """Test getting preset with exact name match."""
        self.manager.save_preset("Test Preset", genre="Test")

        preset = self.manager.get_preset("Test Preset")
        self.assertIsNotNone(preset)
        self.assertEqual(preset['name'], "Test Preset")

        # Different case should NOT match (API is case-sensitive)
        preset_wrong_case = self.manager.get_preset("test preset")
        self.assertIsNone(preset_wrong_case)

    def test_delete_preset(self):
        """Test deleting a preset."""
        # Add a preset
        self.manager.save_preset("Test Preset", genre="Test")
        self.assertEqual(len(self.manager.get_presets()), 1)

        # Delete it
        success = self.manager.delete_preset("Test Preset")
        self.assertTrue(success)
        self.assertEqual(len(self.manager.get_presets()), 0)

    def test_delete_nonexistent_preset(self):
        """Test deleting a preset that doesn't exist."""
        success = self.manager.delete_preset("Nonexistent")
        self.assertFalse(success)

    def test_preset_persistence(self):
        """Test that presets persist across manager instances."""
        # Save with first manager
        self.manager.save_preset("Persistent", genre="Test", word_count=600)

        # Create new manager with same file
        manager2 = PresetsManager(presets_dir=self.test_dir)
        presets = manager2.get_presets()
        self.assertEqual(len(presets), 1)
        self.assertEqual(presets[0]['name'], "Persistent")
        self.assertEqual(presets[0]['word_count'], 600)

    def test_save_duplicate_preset(self):
        """Test saving a preset with a name that already exists."""
        # Save first preset
        success1 = self.manager.save_preset("Duplicate", genre="Original")
        self.assertTrue(success1)

        # Try to save duplicate - should fail
        success2 = self.manager.save_preset("Duplicate", genre="Updated")
        self.assertFalse(success2)

        # Should still have only one preset with original values
        presets = self.manager.get_presets()
        self.assertEqual(len(presets), 1)
        self.assertEqual(presets[0]['genre'], "Original")


if __name__ == '__main__':
    unittest.main()