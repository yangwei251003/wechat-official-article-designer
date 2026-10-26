from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from common import read_text, write_text

ALLOWED_TAGS = {"section", "p", "span", "strong", "em", "br", "img", "table", "tbody", "thead", "tr", "td", "th", "blockquote", "a"}
DROP_TAGS = {"script", "style", "link", "iframe", "video", "audio", "canvas", "svg", "form", "input", "button", "object", "embed", "meta"}
ALLOWED_ATTRS = {"style", "src", "href", "alt", "title", "width", "height", "role", "colspan", "rowspan"}
BANNED_CSS = re.compile(r"(?:display\s*:\s*(?:inline-)?(?:flex|grid)|position\s*:|float\s*:|transform\s*:|(?:backdrop-)?filter\s*:|animation\s*:|transition\s*:|clip-path\s*:|mask(?:-image)?\s*:|background(?:-image)?\s*:[^;]*(?:url\(|gradient\()|(?:var|calc)\s*\(|(?:^|:)\s*[^;]*(?:\d|\.)+(?:vw|vh|vmin|vmax)\b|margin(?:-[a-z]+)?\s*:\s*-)", re.I)
SAFE_URL = re.compile(r"^(?:https://|mailto:|#|assets/|\./assets/)", re.I)


def _parse_css_rules(css: str) -> list[tuple[str, str]]:
    rules: list[tuple[str, str]] = []
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for selector_group, declarations in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        clean = _sanitize_style(declarations)
        for selector in selector_group.split(","):
            selector = selector.strip()
            if re.fullmatch(r"(?:[a-zA-Z][\w-]*|\.[\w-]+|#[\w-]+)", selector) and clean:
                rules.append((selector, clean))
    return rules


def _sanitize_style(style: str) -> str:
    safe: list[str] = []
    for declaration in style.split(";"):
        declaration = declaration.strip()
        if not declaration or ":" not in declaration or BANNED_CSS.search(declaration):
            continue
        prop, value = declaration.split(":", 1)
        if re.fullmatch(r"[a-zA-Z-]+", prop.strip()) and "expression(" not in value.lower() and "javascript:" not in value.lower():
            safe.append(f"{prop.strip().lower()}:{value.strip()}")
    return ";".join(safe)


def sanitize_and_inline(source: str) -> dict[str, Any]:
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise RuntimeError("需要beautifulsoup4以执行CSS内联与HTML清理") from exc
    soup = BeautifulSoup(source, "html.parser")
    css = "\n".join(tag.get_text(" ") for tag in soup.find_all("style"))
    rules = _parse_css_rules(css)
    removed: list[str] = []
    for selector, declarations in rules:
        try:
            nodes = soup.select(selector)
        except Exception:
            continue
        for node in nodes:
            existing = _sanitize_style(str(node.get("style", "")))
            node["style"] = ";".join(part for part in (declarations, existing) if part)
    for tag in list(soup.find_all(DROP_TAGS)):
        removed.append(tag.name)
        tag.decompose()
    for tag in list(soup.find_all(True)):
        if tag.name not in ALLOWED_TAGS:
            removed.append(tag.name)
            tag.unwrap()
            continue
        attrs = dict(tag.attrs)
        for key in list(attrs):
            lower = key.lower()
            if lower.startswith("on") or lower not in ALLOWED_ATTRS:
                tag.attrs.pop(key, None)
        if tag.has_attr("style"):
            clean = _sanitize_style(str(tag["style"]))
            if clean:
                tag["style"] = clean
            else:
                tag.attrs.pop("style", None)
        for key in ("src", "href"):
            if tag.has_attr(key) and not SAFE_URL.match(str(tag[key])):
                tag.attrs.pop(key, None)
                removed.append(f"unsafe-{key}")
    return {"html": str(soup), "removed": sorted(set(removed)), "css_rules_inlined": len(rules)}


def main() -> int:
    parser = argparse.ArgumentParser(description="内联简单CSS并清理为微信安全HTML")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = sanitize_and_inline(read_text(args.input))
    write_text(args.output, result["html"] + "\n")
    if args.report:
        write_text(args.report, json.dumps({k: v for k, v in result.items() if k != "html"}, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
