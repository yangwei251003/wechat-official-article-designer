from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_resolve(path: Path, root: Path, *, must_exist: bool = True) -> Path:
    """Resolve a user-controlled path and require it to remain inside root."""
    root = root.resolve()
    resolved = path.resolve(strict=must_exist)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"路径超出允许目录：{path}") from exc
    return resolved


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def slugify(value: str) -> str:
    value = re.sub(r"[#*_`~<>\[\]{}()（）《》:：/\\]+", " ", value.strip().lower())
    value = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value, flags=re.UNICODE)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        value = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    return value[:48]


def strip_markdown_inline(value: str) -> str:
    value = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"(\*\*|__|\*|_|~~)", "", value)
    return html.unescape(value).strip()


class SourceHTMLParser(HTMLParser):
    BLOCK_TYPES = {"p": "paragraph", "blockquote": "quote", "li": "list", **{f"h{i}": "heading" for i in range(1, 7)}}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict[str, str]] = []
        self.active_tag: str | None = None
        self.buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {key.lower(): value or "" for key, value in attrs}
        if tag == "img":
            self._flush()
            self.blocks.append({"type": "image", "src": attr_map.get("src", ""), "alt": attr_map.get("alt", "")})
        elif tag in self.BLOCK_TYPES and self.active_tag is None:
            self.active_tag = tag

    def handle_data(self, data: str) -> None:
        if self.active_tag:
            self.buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.active_tag == tag.lower():
            self._flush()

    def _flush(self) -> None:
        if self.active_tag:
            text = re.sub(r"\s+", " ", "".join(self.buffer)).strip()
            if text:
                kind = self.BLOCK_TYPES[self.active_tag]
                block = {"type": kind, "text": text}
                if kind == "heading":
                    block["level"] = self.active_tag[1:]
                self.blocks.append(block)
        self.active_tag = None
        self.buffer.clear()


def html_blocks(source: str) -> list[dict[str, str]]:
    parser = SourceHTMLParser()
    parser.feed(source)
    parser._flush()
    return parser.blocks


def markdown_blocks(source: str) -> list[dict[str, str]]:
    if re.search(r"<(?:p|h[1-6]|blockquote|li|img)\b", source, re.I):
        parsed = html_blocks(source)
        if parsed:
            return parsed
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                lines = lines[index + 1 :]
                break
    blocks: list[dict[str, str]] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            text = strip_markdown_inline("\n".join(paragraph))
            if text:
                blocks.append({"type": "paragraph", "text": text})
            paragraph.clear()

    for line in lines:
        raw = line.rstrip()
        if not raw.strip():
            flush()
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", raw)
        if heading:
            flush()
            blocks.append({"type": "heading", "text": strip_markdown_inline(heading.group(2)), "level": str(len(heading.group(1)))})
            continue
        image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", raw.strip())
        if image:
            flush()
            blocks.append({"type": "image", "alt": image.group(1), "src": image.group(2)})
            continue
        quote = re.match(r"^>\s?(.*)$", raw)
        if quote:
            flush()
            blocks.append({"type": "quote", "text": strip_markdown_inline(quote.group(1))})
            continue
        item = re.match(r"^(?:[-*+]\s+|\d+[.)、]\s*)(.+)$", raw.strip())
        if item:
            flush()
            blocks.append({"type": "list", "text": strip_markdown_inline(item.group(1))})
            continue
        paragraph.append(raw.strip())
    flush()
    return blocks


def extract_title(source: str, blocks: list[dict[str, str]]) -> str:
    for block in blocks:
        if block["type"] == "heading" and block.get("level") == "1":
            return block["text"]
    for block in blocks:
        if block.get("text"):
            return block["text"][:60]
    return "未命名文章"


def source_text_blocks(source: str) -> list[str]:
    return [b["text"] for b in markdown_blocks(source) if b["type"] in {"heading", "paragraph", "quote", "list"} and b.get("text")]


def normalize_visible(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"\s+", "", value)
    return value


class FragmentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.images: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k.lower(): v or "" for k, v in attrs}
        self.tags.append((tag.lower(), attr_map))
        if tag.lower() in {"script", "style"}:
            self._skip += 1
        if tag.lower() == "img":
            self.images.append(attr_map.get("src", ""))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.text.append(data)


def parse_fragment(fragment: str) -> FragmentParser:
    parser = FragmentParser()
    parser.feed(fragment)
    return parser


def is_wechat_url(src: str) -> bool:
    return bool(re.match(r"^https://(?:mmbiz\.qpic\.cn|mmbiz\.qlogo\.cn)/", src, re.I))
