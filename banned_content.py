"""
banned_content.py — Single source of truth for all banned names, words, phrases,
dialogue crutches, and tropes in story generation.

Used by:
  - story_generator.py (_build_prompt, build_chapter_prompt, StoryValidator)
  - GemmaNovelist.md (reference only — the modelfile has its own copy for the SYSTEM prompt)

When you update this file, the code-level enforcement updates automatically.
The modelfile (GemmaNovelist.md) must be updated separately and rebuilt with:
    ollama create gemma-novelist -f GemmaNovelist.md
"""

import re

# ── Banned Character Names ────────────────────────────────────────────────────
# These appear 10-100x more in AI-generated fiction than in human writing.
# Source: Goodreads AI-slop tracking, GPTZero vocabulary analysis, Kaggle
# sci-fi dataset analysis (Elara alone appears in 124+ catalogued AI books).

BANNED_NAMES_FEMALE = {
    "elara", "lyra", "kira", "aria", "seraphina", "mira", "zara", "luna",
    "isolde", "freya", "selene", "anya", "astra", "elysia", "lilith",
    "cassandra", "morgana", "celeste", "aurora", "nova", "sable", "ember",
    "raven", "nyx", "althea", "elena", "elira", "elarya", "liora",
}

BANNED_NAMES_MALE = {
    "kael", "theron", "aiden", "kai", "rowan", "finn", "asher", "orion",
    "caspian", "jasper", "thorne", "draven", "lucian", "caelum", "kaelan",
    "kaelen", "zephyr", "silas", "dorian", "ren", "rylan", "callum",
    "declan", "evander", "gideon", "alaric", "cedric",
}

BANNED_NAMES_PLACES = {
    "eldoria", "aethermoor", "shadowvale", "thornfield", "ravenhollow",
    "celestia", "silverpeak", "ironhold", "stormwatch", "crystalspire",
    "moonhaven", "duskwood", "frosthollow", "brightwater", "ashenmoor",
    "starfall", "dreamspire", "nethervale", "wyrmrest", "aethelgard",
}

# Combined set for fast lookup
BANNED_NAMES_ALL = BANNED_NAMES_FEMALE | BANNED_NAMES_MALE | BANNED_NAMES_PLACES


# ── Banned Vocabulary ─────────────────────────────────────────────────────────
# Words that appear 10-120x more in AI-generated prose than human writing.
# Source: GPTZero AI Vocabulary analysis, Grammarly AI words study,
# ContentBeta 300+ word list, Embryo cross-referencing study.

BANNED_WORDS = {
    "delve", "tapestry", "testament", "beacon", "intricate", "resonate",
    "navigate", "foster", "realm", "embark", "landscape", "crucial",
    "unveil", "pivotal", "nuance", "multifaceted", "comprehensive",
    "paradigm", "synergy", "leverage", "robust", "hone", "facilitate",
    "myriad", "plethora", "underscore", "bolster", "bespoke", "paramount",
    "commendable", "noteworthy", "vital", "moreover", "furthermore",
    "indeed", "poignant", "profound", "stark", "visceral", "ethereal",
    "ephemeral", "enigmatic", "luminous", "iridescent", "gossamer",
    "eldritch", "verdant", "obsidian", "azure", "alabaster",
}

BANNED_PHRASES = {
    "a testament to", "the tapestry of", "it is worth noting",
    "a delicate balance", "in the realm of", "a beacon of",
    "the landscape of", "serves as a reminder", "at the heart of",
    "the intricacies of", "a sense of foreboding", "the weight of the world",
    "little did they know", "the air was thick with", "a chill ran down",
    "time seemed to stop", "darkness threatened to consume",
    "a flicker of hope", "the silence was deafening",
    "eyes that held centuries", "ancient power stirred",
    "destiny awaited", "the chosen one", "a prophecy foretold",
    "the balance between light and dark",
}

BANNED_DIALOGUE = {
    "i never asked for this", "you don't understand",
    "we don't have much time", "there's something you should know",
    "it's not that simple", "you're the only one who can",
    "i made a promise", "this changes everything",
}


# ── Prompt-level Name Ban (injected into user prompts) ────────────────────────
# This text is appended to every generation prompt. System prompts alone
# are insufficient for 12B models — deeply trained name preferences override them.

PROMPT_NAME_BAN = (
    "Character naming requirement: do NOT use any of these names: "
    "Elara, Lyra, Kira, Aria, Seraphina, Zara, Mira, Kael, Theron, Aiden, "
    "Luna, Freya, Selene, Anya, Thorne, Draven, Lucian, Orion, Caspian, "
    "Aurora, Nova, Ember, Raven, Silas, Dorian, Finn, Rowan, Asher. "
    "These names are forbidden. Also do not use place names like Eldoria, "
    "Shadowvale, Thornfield, Ravenhollow, Moonhaven, or Aethermoor. "
    "Instead, derive each character's name from their specific cultural "
    "background, region, class, and era within the story's world. "
    "The name must feel like it belongs only to this character in this world."
)


def check_banned_names(text: str) -> list:
    """
    Scan text for banned names. Returns list of (name, positions) tuples.
    Case-insensitive word-boundary matching.
    """
    found = []
    text_lower = text.lower()
    for name in BANNED_NAMES_ALL:
        # Word boundary match to avoid false positives (e.g. "realm" in "realms")
        pattern = r'\b' + re.escape(name) + r'\b'
        matches = list(re.finditer(pattern, text_lower))
        if matches:
            positions = [m.start() for m in matches]
            found.append((name, positions))
    return found


def check_banned_words(text: str) -> list:
    """
    Scan text for banned vocabulary words. Returns list of (word, count) tuples.
    """
    found = []
    text_lower = text.lower()
    for word in BANNED_WORDS:
        pattern = r'\b' + re.escape(word) + r'\b'
        matches = list(re.finditer(pattern, text_lower))
        if matches:
            found.append((word, len(matches)))
    return found


def check_banned_phrases(text: str) -> list:
    """
    Scan text for banned phrases. Returns list of (phrase, count) tuples.
    """
    found = []
    text_lower = text.lower()
    for phrase in BANNED_PHRASES:
        count = text_lower.count(phrase)
        if count > 0:
            found.append((phrase, count))
    return found


def check_banned_dialogue(text: str) -> list:
    """
    Scan text for banned dialogue crutches. Returns list of (line, count) tuples.
    """
    found = []
    text_lower = text.lower()
    for line in BANNED_DIALOGUE:
        count = text_lower.count(line)
        if count > 0:
            found.append((line, count))
    return found


def validate_story(text: str) -> dict:
    """
    Run all validators against a story. Returns a report dict.

    Usage:
        from banned_content import validate_story
        report = validate_story(story_text)
        if not report['clean']:
            print(f"Found {report['total_violations']} violations")
            for v in report['violations']:
                print(f"  [{v['category']}] {v['item']} (x{v['count']})")
    """
    violations = []

    for name, positions in check_banned_names(text):
        violations.append({
            "category": "banned_name",
            "item": name,
            "count": len(positions),
            "severity": "high",
        })

    for word, count in check_banned_words(text):
        violations.append({
            "category": "banned_word",
            "item": word,
            "count": count,
            "severity": "medium",
        })

    for phrase, count in check_banned_phrases(text):
        violations.append({
            "category": "banned_phrase",
            "item": phrase,
            "count": count,
            "severity": "medium",
        })

    for line, count in check_banned_dialogue(text):
        violations.append({
            "category": "banned_dialogue",
            "item": line,
            "count": count,
            "severity": "low",
        })

    # Check for preamble / postamble (model breaking the contract)
    first_line = text.strip().split('\n')[0].lower() if text.strip() else ""
    preamble_markers = [
        "okay, here", "here is", "here's a", "sure,", "certainly",
        "i'd be happy", "let me", "of course", "here you go",
        "i've tried", "i've written", "below is",
    ]
    for marker in preamble_markers:
        if first_line.startswith(marker):
            violations.append({
                "category": "preamble",
                "item": f"Story begins with: \"{first_line[:60]}...\"",
                "count": 1,
                "severity": "high",
            })
            break

    total = sum(v["count"] for v in violations)
    high_count = sum(v["count"] for v in violations if v["severity"] == "high")

    return {
        "clean": total == 0,
        "total_violations": total,
        "high_severity_count": high_count,
        "violations": sorted(violations, key=lambda v: {"high": 0, "medium": 1, "low": 2}[v["severity"]]),
    }
