#!/usr/bin/env python3
"""
Unit tests for story generator components.
"""
import unittest
from story_generator import DEFAULT_WORD_COUNT, DEFAULT_MAX_CHARS, RAPID_MODE_WORD_COUNT
from story_generator import StoryMetrics

class TestConstants(unittest.TestCase):
    """Test that constants are properly defined."""

    def test_default_constants(self):
        """Test that default constants have expected values."""
        self.assertEqual(DEFAULT_WORD_COUNT, 500)
        self.assertEqual(DEFAULT_MAX_CHARS, 280)
        self.assertEqual(RAPID_MODE_WORD_COUNT, 300)

class TestStoryMetrics(unittest.TestCase):
    """Test story metrics calculations."""

    def test_calculate_metrics_basic(self):
        """Test basic metrics calculation."""
        metrics = StoryMetrics.calculate_metrics("The cat sat on the mat. It was happy.")
        self.assertIn('word_count', metrics)
        self.assertIn('sentence_count', metrics)
        self.assertIn('readability_score', metrics)
        self.assertEqual(metrics['word_count'], 9)
        self.assertEqual(metrics['sentence_count'], 2)

    def test_calculate_metrics_empty_text(self):
        """Test that calculate_metrics handles empty text without division by zero."""
        result = StoryMetrics.calculate_metrics("")
        self.assertEqual(result['word_count'], 0)
        self.assertEqual(result['sentence_count'], 0)
        self.assertEqual(result['readability_score'], 0)

        result = StoryMetrics.calculate_metrics("   ")
        self.assertEqual(result['word_count'], 0)

if __name__ == '__main__':
    unittest.main()