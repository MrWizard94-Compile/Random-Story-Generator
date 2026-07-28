#!/usr/bin/env python3
"""
Unit tests for export functionality.
"""
import unittest
import os
import tempfile
from story_generator import StoriesManager


class TestExportFunctionality(unittest.TestCase):
    """Test export functions (PDF, DOCX, TXT)."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.manager = StoriesManager()
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.manager.STORIES_DIR = self.test_dir

        # Create a test story file
        self.test_story_content = """# Test Story

This is a test story for export functionality.

**Generated:** 2024-01-01 12:00:00
**Model:** test-model
**Genre:** Test
**Tone:** Neutral

The quick brown fox jumps over the lazy dog. This is a test sentence with multiple words and punctuation! How does this export?

Another paragraph here with some dialogue. "Hello world!" said the fox.

The end.
"""
        self.test_filename = "test_story.md"
        self.test_filepath = os.path.join(self.test_dir, self.test_filename)
        with open(self.test_filepath, 'w', encoding='utf-8') as f:
            f.write(self.test_story_content)

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        # Remove test files
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pdf_export(self):
        """Test PDF export functionality."""
        try:
            pdf_path = self.manager.export_to_pdf(self.test_filename)
            self.assertTrue(os.path.exists(pdf_path))
            self.assertTrue(pdf_path.endswith('.pdf'))
            self.assertGreater(os.path.getsize(pdf_path), 0)
        except Exception as e:
            self.fail(f"PDF export failed: {e}")

    def test_docx_export(self):
        """Test DOCX export functionality."""
        try:
            docx_path = self.manager.export_to_docx(self.test_filename)
            self.assertTrue(os.path.exists(docx_path))
            self.assertTrue(docx_path.endswith('.docx'))
            self.assertGreater(os.path.getsize(docx_path), 0)
        except Exception as e:
            self.fail(f"DOCX export failed: {e}")

    def test_txt_export(self):
        """Test TXT export functionality."""
        try:
            txt_path = self.manager.export_to_txt(self.test_filename)
            self.assertTrue(os.path.exists(txt_path))
            self.assertTrue(txt_path.endswith('.txt'))
            self.assertGreater(os.path.getsize(txt_path), 0)

            # Verify content
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("Test Story", content)
                self.assertIn("quick brown fox", content)
        except Exception as e:
            self.fail(f"TXT export failed: {e}")

    def test_export_nonexistent_file(self):
        """Test export with nonexistent file."""
        with self.assertRaises(Exception):
            self.manager.export_to_pdf("nonexistent.md")

    def test_export_with_custom_path(self):
        """Test export with custom output path."""
        custom_dir = tempfile.mkdtemp()
        try:
            custom_path = os.path.join(custom_dir, "custom_export.pdf")
            pdf_path = self.manager.export_to_pdf(self.test_filename, custom_path)
            self.assertEqual(pdf_path, custom_path)
            self.assertTrue(os.path.exists(custom_path))
        finally:
            import shutil
            shutil.rmtree(custom_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
