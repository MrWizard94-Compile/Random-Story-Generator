#!/usr/bin/env python3
"""
Quality Assurance and Edge Cases tests.
"""
import unittest
import tempfile
import os
import json
import time
import shutil
from unittest.mock import patch, MagicMock
from story_generator import StoryGenerator, StoriesManager, PresetsManager, StoryMetrics


class TestQualityAssurance(unittest.TestCase):
    """Comprehensive QA testing for edge cases, performance, and error scenarios."""

    def setUp(self):
        """Set up test fixtures for QA testing."""
        self.test_dir = tempfile.mkdtemp()
        self.stories_dir = os.path.join(self.test_dir, "stories")
        self.ratings_file = os.path.join(self.test_dir, "ratings.json")
        self.presets_file = os.path.join(self.test_dir, "presets.json")

        self.stories_manager = StoriesManager(
            ratings_file=self.ratings_file,
            stories_dir=self.stories_dir
        )
        self.presets_manager = PresetsManager(presets_dir=self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_empty_and_whitespace_inputs(self):
        """Test handling of empty and whitespace inputs."""
        # Test empty story text - currently allowed, but should create file
        saved_path = self.stories_manager.save_story("", model="test")
        self.assertTrue(os.path.exists(saved_path))

        # Test whitespace-only story text - currently allowed
        saved_path2 = self.stories_manager.save_story("   \n\t  ", model="test")
        self.assertTrue(os.path.exists(saved_path2))

        # Test empty filename - should generate default
        saved_path3 = self.stories_manager.save_story("Test", model="test")
        self.assertTrue(os.path.exists(saved_path3))
        self.assertIn("story_", os.path.basename(saved_path3))

        # Test None filename - should generate default
        saved_path4 = self.stories_manager.save_story("Test", model="test", filename=None)
        self.assertTrue(os.path.exists(saved_path4))

    def test_extremely_long_inputs(self):
        """Test handling of very long inputs."""
        # Very long story text
        long_story = "This is a test story. " * 1000  # ~25KB of text
        saved_path = self.stories_manager.save_story(long_story, model="test")
        self.assertTrue(os.path.exists(saved_path))

        # Load and verify
        loaded = self.stories_manager.load_story(os.path.basename(saved_path))
        self.assertIsNotNone(loaded)
        self.assertIn(long_story[:100], loaded)  # Verify content is preserved

        # Very long filename
        long_filename = "a" * 200 + ".md"
        saved_path2 = self.stories_manager.save_story("Test", model="test", filename=long_filename)
        self.assertTrue(os.path.exists(saved_path2))

    def test_special_characters_and_unicode(self):
        """Test handling of special characters and Unicode text."""
        # Unicode story with emojis and special chars
        unicode_story = "🚀 🌟 Unicode Test: naïve, résumé, México, 日本語, العربية 🌟 🚀"
        saved_path = self.stories_manager.save_story(unicode_story, model="test")
        self.assertTrue(os.path.exists(saved_path))

        # Load and verify Unicode preservation
        loaded = self.stories_manager.load_story(os.path.basename(saved_path))
        self.assertIn("🚀", loaded)
        self.assertIn("日本語", loaded)
        self.assertIn("العربية", loaded)

        # Special characters in metadata
        special_genre = "Sci-Fi/Fantasy & Adventure!"
        special_tone = "Dark & Mysterious (2024 Edition)"
        saved_path2 = self.stories_manager.save_story(
            "Special chars test",
            model="test",
            genre=special_genre,
            tone=special_tone
        )

        metadata = self.stories_manager.get_story_metadata(os.path.basename(saved_path2))
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['genre'], special_genre)
        self.assertEqual(metadata['tone'], special_tone)

    def test_boundary_conditions(self):
        """Test boundary conditions and limits."""
        # Word count boundaries
        self.assertEqual(StoryMetrics.calculate_metrics("")['readability_score'], 0)
        # Whitespace-only text doesn't hit the empty-text short-circuit,
        # so readability_score is calculated (0 words/sentence → score of 10)
        whitespace_metrics = StoryMetrics.calculate_metrics("   ")
        self.assertIsInstance(whitespace_metrics['readability_score'], (int, float))

        # Single word
        metrics = StoryMetrics.calculate_metrics("Hello")
        self.assertEqual(metrics['word_count'], 1)
        self.assertEqual(metrics['sentence_count'], 1)

        # Very short sentences
        short_text = "Hi. Bye."
        metrics = StoryMetrics.calculate_metrics(short_text)
        self.assertGreater(metrics['word_count'], 0)

        # Rating boundaries
        filename = "boundary_test.md"
        self.stories_manager.save_story("Test", model="test", filename=filename)

        # Valid ratings
        for rating in [0, 1, 2, 3, 4, 5]:
            success = self.stories_manager.set_rating(filename, rating)
            self.assertTrue(success)
            self.assertEqual(self.stories_manager.get_rating(filename), rating)

        # Invalid ratings
        self.assertFalse(self.stories_manager.set_rating(filename, -1))
        self.assertFalse(self.stories_manager.set_rating(filename, 6))
        self.assertFalse(self.stories_manager.set_rating(filename, 10))

    @patch('story_generator.requests.post')
    def test_network_error_recovery(self, mock_post):
        """Test recovery from network errors."""
        # Connection timeout
        mock_post.side_effect = Exception("Connection timeout")

        with self.assertRaises(Exception):
            StoryGenerator.generate_story(model="test")

        # HTTP error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 500")
        mock_post.return_value = mock_response

        with self.assertRaises(Exception):
            StoryGenerator.generate_story(model="test")

        # Malformed JSON response
        mock_response2 = MagicMock()
        mock_response2.raise_for_status.return_value = None
        mock_response2.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_post.return_value = mock_response2

        with self.assertRaises(Exception):
            StoryGenerator.generate_story(model="test")

    def test_file_system_error_recovery(self):
        """Test recovery from file system errors."""
        # Try to save to read-only directory (if possible)
        # For now, test with valid operations

        # Test loading corrupted file
        corrupted_path = os.path.join(self.stories_dir, "corrupted.md")
        os.makedirs(self.stories_dir, exist_ok=True)
        with open(corrupted_path, 'wb') as f:
            f.write(b'\x00\x01\x02Invalid UTF-8\x80\x81')

        # Should handle gracefully
        metadata = self.stories_manager.get_story_metadata("corrupted.md")
        self.assertIsNotNone(metadata)  # Should return default metadata

    def test_concurrent_operations_simulation(self):
        """Test that ratings persist correctly across manager instances."""
        # Use unique files for this test to avoid interference
        test_dir = tempfile.mkdtemp()
        try:
            stories_dir = os.path.join(test_dir, "stories")
            ratings_file = os.path.join(test_dir, "ratings.json")

            # Save a story and rate it
            manager1 = StoriesManager(ratings_file=ratings_file, stories_dir=stories_dir)
            path1 = manager1.save_story("Story 1", model="test1")
            filename1 = os.path.basename(path1)
            manager1.set_rating(filename1, 5)

            # Force save and ensure file exists
            import time
            time.sleep(0.1)  # Small delay to ensure file operations complete

            # Create a new manager instance (simulating a new session)
            manager_new = StoriesManager(ratings_file=ratings_file, stories_dir=stories_dir)

            # New manager should see the rating
            self.assertEqual(manager_new.get_rating(filename1), 5)

            # New manager adds another story and rates it
            path2 = manager_new.save_story("Story 2", model="test2", filename="story_2.md")
            filename2 = os.path.basename(path2)
            manager_new.set_rating(filename2, 4)

            # Force save
            time.sleep(0.1)

            # Test persistence by creating another new manager
            manager_final = StoriesManager(ratings_file=ratings_file, stories_dir=stories_dir)

            self.assertEqual(manager_final.get_rating(filename1), 5)
            self.assertEqual(manager_final.get_rating(filename2), 4)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_data_corruption_recovery(self):
        """Test recovery from corrupted data files."""
        # Create corrupted ratings file
        corrupted_ratings = {
            "story1.md": {
                "rating": "not_a_number",  # Invalid rating
                "favorite": "not_a_boolean"  # Invalid favorite
            },
            "story2.md": {
                "rating": 10,  # Out of range
                "favorite": True
            }
        }

        with open(self.ratings_file, 'w') as f:
            json.dump(corrupted_ratings, f)

        # Create new manager - should recover gracefully
        manager = StoriesManager(
            ratings_file=self.ratings_file,
            stories_dir=self.stories_dir
        )

        # Should have corrected invalid data
        self.assertEqual(manager.get_rating("story1.md"), 0)  # Reset invalid rating
        self.assertFalse(manager.get_favorite("story1.md"))  # Reset invalid favorite
        self.assertEqual(manager.get_rating("story2.md"), 0)  # Reset out-of-range rating
        self.assertTrue(manager.get_favorite("story2.md"))  # Keep valid favorite

    def test_preset_edge_cases(self):
        """Test preset management edge cases."""
        # Empty preset name - currently allowed
        success = self.presets_manager.save_preset("", genre="Test")
        self.assertTrue(success)  # Currently doesn't validate

        preset = self.presets_manager.get_preset("")
        self.assertIsNotNone(preset)

        # Whitespace-only name - currently allowed
        success = self.presets_manager.save_preset("   ", genre="Test")
        self.assertTrue(success)

        # Very long preset name
        long_name = "A" * 200
        success = self.presets_manager.save_preset(long_name, genre="Test")
        self.assertTrue(success)

        preset = self.presets_manager.get_preset(long_name)
        self.assertIsNotNone(preset)

        # Case sensitivity
        success1 = self.presets_manager.save_preset("TestPreset", genre="Fantasy")
        self.assertTrue(success1)

        # API is case-sensitive — different case is a different preset
        preset_exact = self.presets_manager.get_preset("TestPreset")
        preset_lower = self.presets_manager.get_preset("testpreset")

        self.assertIsNotNone(preset_exact)
        self.assertIsNone(preset_lower)  # Case mismatch returns None
        self.assertEqual(preset_exact['genre'], "Fantasy")

    @patch('story_generator.requests.post')
    def test_performance_baseline(self, mock_post):
        """Test performance baseline for operations."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'Performance test story.'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Time story generation
        start_time = time.time()
        story_text, model_used = StoryGenerator.generate_story(
            model='test-model',
            word_count=100
        )
        generation_time = time.time() - start_time

        # Should complete in reasonable time (allow generous limit for CI)
        self.assertLess(generation_time, 5.0)  # 5 seconds max
        # Note: Mocked calls may be very fast, so we don't enforce minimum time

        # Time story saving
        start_time = time.time()
        saved_path = self.stories_manager.save_story(story_text, model='test-model')
        save_time = time.time() - start_time

        self.assertLess(save_time, 1.0)  # 1 second max for saving

        # Time metadata extraction
        start_time = time.time()
        metadata = self.stories_manager.get_story_metadata(os.path.basename(saved_path))
        metadata_time = time.time() - start_time

        self.assertLess(metadata_time, 0.5)  # 500ms max for metadata

    def test_bulk_operations_load(self):
        """Test bulk operations under load."""
        # Create many stories
        story_count = 10  # Reasonable number for testing

        for i in range(story_count):
            content = f"Story content {i} with some text to make it longer."
            filename = f"bulk_test_{i}.md"
            self.stories_manager.save_story(content, model="bulk-test", filename=filename)

        # Verify all were saved
        all_stories = self.stories_manager.get_all_stories_metadata()
        self.assertEqual(len(all_stories), story_count)

        # Bulk rating operations
        for i in range(story_count):
            filename = f"bulk_test_{i}.md"
            rating = (i % 5) + 1  # Ratings 1-5
            self.stories_manager.set_rating(filename, rating)

        # Verify ratings
        for i in range(story_count):
            filename = f"bulk_test_{i}.md"
            expected_rating = (i % 5) + 1
            self.assertEqual(self.stories_manager.get_rating(filename), expected_rating)

        # Test bulk filtering
        high_rated = self.stories_manager.filter_stories(min_rating=4)
        # Should have stories with ratings 4 and 5
        expected_high_rated = sum(1 for i in range(story_count) if (i % 5) + 1 >= 4)
        self.assertEqual(len(high_rated), expected_high_rated)

    def test_memory_and_resource_usage(self):
        """Test for memory leaks and resource usage issues."""
        # Create stories with varying sizes
        sizes = [100, 1000, 10000]  # Characters

        for size in sizes:
            content = "A" * size
            saved_path = self.stories_manager.save_story(content, model="memory-test")
            self.assertTrue(os.path.exists(saved_path))

            # Load and verify
            loaded = self.stories_manager.load_story(os.path.basename(saved_path))
            self.assertIsNotNone(loaded)

            # Verify size is reasonable (allow for metadata overhead)
            self.assertGreater(len(loaded), size - 100)

        # Test metrics calculation on large text
        large_text = "This is a test sentence. " * 1000  # ~30KB
        metrics = StoryMetrics.calculate_metrics(large_text)

        self.assertIsInstance(metrics, dict)
        self.assertGreater(metrics['word_count'], 1000)
        self.assertGreater(metrics['sentence_count'], 0)  # Just check it's positive

    def test_invalid_metadata_formats(self):
        """Test handling of various invalid metadata formats."""
        # Story with malformed frontmatter
        malformed_story = """---
**Generated:** invalid-date
**Model:** test
**Genre:** Test
---

# Malformed Story

Content here.
"""

        malformed_path = os.path.join(self.stories_dir, "malformed.md")
        os.makedirs(self.stories_dir, exist_ok=True)
        with open(malformed_path, 'w', encoding='utf-8') as f:
            f.write(malformed_story)

        # Should handle gracefully
        metadata = self.stories_manager.get_story_metadata("malformed.md")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['model'], 'test')  # Should still extract valid fields
        self.assertIsNone(metadata['generated_date'])  # Invalid date should be None

        # Story with missing frontmatter
        no_frontmatter = """# Story Without Frontmatter

Just plain content.
"""

        no_fm_path = os.path.join(self.stories_dir, "no_frontmatter.md")
        with open(no_fm_path, 'w', encoding='utf-8') as f:
            f.write(no_frontmatter)

        metadata2 = self.stories_manager.get_story_metadata("no_frontmatter.md")
        self.assertIsNotNone(metadata2)
        self.assertEqual(metadata2['title'], 'Story Without Frontmatter')

    def test_export_edge_cases(self):
        """Test export functionality with edge cases."""
        # Create story with special content
        special_content = """# Special Story

**Special characters:** àáâãäå, èéêë, ìíîï, òóôõö
**Emojis:** 😀 🎉 🚀 🌟
**Symbols:** © ® ™ ∞ ∑ √ ∫
**Quotes:** "Hello" 'World'
**Newlines and tabs:**\n\tIndented text
"""

        saved_path = self.stories_manager.save_story(special_content, model="special")
        filename = os.path.basename(saved_path)

        # Test PDF export
        pdf_path = self.stories_manager.export_to_pdf(filename)
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 1000)  # Should be substantial

        # Test TXT export
        txt_path = self.stories_manager.export_to_txt(filename)
        self.assertTrue(os.path.exists(txt_path))

        # Verify TXT content includes special characters
        with open(txt_path, 'r', encoding='utf-8') as f:
            txt_content = f.read()
            self.assertIn("àáâãäå", txt_content)
            self.assertIn("😀", txt_content)
            self.assertIn("© ® ™", txt_content)

    def test_filtering_edge_cases(self):
        """Test story filtering with edge cases."""
        # Create stories with various metadata
        stories_data = [
            ("story1.md", "Fantasy", "Heroic", "model1"),
            ("story2.md", "Mystery", "Dark", "model2"),
            ("story3.md", None, "Light", "model1"),  # No genre
            ("story4.md", "Sci-Fi", None, "model2"),  # No tone
        ]

        for filename, genre, tone, model in stories_data:
            self.stories_manager.save_story(
                f"Content for {filename}",
                model=model,
                genre=genre,
                tone=tone,
                filename=filename
            )

        # Test filtering by existing genre
        fantasy_stories = self.stories_manager.filter_stories(genre="Fantasy")
        self.assertEqual(len(fantasy_stories), 1)
        self.assertEqual(fantasy_stories[0]['filename'], 'story1.md')

        # Test filtering by non-existent genre
        none_stories = self.stories_manager.filter_stories(genre="NonExistent")
        self.assertEqual(len(none_stories), 0)

        # Test filtering by model
        model1_stories = self.stories_manager.filter_stories(model="model1")
        self.assertEqual(len(model1_stories), 2)

        # Test complex filtering
        complex_filter = self.stories_manager.filter_stories(
            genre="Fantasy",
            model="model1"
        )
        self.assertEqual(len(complex_filter), 1)


if __name__ == '__main__':
    unittest.main()