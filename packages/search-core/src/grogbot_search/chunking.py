from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List, Optional

from bs4 import BeautifulSoup
import markdown as markdown_lib

TARGET_WORDS = 512
MAX_WORDS = 1024
MAX_CHARS = 4096


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


def _split_simple_boundaries(text: str) -> List[str]:
    pieces = re.split(
        r"(?:\s*[;•|]\s+|(?<=:)\s+(?=[A-Z0-9])|(?<=,)\s+(?=[A-Z0-9][^\s]*\b)|\s{3,})",
        text.strip(),
    )
    return [_normalize_inline_whitespace(piece) for piece in pieces if piece.strip()]


def _word_count(text: str) -> int:
    return len(text.split())


def _normalize_inline_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _truncate_text_to_limits(text: str, *, max_words: int, max_chars: int) -> str:
    text = _normalize_inline_whitespace(text)
    if not text:
        return ""

    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words])

    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars].rstrip()
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated.rstrip()


def _body_fits_limits(*, context: str, body: str) -> bool:
    body = _normalize_inline_whitespace(body)
    if not body:
        return False
    composed = _compose_chunk_text(context=context, body=body)
    return _word_count(composed) <= MAX_WORDS and len(composed) <= MAX_CHARS


def _bounded_context(context: str) -> str:
    context = _normalize_inline_whitespace(context)
    if not context:
        return ""

    max_context_words = min(max(8, MAX_WORDS // 4), max(1, MAX_WORDS - 1))
    max_context_chars = min(max(128, MAX_CHARS // 3), max(1, MAX_CHARS - 2))
    return _truncate_text_to_limits(context, max_words=max_context_words, max_chars=max_context_chars)


def _available_body_word_budget(context: str) -> int:
    return max(1, MAX_WORDS - _word_count(context))


def _available_body_char_budget(context: str) -> int:
    separator = 1 if context else 0
    return max(1, MAX_CHARS - len(context) - separator)


def _split_word_windows(text: str, *, context: str) -> List[str]:
    words = text.split()
    if not words:
        return []

    max_words = _available_body_word_budget(context)
    max_chars = _available_body_char_budget(context)
    windows: List[str] = []
    current: List[str] = []

    for word in words:
        candidate_words = current + [word]
        candidate = " ".join(candidate_words)
        if current and (len(candidate_words) > max_words or len(candidate) > max_chars):
            windows.append(" ".join(current))
            current = [word]
            continue
        current = candidate_words

    if current:
        windows.append(" ".join(current))
    return [_normalize_inline_whitespace(window) for window in windows if window.strip()]


def _split_char_windows(text: str, *, context: str) -> List[str]:
    text = _normalize_inline_whitespace(text)
    if not text:
        return []

    max_chars = _available_body_char_budget(context)
    if max_chars <= 0:
        return []

    windows: List[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= max_chars:
            windows.append(remaining)
            break

        split_at = remaining.rfind(" ", 0, max_chars + 1)
        if split_at <= 0:
            split_at = max_chars
        window = remaining[:split_at].strip()
        if window:
            windows.append(window)
        remaining = remaining[split_at:].strip()

    return [window for window in windows if window]


def _looks_low_signal(text: str) -> bool:
    text = _normalize_inline_whitespace(text)
    if not text:
        return True

    words = text.split()
    if not words:
        return True

    alpha_chars = sum(char.isalpha() for char in text)
    non_space_chars = sum(not char.isspace() for char in text)
    alpha_ratio = (alpha_chars / non_space_chars) if non_space_chars else 0.0
    sentence_markers = len(re.findall(r"[.!?]", text))
    long_tokens = sum(len(word) > 40 for word in words)
    unique_word_ratio = len({word.lower() for word in words}) / len(words)

    if len(words) >= 80 and sentence_markers == 0:
        return True
    if len(words) >= 120 and alpha_ratio < 0.55:
        return True
    if len(words) >= 120 and unique_word_ratio < 0.2:
        return True
    if long_tokens >= 8:
        return True
    return False


def _emit_bounded_chunks(*, body: str, context: str, output: List[str]) -> None:
    body = _normalize_inline_whitespace(body)
    if not body:
        return

    context = _bounded_context(context)

    if _body_fits_limits(context=context, body=body):
        output.append(_compose_chunk_text(context=context, body=body))
        return

    if _looks_low_signal(body) and (_word_count(body) > MAX_WORDS or len(body) > MAX_CHARS):
        return

    for splitter in (_split_sentences, _split_simple_boundaries):
        pieces = splitter(body)
        if len(pieces) <= 1:
            continue

        current: List[str] = []
        for piece in pieces:
            candidate = _normalize_inline_whitespace(" ".join([*current, piece]))
            if current and not _body_fits_limits(context=context, body=candidate):
                _emit_bounded_chunks(body=" ".join(current), context=context, output=output)
                current = [piece]
            else:
                current.append(piece)
        if current:
            _emit_bounded_chunks(body=" ".join(current), context=context, output=output)
        return

    word_windows = _split_word_windows(body, context=context)
    if len(word_windows) > 1:
        for window in word_windows:
            if _body_fits_limits(context=context, body=window):
                output.append(_compose_chunk_text(context=context, body=window))
            else:
                for char_window in _split_char_windows(window, context=context):
                    if _body_fits_limits(context=context, body=char_window):
                        output.append(_compose_chunk_text(context=context, body=char_window))
        return

    for char_window in _split_char_windows(body, context=context):
        if _body_fits_limits(context=context, body=char_window):
            output.append(_compose_chunk_text(context=context, body=char_window))


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
        text = _normalize_inline_whitespace(text)
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
    context = _normalize_inline_whitespace(context)
    body = _normalize_inline_whitespace(body)
    if context:
        return f"{context} {body}".strip()
    return body.strip()


def chunk_markdown(markdown: str) -> List[str]:
    blocks = _parse_body_blocks(markdown)

    chunks: List[str] = []
    current: List[str] = []
    current_words = 0
    current_context: Optional[str] = None

    def flush_current() -> None:
        nonlocal current, current_words, current_context
        if current:
            _emit_bounded_chunks(body=" ".join(current), context=current_context or "", output=chunks)
        current = []
        current_words = 0
        current_context = None

    for block in blocks:
        if _looks_low_signal(block.text) and (block.words > MAX_WORDS or len(block.text) > MAX_CHARS):
            flush_current()
            continue

        if block.words > MAX_WORDS or len(_compose_chunk_text(context=block.context, body=block.text)) > MAX_CHARS:
            flush_current()
            _emit_bounded_chunks(body=block.text, context=block.context, output=chunks)
            continue

        if current and block.context != current_context:
            flush_current()

        next_body = " ".join([*current, block.text])
        if current and not _body_fits_limits(context=current_context or "", body=next_body):
            flush_current()

        if not current:
            current_context = block.context

        current.append(block.text)
        current_words += block.words

        if current_words >= TARGET_WORDS:
            flush_current()

    flush_current()
    return chunks
