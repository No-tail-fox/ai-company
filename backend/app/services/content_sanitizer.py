from __future__ import annotations

from dataclasses import dataclass
import html
from html.parser import HTMLParser
import re


ZERO_WIDTH_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")
UNSAFE_BLOCK_RE = re.compile(r"<(script|style|svg)\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL)
SPAN_FONT_RE = re.compile(r"</?(?:span|font)\b[^>]*>", re.IGNORECASE)
BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
PARAGRAPH_OPEN_RE = re.compile(r"<p\b[^>]*>", re.IGNORECASE)
PARAGRAPH_CLOSE_RE = re.compile(r"</p\s*>", re.IGNORECASE)
DIV_OPEN_RE = re.compile(r"<div\b[^>]*>", re.IGNORECASE)
DIV_CLOSE_RE = re.compile(r"</div\s*>", re.IGNORECASE)
IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
TABLE_RE = re.compile(r"<table\b[^>]*>.*?</table\s*>", re.IGNORECASE | re.DOTALL)
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
MARKDOWN_ESCAPED_WORD_RE = re.compile(r"\\([_])(?=[A-Za-z0-9])")
WHITESPACE_LINE_RE = re.compile(r"[ \t]+\n")
MANY_BLANK_LINES_RE = re.compile(r"\n{3,}")

MOJIBAKE_MARKERS = ("Ã", "Â", "â", "å", "æ", "ç", "è", "é", "ä", "ð", "ï", "\ufffd")


@dataclass(frozen=True)
class SanitizeResult:
    text: str
    changed: bool
    dirty_before: bool
    dirty_after: bool


def clean_text(value: str | None) -> str:
    text = _drop_invalid_unicode("" if value is None else str(value))
    text = ZERO_WIDTH_RE.sub("", text)
    text = _html_unescape_stable(text)
    text = _repair_mojibake(text)
    text = text.replace("\ufffd", "")
    return _compact_inline_whitespace(text).strip()


def clean_markdown(markdown: str | None) -> str:
    original = "" if markdown is None else str(markdown)
    cleaned = _drop_invalid_unicode(original)
    cleaned = ZERO_WIDTH_RE.sub("", cleaned)
    cleaned = _html_unescape_stable(cleaned)
    cleaned = _repair_mojibake(cleaned)
    cleaned = UNSAFE_BLOCK_RE.sub("", cleaned)
    cleaned = TABLE_RE.sub(lambda match: _html_table_to_markdown(match.group(0)), cleaned)
    cleaned = IMG_RE.sub(lambda match: _html_img_to_markdown(match.group(0)), cleaned)
    cleaned = BR_RE.sub("\n", cleaned)
    cleaned = PARAGRAPH_OPEN_RE.sub("", cleaned)
    cleaned = PARAGRAPH_CLOSE_RE.sub("\n\n", cleaned)
    cleaned = DIV_OPEN_RE.sub("", cleaned)
    cleaned = DIV_CLOSE_RE.sub("\n", cleaned)
    cleaned = SPAN_FONT_RE.sub("", cleaned)
    cleaned = re.sub(r"<!--.*?-->", "", cleaned, flags=re.DOTALL)
    cleaned = HTML_TAG_RE.sub("", cleaned)
    cleaned = MARKDOWN_ESCAPED_WORD_RE.sub(r"\1", cleaned)
    cleaned = cleaned.replace("\ufffd", "")
    cleaned = WHITESPACE_LINE_RE.sub("\n", cleaned)
    cleaned = MANY_BLANK_LINES_RE.sub("\n\n", cleaned)
    return cleaned.strip()


def sanitize_markdown(markdown: str | None) -> SanitizeResult:
    original = "" if markdown is None else str(markdown)
    cleaned = clean_markdown(original)
    return SanitizeResult(
        text=cleaned,
        changed=cleaned != original,
        dirty_before=is_dirty_markdown(original),
        dirty_after=is_dirty_markdown(cleaned),
    )


def is_dirty_markdown(markdown: str | None) -> bool:
    text = "" if markdown is None else str(markdown)
    return any(
        marker in text
        for marker in (
            "<span",
            "<font",
            "<script",
            "<style",
            "<svg",
            "<table",
            "<img",
            "&#x",
            "&nbsp;",
            "\u200b",
            "\u200c",
            "\u200d",
            "\ufeff",
            "\ufffd",
        )
    )


def _drop_invalid_unicode(value: str) -> str:
    return value.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")


def _html_unescape_stable(value: str) -> str:
    previous = value
    for _ in range(3):
        current = html.unescape(previous)
        if current == previous:
            return current
        previous = current
    return previous


def _compact_inline_whitespace(value: str) -> str:
    return re.sub(r"[ \t]{2,}", " ", value)


def _repair_mojibake(value: str) -> str:
    if not value or not any(marker in value for marker in MOJIBAKE_MARKERS):
        return value
    candidates = [value]
    for encoding in ("cp1252", "latin1"):
        try:
            candidates.append(value.encode(encoding).decode("utf-8"))
        except UnicodeError:
            continue
    recovered = _mixed_mojibake_candidate(value)
    if recovered:
        candidates.append(recovered)
    return max(candidates, key=_text_quality_score)


def _mixed_mojibake_candidate(value: str) -> str:
    raw = bytearray()
    for char in value:
        codepoint = ord(char)
        if codepoint <= 255:
            raw.append(codepoint)
            continue
        try:
            raw.extend(char.encode("cp1252"))
        except UnicodeError:
            return ""
    try:
        return bytes(raw).decode("utf-8")
    except UnicodeError:
        return ""


def _text_quality_score(value: str) -> int:
    cjk_count = sum(1 for char in value if "\u4e00" <= char <= "\u9fff")
    marker_count = sum(value.count(marker) for marker in MOJIBAKE_MARKERS)
    replacement_count = value.count("\ufffd") + value.count("?")
    control_count = sum(1 for char in value if ord(char) < 32 and char not in "\n\r\t")
    return (cjk_count * 8) - (marker_count * 5) - (replacement_count * 4) - (control_count * 6)


def _html_img_to_markdown(tag: str) -> str:
    attrs = _parse_attrs(tag)
    src = attrs.get("src", "").strip()
    if not src:
        return ""
    alt = clean_text(attrs.get("alt", "")).replace("[", "").replace("]", "")
    return f"![{alt}]({src})"


def _html_table_to_markdown(table_html: str) -> str:
    parser = _TableParser()
    parser.feed(table_html)
    rows = [[clean_text(cell) for cell in row] for row in parser.rows if any(clean_text(cell) for cell in row)]
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]
    header = normalized[0]
    separator = ["---"] * width
    body = normalized[1:]
    lines = [_markdown_table_row(header), _markdown_table_row(separator)]
    lines.extend(_markdown_table_row(row) for row in body)
    return "\n".join(lines)


def _markdown_table_row(cells: list[str]) -> str:
    safe_cells = [cell.replace("|", "\\|").replace("\n", " ").strip() for cell in cells]
    return f"| {' | '.join(safe_cells)} |"


def _parse_attrs(tag: str) -> dict[str, str]:
    parser = _AttrParser()
    parser.feed(tag)
    return parser.attrs


class _AttrParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.attrs: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del tag
        self.attrs = {name.lower(): value or "" for name, value in attrs}


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.lower() == "tr":
            self._current_row = []
        elif tag.lower() in {"td", "th"} and self._current_row is not None:
            self._current_cell = []
        elif tag.lower() == "br" and self._current_cell is not None:
            self._current_cell.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"td", "th"} and self._current_row is not None and self._current_cell is not None:
            self._current_row.append("".join(self._current_cell))
            self._current_cell = None
        elif tag.lower() == "tr" and self._current_row is not None:
            self.rows.append(self._current_row)
            self._current_row = None

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.append(data)
