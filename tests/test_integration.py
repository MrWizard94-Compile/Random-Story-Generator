#!/usr/bin/env python3
"""
Integration tests for end-to-end story generation workflows.
"""
import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import patch, MagicMock
from story_generator import StoryGenerator, StoriesManager, PresetsManager


class TestIntegrationWorkflows(unittest.TestCase):
    """Test complete user workflows from generation to export."""

    def setUp(self):
        """Set up test fixtures for integration testing."""
        self.test_dir = tempfile.mkdtemp()
        self.stories_dir = os.path.join(self.test_dir, "stories")
        self.ratings_file = os.path.join(self.test_dir, "ratings.json")
        self.presets_file = os.path.join(self.test_dir, "presets.json")

        # Initialize managers with test paths
        self.stories_manager = StoriesManager(
            ratings_file=self.ratings_file,
            stories_dir=self.stories_dir
        )
        self.presets_manager = PresetsManager(presets_dir=self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('story_generator.requests.post')
    def test_complete_story_generation_workflow(self, mock_post):
        """Test complete workflow: generate → save → rate → export."""
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'Once upon a time, a brave knight saved the kingdom from evil.'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Step 1: Generate story
        story_text, model_used = StoryGenerator.generate_story(
            model='llama2',
            genre='Fantasy',
            tone='Heroic',
            word_count=50
        )

        self.assertIsInstance(story_text, str)
        self.assertEqual(model_used, 'llama2')
        self.assertIn('brave knight', story_text)

        # Step 2: Save story
        saved_path = self.stories_manager.save_story(
            story_text=story_text,
            model='llama2',
            genre='Fantasy',
            tone='Heroic'
        )

        self.assertTrue(os.path.exists(saved_path))
        self.assertTrue(saved_path.endswith('.md'))

        # Extract filename from path
        filename = os.path.basename(saved_path)

        # Step 3: Verify story was saved and can be loaded
        loaded_content = self.stories_manager.load_story(filename)
        self.assertIsNotNone(loaded_content)
        self.assertIn('brave knight', loaded_content)

        # Step 4: Get metadata
        metadata = self.stories_manager.get_story_metadata(filename)
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['model'], 'llama2')
        self.assertEqual(metadata['genre'], 'Fantasy')
        self.assertEqual(metadata['tone'], 'Heroic')

        # Step 5: Rate the story
        success = self.stories_manager.set_rating(filename, 5)
        self.assertTrue(success)

        rating = self.stories_manager.get_rating(filename)
        self.assertEqual(rating, 5)

        # Step 6: Mark as favorite
        success = self.stories_manager.set_favorite(filename, True)
        self.assertTrue(success)

        is_fav = self.stories_manager.get_favorite(filename)
        self.assertTrue(is_fav)

        # Step 7: Export to different formats
        pdf_path = self.stories_manager.export_to_pdf(filename)
        self.assertTrue(os.path.exists(pdf_path))
        self.assertTrue(pdf_path.endswith('.pdf'))

        txt_path = self.stories_manager.export_to_txt(filename)
        self.assertTrue(os.path.exists(txt_path))
        self.assertTrue(txt_path.endswith('.txt'))

        # Step 8: Verify ratings persist across manager instances
        new_manager = StoriesManager(
            ratings_file=self.ratings_file,
            stories_dir=self.stories_dir
        )

        self.assertEqual(new_manager.get_rating(filename), 5)
        self.assertTrue(new_manager.get_favorite(filename))

    @patch('story_generator.requests.post')
    def test_preset_based_generation_workflow(self, mock_post):
        """Test workflow using presets: create preset → generate → save."""
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'A mysterious tale in the dark forest.'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Step 1: Create and save a preset
        success = self.presets_manager.save_preset(
            name="Mystery Forest",
            genre="Mystery",
            tone="Dark",
            word_count=75,
            custom_prompt="Write about a mysterious forest"
        )
        self.assertTrue(success)

        # Step 2: Retrieve preset
        preset = self.presets_manager.get_preset("Mystery Forest")
        self.assertIsNotNone(preset)
        self.assertEqual(preset['genre'], "Mystery")
        self.assertEqual(preset['tone'], "Dark")
        self.assertEqual(preset['word_count'], 75)

        # Step 3: Generate story using preset data
        story_text, model_used = StoryGenerator.generate_story(
            model='llama2',
            genre=preset['genre'],
            tone=preset['tone'],
            word_count=preset['word_count'],
            custom_prompt=preset['custom_prompt']
        )

        self.assertIsInstance(story_text, str)
        self.assertIn('mysterious', story_text.lower())

        # Step 4: Save generated story
        saved_path = self.stories_manager.save_story(
            story_text=story_text,
            model='llama2',
            genre=preset['genre'],
            tone=preset['tone']
        )

        self.assertTrue(os.path.exists(saved_path))

        # Step 5: Verify preset persists across manager instances
        new_presets_manager = PresetsManager(presets_dir=self.test_dir)
        preset_copy = new_presets_manager.get_preset("Mystery Forest")
        self.assertIsNotNone(preset_copy)
        self.assertEqual(preset_copy['genre'], "Mystery")

    def test_story_filtering_and_statistics(self):
        """Test story filtering and statistics generation."""
        # Create test story files manually
        story1_content = """---
**Generated:** 2024-01-15 10:00:00
**Model:** llama2
**Genre:** Fantasy
**Tone:** Heroic
---

# Test Story 1

This is a fantasy story about heroes.
"""

        story2_content = """---
**Generated:** 2024-01-16 11:00:00
**Model:** mistral
**Genre:** Mystery
**Tone:** Dark
---

# Test Story 2

This is a mystery story in the dark.
"""

        # Save stories
        path1 = os.path.join(self.stories_dir, "story1.md")
        path2 = os.path.join(self.stories_dir, "story2.md")

        os.makedirs(self.stories_dir, exist_ok=True)
        with open(path1, 'w', encoding='utf-8') as f:
            f.write(story1_content)
        with open(path2, 'w', encoding='utf-8') as f:
            f.write(story2_content)

        # Rate stories
        self.stories_manager.set_rating("story1.md", 5)
        self.stories_manager.set_favorite("story1.md", True)
        self.stories_manager.set_rating("story2.md", 3)

        # Test filtering by rating
        high_rated = self.stories_manager.filter_stories(min_rating=4)
        self.assertEqual(len(high_rated), 1)
        self.assertEqual(high_rated[0]['filename'], 'story1.md')

        # Test filtering by favorites
        favorites = self.stories_manager.filter_stories(favorites_only=True)
        self.assertEqual(len(favorites), 1)
        self.assertEqual(favorites[0]['filename'], 'story1.md')

        # Test filtering by genre
        fantasy_stories = self.stories_manager.filter_stories(genre="Fantasy")
        self.assertEqual(len(fantasy_stories), 1)
        self.assertEqual(fantasy_stories[0]['filename'], 'story1.md')

        # Test statistics
        stats = self.stories_manager.get_rating_stats()
        self.assertEqual(stats['total_rated'], 2)
        self.assertEqual(stats['favorites'], 1)
        self.assertEqual(stats['distribution'][5], 1)
        self.assertEqual(stats['distribution'][3], 1)

    @patch('story_generator.requests.post')
    def test_bulk_story_generation_and_management(self, mock_post):
        """Test generating multiple stories and managing them."""
        # Mock response for story generation
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'A generated story about adventure.'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        generated_stories = []

        # Generate multiple stories
        for i in range(3):
            story_text, model_used = StoryGenerator.generate_story(
                model='llama2',
                genre=f'Genre{i}',
                tone=f'Tone{i}',
                word_count=30 + i * 10
            )

            # Save each story with explicit filename to avoid timestamp collisions
            filename = f"bulk_story_{i}.md"
            saved_path = self.stories_manager.save_story(
                story_text=story_text,
                model='llama2',
                genre=f'Genre{i}',
                tone=f'Tone{i}',
                filename=filename
            )

            generated_stories.append(filename)

            # Rate each story differently
            self.stories_manager.set_rating(filename, i + 1)

        # Verify all stories were saved
        self.assertEqual(len(generated_stories), 3)

        # Verify all stories can be retrieved
        all_stories = self.stories_manager.get_all_stories_metadata()
        self.assertEqual(len(all_stories), 3)

        # Test sorting by rating
        sorted_stories = self.stories_manager.filter_stories(sort_by='rating_desc')
        self.assertEqual(len(sorted_stories), 3)
        # Should be sorted highest rating first
        self.assertEqual(sorted_stories[0]['rating'], 3)

    def test_error_handling_integration(self):
        """Test error handling across components."""
        # Test loading non-existent story
        result = self.stories_manager.load_story("nonexistent.md")
        self.assertIsNone(result)

        # Test getting metadata for non-existent story
        metadata = self.stories_manager.get_story_metadata("nonexistent.md")
        self.assertIsNone(metadata)

        # Test rating non-existent story
        success = self.stories_manager.set_rating("nonexistent.md", 5)
        self.assertTrue(success)  # Should succeed but not crash

        # Test exporting non-existent story
        with self.assertRaises(Exception):
            self.stories_manager.export_to_pdf("nonexistent.md")

        # Test getting non-existent preset
        preset = self.presets_manager.get_preset("nonexistent")
        self.assertIsNone(preset)

        # Test deleting non-existent preset
        success = self.presets_manager.delete_preset("nonexistent")
        self.assertFalse(success)

    def test_cross_component_data_integrity(self):
        """Test that data integrity is maintained across component interactions."""
        # Create a story file manually
        story_content = """---
**Generated:** 2024-01-20 12:00:00
**Model:** test-model
**Genre:** Integration
**Tone:** Test
---

# Integration Test Story

This is a test story for integration testing.
"""

        story_path = os.path.join(self.stories_dir, "integration_test.md")
        os.makedirs(self.stories_dir, exist_ok=True)
        with open(story_path, 'w', encoding='utf-8') as f:
            f.write(story_content)

        filename = "integration_test.md"

        # Test that metadata extraction works
        metadata = self.stories_manager.get_story_metadata(filename)
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['title'], 'Integration Test Story')
        self.assertEqual(metadata['model'], 'test-model')
        self.assertEqual(metadata['genre'], 'Integration')

        # Test that story appears in listings
        all_stories = self.stories_manager.get_all_stories_metadata()
        self.assertEqual(len(all_stories), 1)
        self.assertEqual(all_stories[0]['filename'], filename)

        # Add rating to create the ratings file
        self.stories_manager.set_rating(filename, 4)

        # Test that ratings file is created and maintained
        self.assertTrue(os.path.exists(self.ratings_file))

        # Add rating and verify persistence
        self.stories_manager.set_rating(filename, 4)
        self.stories_manager.set_favorite(filename, True)

        # Create new manager instance and verify data persists
        new_manager = StoriesManager(
            ratings_file=self.ratings_file,
            stories_dir=self.stories_dir
        )

        self.assertEqual(new_manager.get_rating(filename), 4)
        self.assertTrue(new_manager.get_favorite(filename))

        # Verify ratings file contains correct data
        with open(self.ratings_file, 'r', encoding='utf-8') as f:
            ratings_data = json.load(f)

        expected_key = filename
        self.assertIn(expected_key, ratings_data)
        self.assertEqual(ratings_data[expected_key]['rating'], 4)
        self.assertTrue(ratings_data[expected_key]['favorite'])


if __name__ == '__main__':
    unittest.main()