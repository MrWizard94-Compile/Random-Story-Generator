#!/usr/bin/env python3
"""
Unit tests for story generation functionality.
"""
import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
from story_generator import StoryGenerator, DEFAULT_WORD_COUNT, StoryMetrics


class TestStoryGeneration(unittest.TestCase):
    """Test story generation functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('story_generator.requests.post')
    def test_generate_story_success(self, mock_post):
        """Test successful story generation."""
        # Mock the requests response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': 'Once upon a time, there was a brave knight who saved the kingdom.'
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Generate story
        story_text, model_used = StoryGenerator.generate_story(
            model='test-model',
            genre='Fantasy',
            tone='Heroic',
            word_count=100
        )

        # Verify result
        self.assertIsInstance(story_text, str)
        self.assertEqual(model_used, 'test-model')
        self.assertIn('brave knight', story_text)

        # Verify requests was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['json']['model'], 'test-model')
        self.assertIn('Fantasy', call_args[1]['json']['prompt'])
        self.assertIn('Heroic', call_args[1]['json']['prompt'])

    @patch('story_generator.requests.post')
    def test_generate_story_with_custom_prompt(self, mock_post):
        """Test story generation with custom prompt."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'Custom story content'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        custom_prompt = "Write a story about a magical forest."
        story_text, model_used = StoryGenerator.generate_story(
            model='test-model',
            custom_prompt=custom_prompt
        )

        self.assertIsInstance(story_text, str)
        self.assertIn('Custom story content', story_text)
        mock_post.assert_called_once()

    @patch('story_generator.requests.post')
    def test_generate_story_error_handling(self, mock_post):
        """Test error handling in story generation."""
        mock_post.side_effect = Exception("Connection Error")

        with self.assertRaises(Exception):
            StoryGenerator.generate_story(model='test-model')

    @patch('story_generator.requests.post')
    def test_generate_story_varied(self, mock_post):
        """Test varied story generation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'Varied story'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        story_text, model_used = StoryGenerator.generate_story_varied(
            model='test-model',
            genre='Mystery'
        )

        self.assertIsInstance(story_text, str)
        mock_post.assert_called()

    @patch('story_generator.requests.post')
    def test_generate_story_variants(self, mock_post):
        """Test story variants generation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'response': 'Variant story'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        results = StoryGenerator.generate_story_variants(
            model='test-model',
            variants=2
        )

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        # Should be called twice (once per variant)
        self.assertEqual(mock_post.call_count, 2)

    @patch('story_generator.requests.post')
    def test_generate_story_streaming(self, mock_post):
        """Test streaming story generation."""
        # Mock streaming response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_lines.return_value = [
            b'{"response": "Hello"}',
            b'{"response": " world"}',
            b'{"response": "!"}'
        ]
        mock_post.return_value = mock_response

        chunks = list(StoryGenerator.generate_story_streaming(
            model='test-model',
            genre='Sci-Fi'
        ))

        self.assertIsInstance(chunks, list)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(''.join(chunks), 'Hello world!')
        mock_post.assert_called_once()

    @patch('story_generator.requests.get')
    def test_check_ollama_running(self, mock_get):
        """Test checking if Ollama is running."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = StoryGenerator.check_ollama_running()
        self.assertTrue(result)
        mock_get.assert_called_once()

    @patch('story_generator.requests.get')
    def test_check_ollama_status(self, mock_get):
        """Test checking Ollama status."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'models': ['model1', 'model2']}
        mock_get.return_value = mock_response

        result = StoryGenerator.check_ollama_status()
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)
        mock_get.assert_called_once()

    def test_story_metrics_calculation(self):
        """Test story metrics calculation."""
        text = "This is a simple test story with some words."
        metrics = StoryMetrics.calculate_metrics(text)

        self.assertIsInstance(metrics, dict)
        self.assertIn('word_count', metrics)
        self.assertIn('sentence_count', metrics)
        self.assertIn('readability_score', metrics)
        self.assertIn('word_variety', metrics)
        self.assertIn('complex_word_ratio', metrics)
        self.assertIn('dialogue_ratio', metrics)
        self.assertIn('sentence_variety', metrics)

        # Verify word count
        self.assertEqual(metrics['word_count'], 9)

    def test_readability_score(self):
        """Test readability score calculation."""
        # Simple text should have a good readability score
        simple_text = "The cat sat on the mat. The dog ran in the park."
        metrics = StoryMetrics.calculate_metrics(simple_text)
        self.assertIsInstance(metrics['readability_score'], (int, float))
        self.assertGreaterEqual(metrics['readability_score'], 0)
        self.assertLessEqual(metrics['readability_score'], 10)

        # Empty text should return 0
        empty_metrics = StoryMetrics.calculate_metrics("")
        self.assertEqual(empty_metrics['readability_score'], 0)

    def test_word_variety_calculation(self):
        """Test word variety metric."""
        # Text with all unique words
        unique_text = "The quick brown fox jumps over a lazy dog."
        metrics = StoryMetrics.calculate_metrics(unique_text)
        self.assertGreater(metrics['word_variety'], 80)  # High variety

        # Text with repeated words
        repeated_text = "the the the the the the the the the the"
        metrics2 = StoryMetrics.calculate_metrics(repeated_text)
        self.assertLess(metrics2['word_variety'], 20)  # Low variety

    def test_default_parameters(self):
        """Test that default parameters are set correctly."""
        # Test that DEFAULT_WORD_COUNT is reasonable
        self.assertGreater(DEFAULT_WORD_COUNT, 0)
        self.assertLessEqual(DEFAULT_WORD_COUNT, 2000)  # Reasonable upper bound


if __name__ == '__main__':
    unittest.main()