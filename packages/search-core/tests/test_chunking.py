from __future__ import annotations

import grogbot_search.chunking as chunking


def test_default_chunk_size_bounds():
    assert chunking.TARGET_WORDS == 512
    assert chunking.MAX_WORDS == 1024
    assert chunking.MAX_CHARS == 4096


def test_split_sections_breaks_on_headings():
    markdown = """intro line
# Heading One
body one
## Heading Two
body two
"""

    sections = chunking._split_sections(markdown)

    assert sections == [
        "intro line",
        "# Heading One\nbody one",
        "## Heading Two\nbody two",
    ]


def test_split_sentences_strips_whitespace_and_empties():
    sentences = chunking._split_sentences("  First sentence.  Second sentence!   Third?   ")

    assert sentences == ["First sentence.", "Second sentence!", "Third?"]


def test_chunk_markdown_formats_top_two_context_and_truncates_deeper_levels(monkeypatch):
    monkeypatch.setattr(chunking, "TARGET_WORDS", 100)
    monkeypatch.setattr(chunking, "MAX_WORDS", 100)

    markdown = """# API

intro text

## Auth

token flow

### Refresh

refresh tokens
"""

    chunks = chunking.chunk_markdown(markdown)

    assert chunks == [
        "API intro text",
        "API > Auth token flow refresh tokens",
    ]


def test_chunk_markdown_flushes_when_context_changes(monkeypatch):
    monkeypatch.setattr(chunking, "TARGET_WORDS", 100)
    monkeypatch.setattr(chunking, "MAX_WORDS", 100)

    markdown = """# Alpha

first block

## Beta

second block

# Gamma

third block
"""

    chunks = chunking.chunk_markdown(markdown)

    assert chunks == [
        "Alpha first block",
        "Alpha > Beta second block",
        "Gamma third block",
    ]


def test_chunk_markdown_skips_heading_only_sections():
    markdown = """# One

## Two

### Three
"""

    chunks = chunking.chunk_markdown(markdown)

    assert chunks == []


def test_chunk_markdown_context_counts_toward_hard_limit(monkeypatch):
    monkeypatch.setattr(chunking, "TARGET_WORDS", 100)
    monkeypatch.setattr(chunking, "MAX_WORDS", 4)

    markdown = """# very long heading context for this section

one two three four
"""

    chunks = chunking.chunk_markdown(markdown)

    assert chunks == [
        "very long heading one",
        "very long heading two",
        "very long heading three",
        "very long heading four",
    ]
    assert all(chunking._word_count(chunk) <= chunking.MAX_WORDS for chunk in chunks)


def test_chunk_markdown_splits_oversized_block_by_sentences_with_context(monkeypatch):
    monkeypatch.setattr(chunking, "TARGET_WORDS", 4)
    monkeypatch.setattr(chunking, "MAX_WORDS", 6)

    markdown = """# Heading

preface words

one two three. four five six. seven eight nine.
"""

    chunks = chunking.chunk_markdown(markdown)

    assert chunks == [
        "Heading preface words",
        "Heading one two three.",
        "Heading four five six.",
        "Heading seven eight nine.",
    ]


def test_chunk_markdown_flushes_when_next_block_would_exceed_max(monkeypatch):
    monkeypatch.setattr(chunking, "TARGET_WORDS", 100)
    monkeypatch.setattr(chunking, "MAX_WORDS", 5)

    markdown = """one two three

four five six
"""

    chunks = chunking.chunk_markdown(markdown)

    assert chunks == ["one two three", "four five six"]


def test_chunk_markdown_sentence_group_flushes_on_max_overflow_with_context(monkeypatch):
    monkeypatch.setattr(chunking, "TARGET_WORDS", 100)
    monkeypatch.setattr(chunking, "MAX_WORDS", 5)

    markdown = """# Heading

one two three. four five six.
"""

    chunks = chunking.chunk_markdown(markdown)

    assert chunks == ["Heading one two three.", "Heading four five six."]


def test_chunk_markdown_flushes_when_target_is_reached(monkeypatch):
    monkeypatch.setattr(chunking, "TARGET_WORDS", 3)
    monkeypatch.setattr(chunking, "MAX_WORDS", 10)

    markdown = """one two three

four five
"""

    chunks = chunking.chunk_markdown(markdown)

    assert chunks == ["one two three", "four five"]


def test_chunk_markdown_splits_single_sentence_block_by_word_window(monkeypatch):
    monkeypatch.setattr(chunking, "TARGET_WORDS", 100)
    monkeypatch.setattr(chunking, "MAX_WORDS", 5)

    markdown = """# Heading

one two three four five six seven eight nine ten eleven
"""

    chunks = chunking.chunk_markdown(markdown)

    assert chunks == [
        "Heading one two three four",
        "Heading five six seven eight",
        "Heading nine ten eleven",
    ]
    assert all(chunking._word_count(chunk) <= chunking.MAX_WORDS for chunk in chunks)


def test_chunk_markdown_enforces_char_limit_with_hard_fallback(monkeypatch):
    monkeypatch.setattr(chunking, "TARGET_WORDS", 100)
    monkeypatch.setattr(chunking, "MAX_WORDS", 100)
    monkeypatch.setattr(chunking, "MAX_CHARS", 20)

    markdown = """abcdefghij klmnopqrst uvwxyz"""

    chunks = chunking.chunk_markdown(markdown)

    assert chunks == ["abcdefghij", "klmnopqrst uvwxyz"]
    assert all(len(chunk) <= chunking.MAX_CHARS for chunk in chunks)


def test_chunk_markdown_drops_low_signal_oversized_block(monkeypatch):
    monkeypatch.setattr(chunking, "TARGET_WORDS", 100)
    monkeypatch.setattr(chunking, "MAX_WORDS", 20)

    markdown = """BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY BUY"""

    chunks = chunking.chunk_markdown(markdown)

    assert chunks == []
