#!/usr/bin/env python3
"""
Unit tests for banned_content.py — the post-generation content validator.
"""
import unittest
from banned_content import (
    check_banned_names, check_banned_words, check_banned_phrases,
    check_banned_dialogue, validate_story,
    BANNED_NAMES_ALL, BANNED_WORDS, BANNED_PHRASES, BANNED_DIALOGUE,
    PROMPT_NAME_BAN,
)


class TestCheckBannedNames(unittest.TestCase):
    """Test banned name detection."""

    def test_detects_female_banned_name(self):
        """Should detect banned female names case-insensitively."""
        result = check_banned_names("Elara walked through the forest.")
        names_found = [name for name, _ in result]
        self.assertIn("elara", names_found)

    def test_detects_male_banned_name(self):
        """Should detect banned male names."""
        result = check_banned_names("Kael drew his sword.")
        names_found = [name for name, _ in result]
        self.assertIn("kael", names_found)

    def test_detects_place_banned_name(self):
        """Should detect banned place names."""
        result = check_banned_names("The city of Eldoria shimmered.")
        names_found = [name for name, _ in result]
        self.assertIn("eldoria", names_found)

    def test_case_insensitive(self):
        """Should match regardless of case."""
        result = check_banned_names("ELARA and elara and Elara.")
        self.assertEqual(len(result), 1)  # One name, multiple positions
        name, positions = result[0]
        self.assertEqual(name, "elara")
        self.assertEqual(len(positions), 3)  # Found 3 times

    def test_no_false_positives_on_substrings(self):
        """Should not match partial words (word boundary matching)."""
        result = check_banned_names("The declaration was clear.")
        self.assertEqual(len(result), 0)

    def test_clean_text_returns_empty(self):
        """Clean text should return no matches."""
        result = check_banned_names("Marcus walked through the village of Thornbury.")
        self.assertEqual(len(result), 0)

    def test_empty_text(self):
        """Empty text should return no matches."""
        self.assertEqual(check_banned_names(""), [])

    def test_multiple_banned_names(self):
        """Should detect multiple distinct banned names."""
        result = check_banned_names("Elara met Kael in Eldoria.")
        names_found = {name for name, _ in result}
        self.assertIn("elara", names_found)
        self.assertIn("kael", names_found)
        self.assertIn("eldoria", names_found)
        self.assertEqual(len(names_found), 3)


class TestCheckBannedWords(unittest.TestCase):
    """Test banned vocabulary word detection."""

    def test_detects_banned_word(self):
        """Should detect common AI-slop words."""
        result = check_banned_words("She began to delve into the mystery.")
        words_found = [word for word, _ in result]
        self.assertIn("delve", words_found)

    def test_detects_multiple_banned_words(self):
        """Should detect multiple banned words."""
        result = check_banned_words("The intricate tapestry of the obsidian realm.")
        words_found = {word for word, _ in result}
        self.assertTrue(len(words_found) >= 3)

    def test_counts_occurrences(self):
        """Should count how many times each word appears."""
        result = check_banned_words("The realm within the realm was vast.")
        realm_entry = next((w, c) for w, c in result if w == "realm")
        self.assertEqual(realm_entry[1], 2)

    def test_clean_text_returns_empty(self):
        """Clean text should return no matches."""
        result = check_banned_words("The cat sat on the mat.")
        self.assertEqual(len(result), 0)

    def test_empty_text(self):
        self.assertEqual(check_banned_words(""), [])


class TestCheckBannedPhrases(unittest.TestCase):
    """Test banned phrase detection."""

    def test_detects_banned_phrase(self):
        """Should detect AI-slop phrases."""
        result = check_banned_phrases("It was a testament to her strength.")
        phrases_found = [phrase for phrase, _ in result]
        self.assertIn("a testament to", phrases_found)

    def test_detects_foreshadowing_cliche(self):
        """Should detect 'little did they know' and similar."""
        result = check_banned_phrases("Little did they know what awaited them.")
        phrases_found = [phrase for phrase, _ in result]
        self.assertIn("little did they know", phrases_found)

    def test_clean_text_returns_empty(self):
        result = check_banned_phrases("The road stretched endlessly ahead.")
        self.assertEqual(len(result), 0)

    def test_empty_text(self):
        self.assertEqual(check_banned_phrases(""), [])


class TestCheckBannedDialogue(unittest.TestCase):
    """Test banned dialogue crutch detection."""

    def test_detects_banned_dialogue(self):
        """Should detect AI-typical dialogue crutches."""
        result = check_banned_dialogue('He said, "You don\'t understand."')
        lines_found = [line for line, _ in result]
        self.assertIn("you don't understand", lines_found)

    def test_detects_multiple_crutches(self):
        text = '"We don\'t have much time," she said. "This changes everything."'
        result = check_banned_dialogue(text)
        self.assertEqual(len(result), 2)

    def test_clean_dialogue_returns_empty(self):
        result = check_banned_dialogue('"Pass the salt," he muttered.')
        self.assertEqual(len(result), 0)

    def test_empty_text(self):
        self.assertEqual(check_banned_dialogue(""), [])


class TestValidateStory(unittest.TestCase):
    """Test the full validate_story pipeline."""

    def test_clean_story_returns_clean(self):
        """A clean story should pass validation."""
        story = "Marcus walked through the village square. The morning sun warmed the cobblestones."
        result = validate_story(story)
        self.assertTrue(result['clean'])
        self.assertEqual(result['total_violations'], 0)
        self.assertEqual(result['high_severity_count'], 0)
        self.assertEqual(len(result['violations']), 0)

    def test_dirty_story_catches_everything(self):
        """A story with all violation types should catch them all."""
        story = (
            'Elara walked through the obsidian tower. '
            'The enigmatic stranger whispered, "You don\'t understand." '
            'It was a testament to her courage.'
        )
        result = validate_story(story)
        self.assertFalse(result['clean'])
        self.assertGreater(result['total_violations'], 0)
        self.assertGreater(result['high_severity_count'], 0)

        categories = {v['category'] for v in result['violations']}
        self.assertIn('banned_name', categories)
        self.assertIn('banned_word', categories)
        self.assertIn('banned_dialogue', categories)
        self.assertIn('banned_phrase', categories)

    def test_preamble_detection(self):
        """Should detect model preamble (contract violation)."""
        story = 'Okay, here is a story about a brave knight.\n\nThe knight rode forth.'
        result = validate_story(story)
        preamble_violations = [v for v in result['violations'] if v['category'] == 'preamble']
        self.assertEqual(len(preamble_violations), 1)
        self.assertEqual(preamble_violations[0]['severity'], 'high')

    def test_preamble_variants(self):
        """Should detect various preamble forms."""
        preambles = [
            "Here is a story about a cat.",
            "Here's a tale of adventure.",
            "Sure, I'd be happy to write that.",
            "Certainly, here is your story.",
            "I'd be happy to help with that.",
            "Let me write that for you.",
            "Below is the story you requested.",
        ]
        for preamble in preambles:
            result = validate_story(preamble)
            preamble_found = any(v['category'] == 'preamble' for v in result['violations'])
            self.assertTrue(preamble_found, f"Failed to detect preamble: '{preamble}'")

    def test_no_preamble_on_clean_start(self):
        """Should NOT flag a story that starts with normal prose."""
        story = "The morning light filtered through the curtains."
        result = validate_story(story)
        preamble_found = any(v['category'] == 'preamble' for v in result['violations'])
        self.assertFalse(preamble_found)

    def test_severity_ordering(self):
        """Violations should be sorted by severity: high first."""
        story = (
            'Elara walked through the obsidian tower. '
            '"You don\'t understand," she whispered.'
        )
        result = validate_story(story)
        severities = [v['severity'] for v in result['violations']]
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        ordered = sorted(severities, key=lambda s: severity_order[s])
        self.assertEqual(severities, ordered)

    def test_violation_structure(self):
        """Each violation should have required keys."""
        story = "Elara delved into the mystery."
        result = validate_story(story)
        for v in result['violations']:
            self.assertIn('category', v)
            self.assertIn('item', v)
            self.assertIn('count', v)
            self.assertIn('severity', v)

    def test_empty_text(self):
        """Empty text should be clean."""
        result = validate_story("")
        self.assertTrue(result['clean'])

    def test_whitespace_only_text(self):
        """Whitespace-only text should be clean (no preamble false positive)."""
        result = validate_story("   \n\t  ")
        self.assertTrue(result['clean'])


class TestPromptNameBan(unittest.TestCase):
    """Test the PROMPT_NAME_BAN constant."""

    def test_prompt_name_ban_is_nonempty_string(self):
        self.assertIsInstance(PROMPT_NAME_BAN, str)
        self.assertGreater(len(PROMPT_NAME_BAN), 100)

    def test_prompt_name_ban_contains_key_names(self):
        """Should reference the most common offenders."""
        self.assertIn("Elara", PROMPT_NAME_BAN)
        self.assertIn("Kael", PROMPT_NAME_BAN)
        self.assertIn("Eldoria", PROMPT_NAME_BAN)


class TestBannedContentSets(unittest.TestCase):
    """Test the banned content data sets themselves."""

    def test_banned_names_all_is_union(self):
        """BANNED_NAMES_ALL should be the union of all name sets."""
        from banned_content import BANNED_NAMES_FEMALE, BANNED_NAMES_MALE, BANNED_NAMES_PLACES
        expected = BANNED_NAMES_FEMALE | BANNED_NAMES_MALE | BANNED_NAMES_PLACES
        self.assertEqual(BANNED_NAMES_ALL, expected)

    def test_sets_are_nonempty(self):
        self.assertGreater(len(BANNED_NAMES_ALL), 50)
        self.assertGreater(len(BANNED_WORDS), 30)
        self.assertGreater(len(BANNED_PHRASES), 10)
        self.assertGreater(len(BANNED_DIALOGUE), 5)

    def test_all_names_are_lowercase(self):
        """All name entries should be lowercase for consistent matching."""
        for name in BANNED_NAMES_ALL:
            self.assertEqual(name, name.lower(), f"Name '{name}' should be lowercase")

    def test_all_words_are_lowercase(self):
        for word in BANNED_WORDS:
            self.assertEqual(word, word.lower(), f"Word '{word}' should be lowercase")

    def test_all_dialogue_is_lowercase(self):
        for line in BANNED_DIALOGUE:
            self.assertEqual(line, line.lower(), f"Dialogue '{line}' should be lowercase")


if __name__ == '__main__':
    unittest.main()
