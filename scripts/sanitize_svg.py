from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from common import read_text, write_text

DANGEROUS_TAGS = {"script", "foreignObject", "iframe", "object", "embed"}
URL_ATTRS = {"href", "{http://www.w3.org/1999/xlink}href", "src"}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def sanitize_svg_text(source: str, *, max_elements: int = 5000) -> dict[str, Any]:
    if "<!DOCTYPE" in source.upper() or "<!ENTITY" in source.upper():
        raise ValueError("SVG包含DTD或实体声明，已拒绝")
    root = ET.fromstring(source)
    if _local(root.tag) != "svg":
        raise ValueError("根元素不是svg")
    removed: list[str] = []
    count = 0
    for parent in list(root.iter()):
        for child in list(parent):
            count += 1
            if count > max_elements:
                raise ValueError("SVG元素数量超过安全上限")
            if _local(child.tag) in DANGEROUS_TAGS:
                removed.append(_local(child.tag))
                parent.remove(child)
        for key in list(parent.attrib):
            lower = _local(key).lower()
            value = parent.attrib[key].strip()
            if lower.startswith("on"):
                removed.append(lower)
                del parent.attrib[key]
            elif key in URL_ATTRS or lower in {"href", "src"}:
                if re.match(r"^(?:https?:|//|javascript:|data:text/html)", value, re.I):
                    removed.append("external-url")
                    del parent.attrib[key]
            elif "url(" in value.lower() and not re.search(r"url\(\s*#", value, re.I):
                removed.append("external-css-url")
                del parent.attrib[key]
    return {"svg": ET.tostring(root, encoding="unicode"), "removed": sorted(set(removed)), "elements": count + 1}


def main() -> int:
    parser = argparse.ArgumentParser(description="移除SVG脚本、事件、外链和危险嵌入")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = sanitize_svg_text(read_text(args.input))
    write_text(args.output, result["svg"] + "\n")
    print(", ".join(result["removed"]) or "clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
