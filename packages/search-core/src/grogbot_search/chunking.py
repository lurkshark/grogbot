from __future__ import annotations

import re
from typing import Iterable, List

from bs4 import BeautifulSoup
import markdown as markdown_lib

TARGET_WORDS = 512
MAX_WORDS = 1024


def markdown_to_text(markdown: str) -> str:
    html = markdown_lib.markdown(markdown)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def _split_sections(markdown: str) -> List[str]:
    sections: List[str] = []
    current: List[str] = []
    for line in markdown.splitlines():
        if line.lstrip().startswith("#"):
            if current:
                sections.append("\n".join(current).strip())
                current = []
        current.append(line)
    if current:
        sections.append("\n".join(current).strip())
    return [section for section in sections if section]


def _split_paragraphs(section: str) -> List[str]:
    return [para.strip() for para in re.split(r"\n\s*\n", section) if para.strip()]


def _split_sentences(text: str) -> List[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def _word_count(text: str) -> int:
    return len(text.split())


def chunk_markdown(markdown: str) -> List[str]:
    sections = _split_sections(markdown)
    blocks: List[str] = []
    for section in sections:
        blocks.extend(_split_paragraphs(section))

    chunks: List[str] = []
    current: List[str] = []
    current_words = 0

    def flush_current() -> None:
        nonlocal current, current_words
        if current:
            chunks.append("\n\n".join(current).strip())
        current = []
        current_words = 0

    for block in blocks:
        block_text = markdown_to_text(block)
        block_words = _word_count(block_text)
        if block_words > MAX_WORDS:
            if current:
                flush_current()
            sentences = _split_sentences(block_text)
            sentence_group: List[str] = []
            sentence_words = 0
            for sentence in sentences:
                word_count = _word_count(sentence)
                if sentence_words + word_count > MAX_WORDS and sentence_group:
                    chunks.append(" ".join(sentence_group).strip())
                    sentence_group = []
                    sentence_words = 0
                sentence_group.append(sentence)
                sentence_words += word_count
                if sentence_words >= TARGET_WORDS:
                    chunks.append(" ".join(sentence_group).strip())
                    sentence_group = []
                    sentence_words = 0
            if sentence_group:
                chunks.append(" ".join(sentence_group).strip())
            continue

        if current_words + block_words > MAX_WORDS and current:
            flush_current()

        current.append(block)
        current_words += block_words

        if current_words >= TARGET_WORDS:
            flush_current()

    flush_current()
    return [markdown_to_text(chunk) for chunk in chunks if chunk]
