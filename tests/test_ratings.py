#!/usr/bin/env python3
"""
Unit tests for story rating and favorites system.
"""
import unittest
import os
import tempfile
from story_generator import StoriesManager


class TestRatingsAndFavorites(unittest.TestCase):
    """Test rating and favorites functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.ratings_file = os.path.join(self.test_dir, "test_ratings.json")
        self.manager = StoriesManager(ratings_file=self.ratings_file, stories_dir=self.test_dir)

        # Create test story files
        self.test_story1 = "test_story1.md"
        self.test_story2 = "test_story2.md"

        story_content = """# Test Story

This is a test story.

**Generated:** 2024-01-01 12:00:00
**Model:** test-model
**Genre:** Test
**Tone:** Neutral

Test content.
"""
        for filename in [self.test_story1, self.test_story2]:
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(story_content)

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_set_and_get_rating(self):
        """Test setting and getting ratings."""
        # Set rating
        success = self.manager.set_rating(self.test_story1, 5)
        self.assertTrue(success)

        # Get rating
        rating = self.manager.get_rating(self.test_story1)
        self.assertEqual(rating, 5)

    def test_rating_bounds(self):
        """Test rating bounds validation."""
        # Valid ratings
        self.assertTrue(self.manager.set_rating(self.test_story1, 0))  # Remove rating
        self.assertTrue(self.manager.set_rating(self.test_story1, 1))
        self.assertTrue(self.manager.set_rating(self.test_story1, 3))
        self.assertTrue(self.manager.set_rating(self.test_story1, 5))

        # Invalid ratings
        self.assertFalse(self.manager.set_rating(self.test_story1, -1))
        self.assertFalse(self.manager.set_rating(self.test_story1, 6))

    def test_set_and_get_favorite(self):
        """Test setting and getting favorites."""
        # Set as favorite
        success = self.manager.set_favorite(self.test_story1, True)
        self.assertTrue(success)

        # Check favorite status
        is_fav = self.manager.get_favorite(self.test_story1)
        self.assertTrue(is_fav)

        # Remove favorite
        success = self.manager.set_favorite(self.test_story1, False)
        self.assertTrue(success)
        is_fav = self.manager.get_favorite(self.test_story1)
        self.assertFalse(is_fav)

    def test_rating_persistence(self):
        """Test that ratings persist across manager instances."""
        # Set rating with first manager
        self.manager.set_rating(self.test_story1, 4)
        self.manager.set_favorite(self.test_story1, True)

        # Create new manager
        manager2 = StoriesManager(ratings_file=self.ratings_file)
        self.assertEqual(manager2.get_rating(self.test_story1), 4)
        self.assertTrue(manager2.get_favorite(self.test_story1))

    def test_get_rating_stats(self):
        """Test rating statistics calculation."""
        # Set some ratings
        self.manager.set_rating(self.test_story1, 5)
        self.manager.set_rating(self.test_story2, 3)
        self.manager.set_favorite(self.test_story1, True)

        stats = self.manager.get_rating_stats()
        self.assertEqual(stats['total_rated'], 2)
        self.assertAlmostEqual(stats['average'], 4.0, places=1)
        self.assertEqual(stats['favorites'], 1)
        self.assertEqual(stats['distribution'][5], 1)
        self.assertEqual(stats['distribution'][3], 1)

    def test_filter_by_rating(self):
        """Test filtering stories by minimum rating."""
        self.manager.set_rating(self.test_story1, 5)
        self.manager.set_rating(self.test_story2, 2)

        # Filter for rating >= 4
        filtered = self.manager.filter_stories(min_rating=4)
        filenames = [s['filename'] for s in filtered]
        self.assertIn(self.test_story1, filenames)
        self.assertNotIn(self.test_story2, filenames)

    def test_filter_by_favorites(self):
        """Test filtering stories by favorites."""
        self.manager.set_favorite(self.test_story1, True)
        self.manager.set_favorite(self.test_story2, False)

        # Filter for favorites only
        filtered = self.manager.filter_stories(favorites_only=True)
        filenames = [s['filename'] for s in filtered]
        self.assertIn(self.test_story1, filenames)
        self.assertNotIn(self.test_story2, filenames)

    def test_unrated_story(self):
        """Test behavior with unrated stories."""
        # No rating set
        rating = self.manager.get_rating(self.test_story1)
        self.assertEqual(rating, 0)

        is_fav = self.manager.get_favorite(self.test_story1)
        self.assertFalse(is_fav)

    def test_invalid_rating_values_in_file(self):
        """Test handling of corrupted rating data."""
        # Manually create corrupted ratings file
        import json
        corrupted_data = {
            self.test_story1: {
                'rating': 10,  # Invalid rating
                'favorite': "not_a_boolean"  # Invalid favorite
            }
        }
        with open(self.ratings_file, 'w') as f:
            json.dump(corrupted_data, f)

        # Create new manager - should handle corruption gracefully
        manager2 = StoriesManager(ratings_file=self.ratings_file)

        # Should be corrected to valid values
        self.assertEqual(manager2.get_rating(self.test_story1), 0)  # Reset to 0
        self.assertFalse(manager2.get_favorite(self.test_story1))  # Reset to False


if __name__ == '__main__':
    unittest.main()
