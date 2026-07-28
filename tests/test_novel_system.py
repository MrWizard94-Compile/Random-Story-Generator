#!/usr/bin/env python3
"""
Unit tests for StoryBible and NovelManager — the long-form novel system.
"""
import unittest
import tempfile
import os
import json
import shutil
from story_generator import StoryBible, NovelManager


class TestStoryBible(unittest.TestCase):
    """Test StoryBible — the living document for novel consistency."""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.novel_dir = os.path.join(self.test_dir, "test_novel")
        os.makedirs(self.novel_dir, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_creates_empty_bible(self) -> None:
        """New bible should have correct defaults."""
        bible = StoryBible(self.novel_dir, "Test Novel")
        self.assertEqual(bible.title, "Test Novel")
        self.assertEqual(bible.data["title"], "Test Novel")
        self.assertEqual(bible.data["chapter_count"], 0)
        self.assertEqual(bible.data["characters"], {})
        self.assertEqual(bible.data["places"], {})
        self.assertEqual(bible.data["open_threads"], [])
        self.assertEqual(bible.data["closed_threads"], [])
        self.assertEqual(bible.data["timeline"], [])

    def test_save_creates_file(self) -> None:
        """save() should write bible.json to disk."""
        bible = StoryBible(self.novel_dir, "Test Novel")
        bible.save()
        path = os.path.join(self.novel_dir, "bible.json")
        self.assertTrue(os.path.exists(path))
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data["title"], "Test Novel")

    def test_load_persists_data(self) -> None:
        """Data should survive save/load cycle."""
        bible = StoryBible(self.novel_dir, "Persistent Novel")
        bible.add_character("Marcus", "A soldier", role="protagonist", arc="Redemption")
        bible.add_place("Iron Keep", "A fortress", significance="Home base")

        # Create new instance from same dir
        bible2 = StoryBible(self.novel_dir, "Persistent Novel")
        self.assertIn("Marcus", bible2.data["characters"])
        self.assertIn("Iron Keep", bible2.data["places"])
        self.assertEqual(bible2.data["characters"]["Marcus"]["role"], "protagonist")

    def test_get_and_set(self) -> None:
        """get() and set() should work as key-value accessors."""
        bible = StoryBible(self.novel_dir, "Test")
        bible.set("genre", "Fantasy")
        self.assertEqual(bible.get("genre"), "Fantasy")
        self.assertIsNone(bible.get("nonexistent"))
        self.assertEqual(bible.get("nonexistent", "default"), "default")

    def test_update(self) -> None:
        """update() should merge multiple fields at once."""
        bible = StoryBible(self.novel_dir, "Test")
        bible.update({"genre": "Sci-Fi", "tone": "Dark", "premise": "In the year 3000..."})
        self.assertEqual(bible.get("genre"), "Sci-Fi")
        self.assertEqual(bible.get("tone"), "Dark")
        self.assertIn("3000", bible.get("premise"))

    def test_add_character(self) -> None:
        """add_character should store character with all fields."""
        bible = StoryBible(self.novel_dir, "Test")
        bible.add_character("Sera", "A blacksmith", role="mentor", arc="Sacrifice")
        char = bible.data["characters"]["Sera"]
        self.assertEqual(char["description"], "A blacksmith")
        self.assertEqual(char["role"], "mentor")
        self.assertEqual(char["arc"], "Sacrifice")
        self.assertEqual(char["last_seen"], 0)

    def test_add_character_updates_last_seen(self) -> None:
        """last_seen should reflect current chapter_count."""
        bible = StoryBible(self.novel_dir, "Test")
        bible.set("chapter_count", 3)
        bible.add_character("Late Arrival", "Appears chapter 3")
        self.assertEqual(bible.data["characters"]["Late Arrival"]["last_seen"], 3)

    def test_add_place(self) -> None:
        """add_place should store place with description and significance."""
        bible = StoryBible(self.novel_dir, "Test")
        bible.add_place("The Docks", "A busy port", significance="Trade hub")
        place = bible.data["places"]["The Docks"]
        self.assertEqual(place["description"], "A busy port")
        self.assertEqual(place["significance"], "Trade hub")

    def test_add_timeline_event(self) -> None:
        """add_timeline_event should append to timeline."""
        bible = StoryBible(self.novel_dir, "Test")
        bible.add_timeline_event(1, "Marcus arrives at the keep")
        bible.add_timeline_event(2, "The siege begins")
        self.assertEqual(len(bible.data["timeline"]), 2)
        self.assertEqual(bible.data["timeline"][0]["chapter"], 1)
        self.assertEqual(bible.data["timeline"][1]["event"], "The siege begins")

    def test_open_and_close_thread(self) -> None:
        """Thread lifecycle: open -> close."""
        bible = StoryBible(self.novel_dir, "Test")
        bible.add_open_thread("Who stole the map?")
        self.assertIn("Who stole the map?", bible.data["open_threads"])
        self.assertNotIn("Who stole the map?", bible.data["closed_threads"])

        bible.close_thread("Who stole the map?")
        self.assertNotIn("Who stole the map?", bible.data["open_threads"])
        self.assertIn("Who stole the map?", bible.data["closed_threads"])

    def test_open_thread_no_duplicates(self) -> None:
        """Adding same thread twice should not duplicate."""
        bible = StoryBible(self.novel_dir, "Test")
        bible.add_open_thread("The missing key")
        bible.add_open_thread("The missing key")
        self.assertEqual(bible.data["open_threads"].count("The missing key"), 1)

    def test_close_nonexistent_thread(self) -> None:
        """Closing a thread that isn't open should be a no-op."""
        bible = StoryBible(self.novel_dir, "Test")
        bible.close_thread("Never opened")
        self.assertEqual(len(bible.data["closed_threads"]), 0)

    def test_set_last_excerpt(self) -> None:
        """set_last_excerpt should store trimmed text."""
        bible = StoryBible(self.novel_dir, "Test")
        long_text = " ".join([f"word{i}" for i in range(500)])
        bible.set_last_excerpt(long_text, max_words=350)
        excerpt_words = bible.data["last_excerpt"].split()
        self.assertLessEqual(len(excerpt_words), 350)

    def test_set_last_excerpt_short_text(self) -> None:
        """Short text should be stored as-is."""
        bible = StoryBible(self.novel_dir, "Test")
        bible.set_last_excerpt("Short text here.")
        self.assertEqual(bible.data["last_excerpt"], "Short text here.")

    def test_render_for_context(self) -> None:
        """render_for_context should produce a compact string."""
        bible = StoryBible(self.novel_dir, "Epic Novel")
        bible.update({"genre": "Fantasy", "tone": "Dark", "premise": "A war-torn kingdom."})
        bible.add_character("Marcus", "A soldier", role="protagonist")
        bible.add_place("Iron Keep", "A fortress")
        bible.add_open_thread("The stolen crown")
        bible.add_timeline_event(1, "Marcus arrives")

        context = bible.render_for_context()
        self.assertIn("Epic Novel", context)
        self.assertIn("Fantasy", context)
        self.assertIn("Marcus", context)
        self.assertIn("Iron Keep", context)
        self.assertIn("stolen crown", context)
        self.assertIn("Marcus arrives", context)

    def test_render_for_context_respects_max_chars(self) -> None:
        """Output should not exceed max_chars."""
        bible = StoryBible(self.novel_dir, "Test")
        # Add lots of data
        for i in range(50):
            bible._data["rules"].append(f"Rule number {i} with a long description to fill space.")
        context = bible.render_for_context(max_chars=500)
        self.assertLessEqual(len(context), 520)  # Allow small overshoot for trim marker

    def test_data_property(self) -> None:
        """data property should return the internal dict."""
        bible = StoryBible(self.novel_dir, "Test")
        self.assertIsInstance(bible.data, dict)
        self.assertEqual(bible.data["title"], "Test")

    def test_empty_schema(self) -> None:
        """_empty() should return valid schema with all required keys."""
        bible = StoryBible(self.novel_dir, "Test")
        empty = bible._empty()
        required_keys = ["version", "title", "genre", "tone", "premise",
                         "characters", "places", "rules", "timeline",
                         "open_threads", "closed_threads", "voice_notes",
                         "chapter_count", "last_excerpt"]
        for key in required_keys:
            self.assertIn(key, empty, f"Missing key: {key}")


class TestNovelManager(unittest.TestCase):
    """Test NovelManager — novel lifecycle management."""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.stories_dir = os.path.join(self.test_dir, "stories")
        os.makedirs(self.stories_dir, exist_ok=True)
        self.manager = NovelManager(self.stories_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_creates_novels_dir(self) -> None:
        """NovelManager should create the novels subdirectory."""
        expected = os.path.join(self.stories_dir, "novels")
        self.assertTrue(os.path.exists(expected))

    def test_create_novel(self) -> None:
        """create_novel should return a StoryBible with correct metadata."""
        bible = self.manager.create_novel("The Iron Gate", genre="Fantasy",
                                          tone="Epic", premise="A siege story.")
        self.assertIsInstance(bible, StoryBible)
        self.assertEqual(bible.data["title"], "The Iron Gate")
        self.assertEqual(bible.data["genre"], "Fantasy")
        self.assertEqual(bible.data["tone"], "Epic")
        self.assertIn("siege", bible.data["premise"])

    def test_create_novel_makes_directory(self) -> None:
        """Novel directory should be created on disk."""
        self.manager.create_novel("Test Novel")
        slug = "test_novel"
        novel_dir = os.path.join(self.stories_dir, "novels", slug)
        self.assertTrue(os.path.exists(novel_dir))
        self.assertTrue(os.path.exists(os.path.join(novel_dir, "bible.json")))

    def test_list_novels_empty(self) -> None:
        """list_novels should return empty list when no novels exist."""
        self.assertEqual(self.manager.list_novels(), [])

    def test_list_novels_with_data(self) -> None:
        """list_novels should find created novels."""
        self.manager.create_novel("Novel One", genre="Fantasy")
        self.manager.create_novel("Novel Two", genre="Sci-Fi")
        novels = self.manager.list_novels()
        self.assertEqual(len(novels), 2)
        titles = {n["title"] for n in novels}
        self.assertIn("Novel One", titles)
        self.assertIn("Novel Two", titles)

    def test_load_novel(self) -> None:
        """load_novel should return a valid StoryBible."""
        bible = self.manager.create_novel("Loadable Novel", genre="Mystery")
        bible.add_character("Detective", "A sharp mind")
        slug = "loadable_novel"
        loaded = self.manager.load_novel(slug)
        self.assertEqual(loaded.data["title"], "Loadable Novel")
        self.assertIn("Detective", loaded.data["characters"])

    def test_load_nonexistent_novel_raises(self) -> None:
        """load_novel should raise FileNotFoundError for missing novels."""
        with self.assertRaises(FileNotFoundError):
            self.manager.load_novel("nonexistent_slug")

    def test_save_and_load_chapter(self) -> None:
        """Chapters should survive save/load cycle."""
        bible = self.manager.create_novel("Chapter Test")
        chapter_text = "The morning came cold and unforgiving."
        path = self.manager.save_chapter(bible, 1, chapter_text, title="Dawn")

        self.assertTrue(os.path.exists(path))
        loaded = self.manager.load_chapter(bible, 1)
        self.assertIn("morning came cold", loaded)
        self.assertIn("Chapter 1: Dawn", loaded)

    def test_save_chapter_updates_bible(self) -> None:
        """save_chapter should update chapter_count and last_excerpt."""
        bible = self.manager.create_novel("Update Test")
        self.manager.save_chapter(bible, 1, "First chapter text here.")
        self.assertEqual(bible.data["chapter_count"], 1)
        self.assertIn("First chapter text", bible.data["last_excerpt"])

    def test_load_nonexistent_chapter(self) -> None:
        """Loading a chapter that doesn't exist should return empty string."""
        bible = self.manager.create_novel("Empty Chapter Test")
        loaded = self.manager.load_chapter(bible, 99)
        self.assertEqual(loaded, "")

    def test_list_chapters(self) -> None:
        """list_chapters should return sorted chapter info."""
        bible = self.manager.create_novel("Multi Chapter")
        self.manager.save_chapter(bible, 1, "Chapter one content.", title="Beginning")
        self.manager.save_chapter(bible, 2, "Chapter two content.", title="Middle")
        self.manager.save_chapter(bible, 3, "Chapter three content.", title="End")

        chapters = self.manager.list_chapters(bible)
        self.assertEqual(len(chapters), 3)
        self.assertEqual(chapters[0]["num"], 1)
        self.assertEqual(chapters[2]["num"], 3)
        self.assertIn("word_count", chapters[0])
        self.assertGreater(chapters[0]["word_count"], 0)

    def test_list_chapters_empty(self) -> None:
        """list_chapters should return empty list for novel with no chapters."""
        bible = self.manager.create_novel("No Chapters")
        chapters = self.manager.list_chapters(bible)
        self.assertEqual(chapters, [])

    def test_assemble_novel(self) -> None:
        """assemble_novel should concatenate all chapters."""
        bible = self.manager.create_novel("Assembly Test", premise="A test premise.")
        self.manager.save_chapter(bible, 1, "Chapter one body.")
        self.manager.save_chapter(bible, 2, "Chapter two body.")
        manuscript = self.manager.assemble_novel(bible)
        self.assertIn("Assembly Test", manuscript)
        self.assertIn("test premise", manuscript)
        self.assertIn("Chapter one body", manuscript)
        self.assertIn("Chapter two body", manuscript)

    def test_export_novel_txt(self) -> None:
        """export_novel_txt should create a text file."""
        bible = self.manager.create_novel("Export Test")
        self.manager.save_chapter(bible, 1, "Export chapter content.")
        out_path = self.manager.export_novel_txt(bible)
        self.assertTrue(os.path.exists(out_path))
        self.assertTrue(out_path.endswith(".txt"))
        with open(out_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("Export chapter content", content)

    def test_slugify(self) -> None:
        """_slugify should produce clean URL-safe slugs."""
        self.assertEqual(self.manager._slugify("Hello World"), "hello_world")
        self.assertEqual(self.manager._slugify("Test: Novel!"), "test_novel")
        self.assertEqual(self.manager._slugify("A" * 100)[:50], "a" * 50)
        self.assertEqual(self.manager._slugify(""), "novel")

    def test_get_chapter_path(self) -> None:
        """get_chapter_path should return properly formatted path."""
        bible = self.manager.create_novel("Path Test")
        path = self.manager.get_chapter_path(bible, 5)
        self.assertIn("chapter_005.md", path)

    def test_build_chapter_prompt(self) -> None:
        """build_chapter_prompt should include bible context and brief."""
        bible = self.manager.create_novel("Prompt Test", genre="Fantasy")
        bible.add_character("Hero", "The protagonist")
        bible.set_last_excerpt("Previous chapter ended here.")

        prompt = NovelManager.build_chapter_prompt(
            bible, chapter_num=2,
            chapter_brief="The hero enters the dungeon.",
            word_count=1500
        )
        self.assertIn("Prompt Test", prompt)
        self.assertIn("Hero", prompt)
        self.assertIn("enters the dungeon", prompt)
        self.assertIn("1500 words", prompt)
        self.assertIn("PREVIOUS CHAPTER", prompt)
        self.assertIn("Previous chapter ended here", prompt)
        # Should include PROMPT_NAME_BAN
        from banned_content import PROMPT_NAME_BAN
        self.assertIn("Character naming requirement", prompt)

    def test_build_chapter_prompt_first_chapter(self) -> None:
        """First chapter should not include previous excerpt section."""
        bible = self.manager.create_novel("First Chapter Test")
        prompt = NovelManager.build_chapter_prompt(bible, 1, "The opening scene.")
        self.assertNotIn("PREVIOUS CHAPTER", prompt)

    def test_build_bible_update_prompt(self) -> None:
        """build_bible_update_prompt should include chapter text and JSON format."""
        bible = self.manager.create_novel("Update Prompt Test")
        chapter_text = "Marcus drew his sword and charged at the gate."
        prompt = NovelManager.build_bible_update_prompt(bible, 1, chapter_text)
        self.assertIn("Chapter 1", prompt)
        self.assertIn("Marcus drew his sword", prompt)
        self.assertIn("new_characters", prompt)
        self.assertIn("new_places", prompt)
        self.assertIn("JSON", prompt)

    def test_apply_bible_update_valid_json(self) -> None:
        """apply_bible_update should parse JSON and update bible."""
        bible = self.manager.create_novel("Apply Update Test")
        update_json = json.dumps({
            "new_characters": [{"name": "Vera", "description": "A healer", "role": "ally", "arc": "Growth"}],
            "new_places": [{"name": "The Well", "description": "A sacred spring", "significance": "Healing"}],
            "new_rules": ["Magic costs lifeforce"],
            "timeline_events": ["Vera heals the wounded"],
            "new_open_threads": ["What lurks beneath the well?"],
            "closed_threads": [],
            "voice_notes": "Keep the prose spare."
        })
        added = NovelManager.apply_bible_update(bible, 1, update_json)
        self.assertGreater(len(added), 0)
        self.assertIn("Vera", bible.data["characters"])
        self.assertIn("The Well", bible.data["places"])
        self.assertIn("Magic costs lifeforce", bible.data["rules"])
        self.assertIn("What lurks beneath the well?", bible.data["open_threads"])
        self.assertIn("spare", bible.data["voice_notes"])

    def test_apply_bible_update_with_markdown_fences(self) -> None:
        """Should handle JSON wrapped in markdown code fences."""
        bible = self.manager.create_novel("Fence Test")
        update = '```json\n{"new_characters": [{"name": "Rook", "description": "A scout"}], "new_places": [], "new_rules": [], "timeline_events": [], "new_open_threads": [], "closed_threads": [], "voice_notes": ""}\n```'
        added = NovelManager.apply_bible_update(bible, 1, update)
        self.assertIn("Rook", bible.data["characters"])

    def test_apply_bible_update_invalid_json(self) -> None:
        """Should return empty list for garbage input."""
        bible = self.manager.create_novel("Bad JSON Test")
        added = NovelManager.apply_bible_update(bible, 1, "this is not json at all")
        self.assertEqual(added, [])

    def test_apply_bible_update_no_json(self) -> None:
        """Should return empty list when no JSON object found."""
        bible = self.manager.create_novel("No JSON Test")
        added = NovelManager.apply_bible_update(bible, 1, "Just some text without braces")
        self.assertEqual(added, [])

    def test_apply_bible_update_closes_thread(self) -> None:
        """Should move thread from open to closed."""
        bible = self.manager.create_novel("Close Thread Test")
        bible.add_open_thread("The mystery of the key")
        update = json.dumps({
            "new_characters": [], "new_places": [], "new_rules": [],
            "timeline_events": [], "new_open_threads": [],
            "closed_threads": ["The mystery of the key"],
            "voice_notes": ""
        })
        NovelManager.apply_bible_update(bible, 2, update)
        self.assertNotIn("The mystery of the key", bible.data["open_threads"])
        self.assertIn("The mystery of the key", bible.data["closed_threads"])

    def test_count_chapters(self) -> None:
        """_count_chapters should count chapter files."""
        bible = self.manager.create_novel("Count Test")
        self.manager.save_chapter(bible, 1, "Ch 1")
        self.manager.save_chapter(bible, 2, "Ch 2")
        count = self.manager._count_chapters(bible.novel_dir)
        self.assertEqual(count, 2)


if __name__ == '__main__':
    unittest.main()
