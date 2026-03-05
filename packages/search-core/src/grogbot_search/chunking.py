from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List, Optional

from bs4 import BeautifulSoup
import markdown as markdown_lib

TARGET_WORDS = 512
MAX_WORDS = 1024


@dataclass
class BodyBlock:
    text: str
    words: int
    context: str


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


def _parse_heading_line(line: str) -> Optional[tuple[int, str]]:
    match = re.match(r"^\s*(#{1,6})\s+(.*?)\s*$", line)
    if not match:
        return None

    level = len(match.group(1))
    heading_raw = re.sub(r"\s+#+\s*$", "", match.group(2)).strip()
    heading_text = markdown_to_text(heading_raw)
    if not heading_text:
        return None
    return level, heading_text


def _normalize_context_path(heading_stack: List[Optional[str]]) -> str:
    top_two = [heading for heading in heading_stack if heading][:2]
    return " > ".join(top_two)


def _parse_body_blocks(markdown: str) -> List[BodyBlock]:
    blocks: List[BodyBlock] = []
    heading_stack: List[Optional[str]] = []
    paragraph_lines: List[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if not paragraph_lines:
            return

        paragraph = "\n".join(paragraph_lines).strip()
        paragraph_lines = []
        if not paragraph:
            return

        text = markdown_to_text(paragraph)
        if not text:
            return

        blocks.append(
            BodyBlock(
                text=text,
                words=_word_count(text),
                context=_normalize_context_path(heading_stack),
            )
        )

    for line in markdown.splitlines():
        heading = _parse_heading_line(line)
        if heading is not None:
            flush_paragraph()
            level, heading_text = heading

            while len(heading_stack) < level:
                heading_stack.append(None)
            heading_stack = heading_stack[:level]
            heading_stack[level - 1] = heading_text
            continue

        if not line.strip():
            flush_paragraph()
            continue

        paragraph_lines.append(line)

    flush_paragraph()
    return blocks


def _compose_chunk_text(*, context: str, body: str) -> str:
    if context:
        return f"{context} {body}".strip()
    return body.strip()


def chunk_markdown(markdown: str) -> List[str]:
    blocks = _parse_body_blocks(markdown)

    chunks: List[str] = []
    current: List[str] = []
    current_words = 0
    current_context: Optional[str] = None

    def emit(body: str, context: str) -> None:
        body = body.strip()
        if not body:
            return
        chunks.append(_compose_chunk_text(context=context, body=body))

    def flush_current() -> None:
        nonlocal current, current_words, current_context
        if current:
            emit(" ".join(current), current_context or "")
        current = []
        current_words = 0
        current_context = None

    for block in blocks:
        if block.words > MAX_WORDS:
            flush_current()
            sentences = _split_sentences(block.text)
            sentence_group: List[str] = []
            sentence_words = 0
            for sentence in sentences:
                word_count = _word_count(sentence)
                if sentence_words + word_count > MAX_WORDS and sentence_group:
                    emit(" ".join(sentence_group), block.context)
                    sentence_group = []
                    sentence_words = 0
                sentence_group.append(sentence)
                sentence_words += word_count
                if sentence_words >= TARGET_WORDS:
                    emit(" ".join(sentence_group), block.context)
                    sentence_group = []
                    sentence_words = 0
            if sentence_group:
                emit(" ".join(sentence_group), block.context)
            continue

        if current and block.context != current_context:
            flush_current()

        if current_words + block.words > MAX_WORDS and current:
            flush_current()

        if not current:
            current_context = block.context

        current.append(block.text)
        current_words += block.words

        if current_words >= TARGET_WORDS:
            flush_current()

    flush_current()
    return chunks
