#!/usr/bin/env python3
"""
Additional tests to improve code coverage.
"""
import unittest
import tempfile
import os
import json
from datetime import datetime
from story_generator import StoryGenerator, StoriesManager, StoryMetrics, ContentQueueManager, PresetsManager, DEFAULT_MAX_CHARS
from banned_content import PROMPT_NAME_BAN


class TestAdditionalCoverage(unittest.TestCase):
    """Additional tests to improve code coverage."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.stories_dir = os.path.join(self.test_dir, "stories")
        self.ratings_file = os.path.join(self.test_dir, "ratings.json")

        self.stories_manager = StoriesManager(
            ratings_file=self.ratings_file,
            stories_dir=self.stories_dir
        )

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_generation_statistics_empty(self):
        """Test get_generation_statistics with no stories."""
        stats = self.stories_manager.get_generation_statistics()
        expected = {
            'total_stories': 0,
            'total_words': 0,
            'average_words': 0,
            'models': {},
            'genres': {},
            'tones': {},
            'generation_timeline': {},
            'earliest_date': None,
            'latest_date': None
        }
        self.assertEqual(stats['total_stories'], 0)
        self.assertEqual(stats['total_words'], 0)
        self.assertEqual(stats['average_words'], 0)
        self.assertEqual(stats['models'], {})
        self.assertEqual(stats['genres'], {})
        self.assertEqual(stats['tones'], {})
        self.assertEqual(stats['generation_timeline'], {})
        self.assertIsNone(stats['earliest_date'])
        self.assertIsNone(stats['latest_date'])

    def test_get_generation_statistics_with_data(self):
        """Test get_generation_statistics with actual story data."""
        # Create some test stories with different metadata
        stories_data = [
            ("story1.md", "Fantasy", "Epic", "model1", 500),
            ("story2.md", "Mystery", "Dark", "model2", 300),
            ("story3.md", "Sci-Fi", "Hopeful", "model1", 400),
            ("story4.md", None, "Light", "model2", 200),
        ]

        for filename, genre, tone, model, word_count in stories_data:
            # Create a story with the specified word count (excluding title)
            story_text = f"Title: Test Story\n\n{' '.join(['word'] * word_count)}"
            self.stories_manager.save_story(story_text, model, genre=genre, tone=tone, filename=filename)

        # Add some ratings
        self.stories_manager.set_rating("story1.md", 5)
        self.stories_manager.set_rating("story2.md", 4)
        self.stories_manager.set_favorite("story1.md", True)

        stats = self.stories_manager.get_generation_statistics()

        # Verify basic counts
        self.assertEqual(stats['total_stories'], 4)
        # Total words will be higher due to titles and metadata
        self.assertGreater(stats['total_words'], 1400)  # At least the content words
        self.assertGreater(stats['average_words'], 350.0)

        # Verify model counts
        self.assertEqual(stats['models']['model1'], 2)
        self.assertEqual(stats['models']['model2'], 2)

        # Verify genre counts
        self.assertEqual(stats['genres']['Fantasy'], 1)
        self.assertEqual(stats['genres']['Mystery'], 1)
        self.assertEqual(stats['genres']['Sci-Fi'], 1)

        # Verify tone counts
        self.assertEqual(stats['tones']['Epic'], 1)
        self.assertEqual(stats['tones']['Dark'], 1)
        self.assertEqual(stats['tones']['Hopeful'], 1)
        self.assertEqual(stats['tones']['Light'], 1)

        # Verify timeline exists
        self.assertIsInstance(stats['generation_timeline'], dict)
        self.assertGreater(len(stats['generation_timeline']), 0)

        # Verify dates
        self.assertIsInstance(stats['earliest_date'], datetime)
        self.assertIsInstance(stats['latest_date'], datetime)

    def test_format_story_as_thread(self):
        """Test format_story_as_thread method."""
        # Test empty input
        self.assertEqual(ContentQueueManager.format_story_as_thread(""), [])
        self.assertEqual(ContentQueueManager.format_story_as_thread("   "), [])

        # Test normal story
        story = "This is a test story with some words that should be formatted into a thread."
        thread = ContentQueueManager.format_story_as_thread(story, max_chars=50)
        self.assertIsInstance(thread, list)
        self.assertGreater(len(thread), 0)

        # Verify segments are reasonable length
        for segment in thread:
            self.assertLessEqual(len(segment), 50)

    def test_template_methods(self):
        """Test template-related methods."""
        # Test _get_template_text
        self.assertEqual(StoryGenerator._get_template_text(None), "")
        self.assertEqual(StoryGenerator._get_template_text(""), "")
        self.assertEqual(StoryGenerator._get_template_text("None"), "")

        # Test valid templates
        hero_journey = StoryGenerator._get_template_text("hero's journey")
        self.assertIn("Hero's Journey", hero_journey)
        self.assertIn("Ordinary world", hero_journey)

        three_act = StoryGenerator._get_template_text("three-act structure")
        self.assertIn("three acts", three_act)

        five_act = StoryGenerator._get_template_text("five-act structure")
        self.assertIn("five acts", five_act)

        character_arc = StoryGenerator._get_template_text("character arc")
        self.assertIn("character arc", character_arc)

        mystery = StoryGenerator._get_template_text("mystery detective")
        self.assertIn("mystery", mystery)

        # Test invalid template
        self.assertEqual(StoryGenerator._get_template_text("invalid"), "")

    def test_build_prompt(self):
        """Test _build_prompt method."""
        # Test custom prompt
        custom = "Custom prompt text"
        prompt = StoryGenerator._build_prompt(custom_prompt=custom)
        self.assertIn(custom, prompt)
        self.assertIn(PROMPT_NAME_BAN, prompt)

        # Test basic prompt
        prompt = StoryGenerator._build_prompt()
        self.assertIn("original, engaging short story", prompt)
        self.assertIn("500 words", prompt)

        # Test with genre and tone
        prompt = StoryGenerator._build_prompt(genre="Fantasy", tone="Dark", word_count=300)
        self.assertIn("Fantasy genre", prompt)
        self.assertIn("Dark tone", prompt)
        self.assertIn("300 words", prompt)

        # Test with template
        prompt = StoryGenerator._build_prompt(template="hero's journey")
        self.assertIn("Hero's Journey", prompt)

    def test_variation_instruction(self):
        """Test _get_variation_instruction method."""
        # Test different indices
        for i in range(5):
            instruction = StoryGenerator._get_variation_instruction(i)
            self.assertIsInstance(instruction, str)
            self.assertGreater(len(instruction), 0)

        # Test out of bounds (should cycle)
        instruction = StoryGenerator._get_variation_instruction(10)
        self.assertIsInstance(instruction, str)

    def test_generate_story_variants(self):
        """Test generate_story_variants method."""
        # Mock the requests to avoid actual API calls
        import unittest.mock as mock

        with mock.patch('story_generator.requests.post') as mock_post:
            mock_response = mock.MagicMock()
            mock_response.json.return_value = {'response': 'Test story variant'}
            mock_post.return_value = mock_response

            variants = StoryGenerator.generate_story_variants("test-model", variants=2)
            self.assertEqual(len(variants), 2)
            for story, model in variants:
                self.assertEqual(story, 'Test story variant')
                self.assertEqual(model, 'test-model')

    def test_format_story_for_platform(self):
        """Test format_story_for_platform method."""
        # Test empty input
        self.assertEqual(StoryGenerator.format_story_for_platform(""), "")

        # Test Twitter/X format
        story = "This is a short story that should be formatted for Twitter."
        formatted = StoryGenerator.format_story_for_platform(story, "twitter")
        self.assertIn("#ShortStory", formatted)
        self.assertIn("#Fiction", formatted)
        self.assertLessEqual(len(formatted), 280)

        # Test Facebook format
        formatted = StoryGenerator.format_story_for_platform(story, "facebook")
        self.assertIn("Read more", formatted)

        # Test Threads format (same as Twitter)
        formatted = StoryGenerator.format_story_for_platform(story, "threads")
        self.assertIn("#ShortStory", formatted)

        # Test unknown platform
        formatted = StoryGenerator.format_story_for_platform(story, "unknown")
        self.assertEqual(formatted, story)

    def test_story_metrics_edge_cases(self):
        """Test StoryMetrics edge cases."""
        # Test with empty text
        metrics = StoryMetrics.calculate_metrics("")
        self.assertEqual(metrics['word_count'], 0)
        self.assertEqual(metrics['sentence_count'], 0)
        self.assertEqual(metrics['readability_score'], 0)

        # Test with very short text
        metrics = StoryMetrics.calculate_metrics("Hi")
        self.assertEqual(metrics['word_count'], 1)

        # Test with numbers and punctuation
        text = "The quick brown fox jumped over the lazy dog."
        metrics = StoryMetrics.calculate_metrics(text)
        self.assertEqual(metrics['word_count'], 9)

    def test_export_error_handling(self):
        """Test export methods error handling."""
        # Test PDF export with invalid file
        with self.assertRaises(Exception):
            self.stories_manager.export_to_pdf("nonexistent.md")

        # Test DOCX export with invalid file
        with self.assertRaises(Exception):
            self.stories_manager.export_to_docx("nonexistent.md")

        # Test TXT export with invalid file
        with self.assertRaises(Exception):
            self.stories_manager.export_to_txt("nonexistent.md")

    def test_filter_stories_edge_cases(self):
        """Test filter_stories with various edge cases."""
        # Create test stories
        self.stories_manager.save_story("Test story 1", "model1", genre="Fantasy")
        self.stories_manager.save_story("Test story 2", "model2", genre="Sci-Fi")

        # Test filtering by non-existent genre
        results = self.stories_manager.filter_stories(genre="NonExistent")
        self.assertEqual(len(results), 0)

        # Test filtering by non-existent model
        results = self.stories_manager.filter_stories(model="nonexistent")
        self.assertEqual(len(results), 0)

        # Test filtering with None values
        results = self.stories_manager.filter_stories(genre=None, model=None)
        # Should return all stories
        all_stories = self.stories_manager.get_all_stories_metadata()
        self.assertEqual(len(results), len(all_stories))

        # Test date filtering (no dates should match future dates)
        future_date = datetime(2030, 1, 1)
        results = self.stories_manager.filter_stories(date_to=future_date)
        # Should include all stories since they're all from the past
        self.assertGreaterEqual(len(results), 1)

    def test_rating_stats_calculation(self):
        """Test rating statistics calculation."""
        # Create stories and add ratings
        self.stories_manager.save_story("Story 1", "model1", filename="story1.md")
        self.stories_manager.save_story("Story 2", "model1", filename="story2.md")
        self.stories_manager.save_story("Story 3", "model2", filename="story3.md")

        # Add ratings
        self.stories_manager.set_rating("story1.md", 5)
        self.stories_manager.set_rating("story2.md", 4)
        self.stories_manager.set_rating("story3.md", 3)

        # Add favorites
        self.stories_manager.set_favorite("story1.md", True)
        self.stories_manager.set_favorite("story2.md", True)

        stats = self.stories_manager.get_rating_stats()

        # Verify rating distribution (only includes rated stories 1-5)
        self.assertEqual(stats['distribution'][5], 1)
        self.assertEqual(stats['distribution'][4], 1)
        self.assertEqual(stats['distribution'][3], 1)

        # Verify averages
        self.assertAlmostEqual(stats['average'], 4.0)  # (5+4+3)/3
        self.assertEqual(stats['total_rated'], 3)
        self.assertEqual(stats['favorites'], 2)

    def test_get_available_models_success(self):
        """Test get_available_models with successful API response."""
        import unittest.mock as mock

        mock_response = mock.Mock()
        mock_response.json.return_value = {"models": [{"name": "llama2"}, {"name": "codellama"}]}

        with mock.patch('requests.get') as mock_get:
            mock_get.return_value = mock_response
            models = StoryGenerator.get_available_models()
            self.assertEqual(models, ["llama2", "codellama"])
            mock_get.assert_called_once_with(StoryGenerator.MODELS_API_URL, timeout=10)

    def test_get_available_models_request_exception(self):
        """Test get_available_models with request exception."""
        import unittest.mock as mock
        import requests

        with mock.patch('requests.get', side_effect=requests.exceptions.RequestException("Network error")):
            with self.assertRaises(Exception) as context:
                StoryGenerator.get_available_models()
            self.assertIn("Failed to fetch models", str(context.exception))

    def test_get_template_text_none(self):
        """Test _get_template_text with None input."""
        result = StoryGenerator._get_template_text(None)
        self.assertEqual(result, "")

    def test_get_template_text_empty(self):
        """Test _get_template_text with empty string."""
        result = StoryGenerator._get_template_text("")
        self.assertEqual(result, "")

    def test_get_template_text_none_string(self):
        """Test _get_template_text with 'None' string."""
        result = StoryGenerator._get_template_text("None")
        self.assertEqual(result, "")

    def test_get_template_text_heros_journey(self):
        """Test _get_template_text with hero's journey template."""
        result = StoryGenerator._get_template_text("hero's journey")
        self.assertIn("Hero's Journey", result)
        self.assertIn("Ordinary world", result)

    def test_get_template_text_three_act(self):
        """Test _get_template_text with three-act structure."""
        result = StoryGenerator._get_template_text("three-act structure")
        self.assertIn("three acts", result)
        self.assertIn("Setup, Confrontation, Resolution", result)

    def test_get_template_text_five_act(self):
        """Test _get_template_text with five-act structure."""
        result = StoryGenerator._get_template_text("five-act structure")
        self.assertIn("five acts", result)
        self.assertIn("Exposition, Rising Action", result)

    def test_get_template_text_character_arc(self):
        """Test _get_template_text with character arc."""
        result = StoryGenerator._get_template_text("character arc")
        self.assertIn("character arc", result)
        self.assertIn("beginning flaw", result)

    def test_get_template_text_mystery_detective(self):
        """Test _get_template_text with mystery detective."""
        result = StoryGenerator._get_template_text("mystery detective")
        self.assertIn("mystery/detective", result)
        self.assertIn("crime discovery", result)

    def test_get_template_text_unknown(self):
        """Test _get_template_text with unknown template."""
        result = StoryGenerator._get_template_text("unknown template")
        self.assertEqual(result, "")

    def test_build_prompt_custom(self):
        """Test _build_prompt with custom prompt."""
        result = StoryGenerator._build_prompt(custom_prompt="Custom story prompt")
        self.assertIn("Custom story prompt", result)
        self.assertIn(PROMPT_NAME_BAN, result)

    def test_build_prompt_basic(self):
        """Test _build_prompt with basic parameters."""
        result = StoryGenerator._build_prompt(genre="fantasy", tone="dark", word_count=1000)
        self.assertIn("fantasy genre", result)
        self.assertIn("dark tone", result)
        self.assertIn("1000 words", result)
        self.assertIn("engaging short story", result)

    def test_build_prompt_with_template(self):
        """Test _build_prompt with template."""
        result = StoryGenerator._build_prompt(genre="mystery", template="hero's journey")
        self.assertIn("mystery genre", result)
        self.assertIn("Hero's Journey", result)

    def test_get_variation_instruction(self):
        """Test _get_variation_instruction with different indices."""
        variations = [
            "Add an unexpected twist ending and strong emotional arc.",
            "Use vivid sensory details and keep the pacing brisk.",
            "Write from the perspective of an unreliable narrator.",
            "Focus on a humoristic tone with sharp dialogue.",
            "Make it a philosophical parable with symbolic motifs."
        ]

        for i in range(len(variations)):
            result = StoryGenerator._get_variation_instruction(i)
            self.assertEqual(result, variations[i])

        # Test wraparound
        result = StoryGenerator._get_variation_instruction(5)
        self.assertEqual(result, variations[0])

    def test_generate_story_varied_success(self):
        """Test generate_story_varied with successful response."""
        import unittest.mock as mock

        mock_response = mock.Mock()
        mock_response.json.return_value = {"response": "Test story content"}

        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = mock_response
            story, model_used = StoryGenerator.generate_story_varied("llama2", variant=1)
            self.assertEqual(story, "Test story content")
            self.assertEqual(model_used, "llama2")
            # Verify the prompt includes variation
            call_args = mock_post.call_args
            prompt = call_args[1]['json']['prompt']
            self.assertIn("Use vivid sensory details", prompt)

    def test_generate_story_varied_request_exception(self):
        """Test generate_story_varied with request exception."""
        import unittest.mock as mock
        import requests

        with mock.patch('requests.post', side_effect=requests.exceptions.RequestException("API error")):
            with self.assertRaises(Exception) as context:
                StoryGenerator.generate_story_varied("llama2")
            self.assertIn("Error generating varied story", str(context.exception))

    def test_generate_story_variants(self):
        """Test generate_story_variants generates multiple variants."""
        import unittest.mock as mock

        mock_response = mock.Mock()
        mock_response.json.return_value = {"response": "Variant story"}

        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = mock_response
            variants = StoryGenerator.generate_story_variants("llama2", variants=2)
            self.assertEqual(len(variants), 2)
            for story, model in variants:
                self.assertEqual(story, "Variant story")
                self.assertEqual(model, "llama2")

    def test_format_story_for_platform_x(self):
        """Test format_story_for_platform for X/Twitter."""
        story = "This is a very long story that should definitely be truncated for social media posting because it exceeds the character limit for Twitter and similar platforms. " * 10  # Make it much longer
        result = StoryGenerator.format_story_for_platform(story, "x")
        self.assertIn("#ShortStory", result)
        self.assertIn("#Fiction", result)
        self.assertIn("...", result)  # Should be truncated
        self.assertLess(len(result), 320)  # Allow some margin for CTA text

    def test_format_story_for_platform_facebook(self):
        """Test format_story_for_platform for Facebook."""
        story = "This is a very long story for Facebook with more content allowed that should be truncated. " * 15  # Make it long
        result = StoryGenerator.format_story_for_platform(story, "facebook")
        self.assertIn("Read more in the app", result)
        self.assertIn("...", result)  # Should be truncated

    def test_format_story_for_platform_instagram(self):
        """Test format_story_for_platform for Instagram."""
        story = "This is a very long Instagram story content that should be truncated. " * 10  # Make it long
        result = StoryGenerator.format_story_for_platform(story, "instagram")
        self.assertIn("#fiction", result)
        self.assertIn("#story", result)
        self.assertIn("...", result)  # Should be truncated

    def test_format_story_for_platform_default(self):
        """Test format_story_for_platform with unknown platform."""
        story = "This is a very long default platform formatting test that should be truncated. " * 8  # Make it long
        result = StoryGenerator.format_story_for_platform(story, "unknown")
        self.assertIn("...", result)  # Should be truncated
        self.assertEqual(len(result), DEFAULT_MAX_CHARS + 3)  # 280 + "..."

    def test_format_story_for_platform_empty(self):
        """Test format_story_for_platform with empty story."""
        result = StoryGenerator.format_story_for_platform("", "x")
        self.assertEqual(result, "")

    def test_generate_story_streaming_success(self):
        """Test generate_story_streaming with successful response."""
        import unittest.mock as mock

        mock_response = mock.Mock()
        mock_response.iter_lines.return_value = [
            b'{"response": "Hello"}',
            b'{"response": " world"}',
            b'{"response": "!"}'
        ]

        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = mock_response
            chunks = list(StoryGenerator.generate_story_streaming("llama2"))
            self.assertEqual(chunks, ["Hello", " world", "!"])

    def test_generate_story_streaming_request_exception(self):
        """Test generate_story_streaming with request exception."""
        import unittest.mock as mock
        import requests

        with mock.patch('requests.post', side_effect=requests.exceptions.RequestException("Stream error")):
            with self.assertRaises(Exception) as context:
                list(StoryGenerator.generate_story_streaming("llama2"))
            self.assertIn("Error generating story", str(context.exception))

    def test_generate_story_success(self):
        """Test generate_story with successful response."""
        import unittest.mock as mock

        mock_response = mock.Mock()
        mock_response.json.return_value = {"response": "Generated story content"}

        with mock.patch('requests.post') as mock_post:
            mock_post.return_value = mock_response
            story, model_used = StoryGenerator.generate_story("llama2")
            self.assertEqual(story, "Generated story content")
            self.assertEqual(model_used, "llama2")

    def test_check_ollama_running_exception(self):
        """Test check_ollama_running with exception."""
        import unittest.mock as mock

        with mock.patch('requests.get', side_effect=Exception("Connection failed")):
            result = StoryGenerator.check_ollama_running()
            self.assertFalse(result)

    def test_check_ollama_status_connection_error(self):
        """Test check_ollama_status with connection error."""
        import unittest.mock as mock
        import requests

        with mock.patch('requests.get', side_effect=requests.exceptions.ConnectionError("Cannot connect")):
            result = StoryGenerator.check_ollama_status()
            self.assertEqual(result["status"], "not_running")
            self.assertIn("Cannot connect to Ollama", result["message"])

    def test_check_ollama_status_timeout(self):
        """Test check_ollama_status with timeout."""
        import unittest.mock as mock
        import requests

        with mock.patch('requests.get', side_effect=requests.exceptions.Timeout("Timeout")):
            result = StoryGenerator.check_ollama_status()
            self.assertEqual(result["status"], "timeout")
            self.assertIn("Ollama response timeout", result["message"])

    def test_check_ollama_status_general_exception(self):
        """Test check_ollama_status with general exception."""
        import unittest.mock as mock

        with mock.patch('requests.get', side_effect=Exception("General error")):
            result = StoryGenerator.check_ollama_status()
            self.assertEqual(result["status"], "error")
            self.assertEqual(result["message"], "General error")

    def test_check_ollama_status_invalid_json(self):
        """Test check_ollama_status with invalid JSON response."""
        import unittest.mock as mock

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        with mock.patch('requests.get', return_value=mock_response):
            result = StoryGenerator.check_ollama_status()
            self.assertEqual(result["status"], "error")
            self.assertIn("Invalid JSON response", result["message"])

    def test_check_ollama_status_invalid_response_format(self):
        """Test check_ollama_status with invalid response format."""
        import unittest.mock as mock

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = "not a dict"

        with mock.patch('requests.get', return_value=mock_response):
            result = StoryGenerator.check_ollama_status()
            self.assertEqual(result["status"], "error")
            self.assertIn("Invalid API response format", result["message"])

    def test_check_ollama_status_invalid_models_data(self):
        """Test check_ollama_status with invalid models data."""
        import unittest.mock as mock

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": "not a list"}

        with mock.patch('requests.get', return_value=mock_response):
            result = StoryGenerator.check_ollama_status()
            self.assertEqual(result["status"], "error")
            self.assertIn("Invalid models data", result["message"])

    def test_check_ollama_status_http_error(self):
        """Test check_ollama_status with HTTP error."""
        import unittest.mock as mock

        mock_response = mock.Mock()
        mock_response.status_code = 500

        with mock.patch('requests.get', return_value=mock_response):
            result = StoryGenerator.check_ollama_status()
            self.assertEqual(result["status"], "error")
            self.assertIn("HTTP 500", result["message"])

    def test_content_queue_manager_init(self):
        """Test ContentQueueManager initialization."""
        queue_manager = ContentQueueManager(queue_dir=self.test_dir)
        self.assertIsNotNone(queue_manager.queue_path)

    def test_add_to_queue(self):
        """Test adding an item to the queue."""
        queue_manager = ContentQueueManager(queue_dir=self.test_dir)

        item = {"filename": "test_story.md", "status": "scheduled",
                "scheduled_time": datetime(2026, 3, 25, 10, 0, 0).isoformat()}
        result = queue_manager.add_to_queue(item)
        self.assertTrue(result)

        # Item should have been assigned an id
        self.assertIn("id", item)

        # Verify it was saved
        queue = queue_manager.get_queue()
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["filename"], "test_story.md")

    def test_get_queue_empty(self):
        """Test getting queue when empty."""
        queue_manager = ContentQueueManager(queue_dir=self.test_dir)
        queue = queue_manager.get_queue()
        self.assertEqual(queue, [])

    def test_get_queue_with_items(self):
        """Test getting queue with items."""
        queue_manager = ContentQueueManager(queue_dir=self.test_dir)

        queue_manager.add_to_queue({"filename": "story1.md", "status": "scheduled"})
        queue_manager.add_to_queue({"filename": "story2.md", "status": "scheduled"})

        queue = queue_manager.get_queue()
        self.assertEqual(len(queue), 2)

    def test_remove_from_queue(self):
        """Test removing item from queue."""
        queue_manager = ContentQueueManager(queue_dir=self.test_dir)

        item = {"id": "test_item_1", "filename": "test_story.md", "status": "scheduled"}
        queue_manager.add_to_queue(item)

        # Verify it exists
        queue = queue_manager.get_queue()
        self.assertEqual(len(queue), 1)

        # Remove it
        result = queue_manager.remove_from_queue("test_item_1")
        self.assertTrue(result)

        # Verify it's gone
        queue = queue_manager.get_queue()
        self.assertEqual(len(queue), 0)

        # Try to remove non-existent item
        result = queue_manager.remove_from_queue("nonexistent")
        self.assertFalse(result)

    def test_update_status_via_update(self):
        """Test updating item status via update_queue_item."""
        queue_manager = ContentQueueManager(queue_dir=self.test_dir)

        item = {"id": "test_item_1", "filename": "test_story.md", "status": "scheduled"}
        queue_manager.add_to_queue(item)

        # Update status
        result = queue_manager.update_queue_item("test_item_1", {"status": "posted"})
        self.assertTrue(result)

        # Verify status changed
        queue = queue_manager.get_queue()
        self.assertEqual(queue[0]["status"], "posted")

        # Try to update non-existent item
        result = queue_manager.update_queue_item("nonexistent", {"status": "posted"})
        self.assertFalse(result)

    def test_update_queue_item(self):
        """Test updating queue item."""
        queue_manager = ContentQueueManager(queue_dir=self.test_dir)

        item = {"id": "test_item_1", "filename": "test_story.md", "status": "scheduled"}
        queue_manager.add_to_queue(item)

        # Update item
        updates = {"status": "cancelled", "filename": "updated_story.md"}
        result = queue_manager.update_queue_item("test_item_1", updates)
        self.assertTrue(result)

        # Verify updates
        queue = queue_manager.get_queue()
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["status"], "cancelled")
        self.assertEqual(queue[0]["filename"], "updated_story.md")
        self.assertEqual(queue[0]["id"], "test_item_1")  # ID should be preserved

        # Try to update non-existent item
        result = queue_manager.update_queue_item("nonexistent", updates)
        self.assertFalse(result)

    def test_execute_queue_item(self):
        """Test executing queue item."""
        queue_manager = ContentQueueManager(queue_dir=self.test_dir)

        item = {"id": "test_item_1", "filename": "test_story.md", "status": "scheduled"}
        queue_manager.add_to_queue(item)

        # Execute item
        result = queue_manager.execute_queue_item("test_item_1", self.stories_manager)
        self.assertTrue(result)

        # Verify status changed
        queue = queue_manager.get_queue()
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["status"], "executed")
        self.assertIn("executed_at", queue[0])

    def test_get_performance_stats_empty(self):
        """Test getting performance stats when no posted items."""
        queue_manager = ContentQueueManager(queue_dir=self.test_dir)
        stats = queue_manager.get_performance_stats()
        expected = {
            'total_posts': 0,
            'total_views': 0,
            'total_likes': 0,
            'total_shares': 0,
            'total_comments': 0,
            'avg_engagement': 0
        }
        self.assertEqual(stats, expected)

    def test_get_performance_stats_with_data(self):
        """Test getting performance stats with items in queue."""
        queue_manager = ContentQueueManager(queue_dir=self.test_dir)

        queue_manager.add_to_queue({"id": "item1", "filename": "story1.md", "status": "scheduled"})
        queue_manager.add_to_queue({"id": "item2", "filename": "story2.md", "status": "scheduled"})

        queue_manager.execute_queue_item("item1", self.stories_manager)
        queue_manager.execute_queue_item("item2", self.stories_manager)

        stats = queue_manager.get_performance_stats()
        self.assertEqual(stats['total_posts'], 2)
        self.assertGreaterEqual(stats['total_views'], 0)
        self.assertGreaterEqual(stats['total_likes'], 0)

    def test_format_story_as_thread_empty(self):
        """Test format_story_as_thread with empty input."""
        result = ContentQueueManager.format_story_as_thread("")
        self.assertEqual(result, [])

    def test_format_story_as_thread_normal(self):
        """Test format_story_as_thread with normal story."""
        story = "This is a short story that should fit in one thread segment."
        result = ContentQueueManager.format_story_as_thread(story, max_chars=50)
        self.assertGreater(len(result), 0)
        # Segments should not exceed max_chars
        for segment in result:
            self.assertLessEqual(len(segment), 50)

    def test_format_story_as_thread_long_word(self):
        """Test format_story_as_thread with word longer than max_chars."""
        long_word = "supercalifragilisticexpialidocious" * 3  # Very long word
        result = ContentQueueManager.format_story_as_thread(long_word, max_chars=200)
        self.assertGreater(len(result), 0)

    def test_format_story_as_thread_multiple_segments(self):
        """Test format_story_as_thread creating multiple segments."""
        # Use paragraph breaks so the splitter has natural break points
        story = "\n\n".join([f"This is paragraph {i} of a longer story that should be split into multiple thread segments." for i in range(10)])
        result = ContentQueueManager.format_story_as_thread(story, max_chars=200)
        self.assertGreater(len(result), 1)
        # Verify all segments fit within max_chars
        for segment in result:
            self.assertLessEqual(len(segment), 200)

    def test_presets_manager_init(self):
        """Test PresetsManager initialization."""
        presets_manager = PresetsManager(presets_dir=self.test_dir)
        self.assertIsNotNone(presets_manager.presets_path)

    def test_save_preset_new(self):
        """Test saving a new preset."""
        presets_manager = PresetsManager(presets_dir=self.test_dir)

        result = presets_manager.save_preset(
            name="Test Preset",
            genre="Fantasy",
            tone="Dark",
            word_count=1000,
            custom_prompt="Test prompt"
        )
        self.assertTrue(result)

        # Verify it was saved
        presets = presets_manager.get_presets()
        self.assertEqual(len(presets), 1)
        self.assertEqual(presets[0]["name"], "Test Preset")
        self.assertEqual(presets[0]["genre"], "Fantasy")

    def test_save_preset_duplicate(self):
        """Test saving a preset with duplicate name."""
        presets_manager = PresetsManager(presets_dir=self.test_dir)

        # Save first preset
        presets_manager.save_preset(name="Test Preset", genre="Fantasy")

        # Try to save duplicate with exact same name
        result = presets_manager.save_preset(name="Test Preset", genre="Sci-Fi")
        self.assertFalse(result)

        # Should still have only one preset
        presets = presets_manager.get_presets()
        self.assertEqual(len(presets), 1)
        self.assertEqual(presets[0]["genre"], "Fantasy")  # Original should remain

    def test_get_presets_empty(self):
        """Test getting presets when none exist."""
        presets_manager = PresetsManager(presets_dir=self.test_dir)
        presets = presets_manager.get_presets()
        self.assertEqual(presets, [])

    def test_get_preset_existing(self):
        """Test getting an existing preset."""
        presets_manager = PresetsManager(presets_dir=self.test_dir)

        presets_manager.save_preset(name="Test Preset", genre="Fantasy", tone="Dark")

        preset = presets_manager.get_preset("Test Preset")
        self.assertIsNotNone(preset)
        self.assertEqual(preset["name"], "Test Preset")
        self.assertEqual(preset["genre"], "Fantasy")

    def test_get_preset_nonexistent(self):
        """Test getting a non-existent preset."""
        presets_manager = PresetsManager(presets_dir=self.test_dir)

        preset = presets_manager.get_preset("Nonexistent")
        self.assertIsNone(preset)

    def test_delete_preset_existing(self):
        """Test deleting an existing preset."""
        presets_manager = PresetsManager(presets_dir=self.test_dir)

        presets_manager.save_preset(name="Test Preset", genre="Fantasy")

        result = presets_manager.delete_preset("Test Preset")
        self.assertTrue(result)

        # Should be empty now
        presets = presets_manager.get_presets()
        self.assertEqual(len(presets), 0)

    def test_delete_preset_nonexistent(self):
        """Test deleting a non-existent preset."""
        presets_manager = PresetsManager(presets_dir=self.test_dir)

        result = presets_manager.delete_preset("Nonexistent")
        self.assertFalse(result)

    def test_update_preset_existing(self):
        """Test updating an existing preset."""
        presets_manager = PresetsManager(presets_dir=self.test_dir)

        presets_manager.save_preset(name="Test Preset", genre="Fantasy", tone="Dark", word_count=500)

        result = presets_manager.update_preset(
            name="Test Preset",
            genre="Sci-Fi",
            tone="Light",
            word_count=1000
        )
        self.assertTrue(result)

        # Verify updates
        preset = presets_manager.get_preset("Test Preset")
        self.assertEqual(preset["genre"], "Sci-Fi")
        self.assertEqual(preset["tone"], "Light")
        self.assertEqual(preset["word_count"], 1000)

    def test_update_preset_nonexistent(self):
        """Test updating a non-existent preset."""
        presets_manager = PresetsManager(presets_dir=self.test_dir)

        result = presets_manager.update_preset(name="Nonexistent", genre="Fantasy")
        self.assertFalse(result)

    def test_update_preset_partial(self):
        """Test updating only some fields of a preset."""
        presets_manager = PresetsManager(presets_dir=self.test_dir)

        presets_manager.save_preset(name="Test Preset", genre="Fantasy", tone="Dark", word_count=500)

        # update_preset overwrites ALL fields (even with None defaults)
        result = presets_manager.update_preset(name="Test Preset", genre="Sci-Fi")
        self.assertTrue(result)

        # Genre was updated
        preset = presets_manager.get_preset("Test Preset")
        self.assertEqual(preset["genre"], "Sci-Fi")
        # Note: tone becomes None because update_preset overwrites all fields
        self.assertIsNone(preset["tone"])
        # word_count resets to default (500) since not explicitly passed
        self.assertEqual(preset["word_count"], 500)


if __name__ == '__main__':
    unittest.main()