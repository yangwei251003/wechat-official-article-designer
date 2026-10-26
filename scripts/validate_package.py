from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import (
    normalize_visible,
    parse_fragment,
    read_json,
    read_text,
    safe_resolve,
    source_text_blocks,
    write_json,
)

ALLOWED_TAGS = {"section", "p", "span", "strong", "em", "br", "img", "table", "thead", "tbody", "tr", "th", "td", "blockquote", "a"}
BANNED_TAGS = {"script", "style", "link", "iframe", "video", "audio", "canvas", "svg", "form", "input", "button", "object", "embed"}
BANNED_STYLE_PATTERNS = {
    "Flex布局": r"display\s*:\s*(?:inline-)?flex",
    "Grid布局": r"display\s*:\s*(?:inline-)?grid",
    "定位": r"position\s*:",
    "浮动": r"float\s*:",
    "变换": r"transform\s*:",
    "滤镜": r"(?:backdrop-)?filter\s*:",
    "动画": r"(?:animation|transition)\s*:",
    "裁切/遮罩": r"(?:clip-path|mask(?:-image)?)\s*:",
    "CSS背景图": r"background(?:-image)?\s*:[^;]*(?:url\(|gradient\()",
    "CSS变量或计算": r"(?:var|calc)\s*\(",
    "视口单位": r"(?:^|:)\s*[^;]*(?:\d|\.)+(?:vw|vh|vmin|vmax)\b",
    "负外边距": r"margin(?:-[a-z]+)?\s*:\s*-",
}


def parse_hex(value: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", value.strip())
    if not match:
        return None
    raw = match.group(1)
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def luminance(rgb: tuple[int, int, int]) -> float:
    values = []
    for channel in rgb:
        value = channel / 255
        values.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
    return 0.2126 * values[0] + 0.7152 * values[1] + 0.0722 * values[2]


def contrast(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def style_map(style: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for declaration in style.split(";"):
        if ":" in declaration:
            key, value = declaration.split(":", 1)
            result[key.strip().lower()] = value.strip()
    return result


def validate(package_dir: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    required = ["source.md", "article-fragment.html", "preview.html", "article-package.json", "design-brief.md", "design-brief.json", "changes.md", "assets"]
    for name in required:
        if not (package_dir / name).exists():
            errors.append(f"缺少文章包文件：{name}")
    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings}

    source = read_text(package_dir / "source.md")
    fragment = read_text(package_dir / "article-fragment.html")
    package = read_json(package_dir / "article-package.json")
    changes = read_text(package_dir / "changes.md").strip()
    parsed = parse_fragment(fragment)

    tags = [tag for tag, _ in parsed.tags]
    for tag in sorted(set(tags)):
        if tag in BANNED_TAGS:
            errors.append(f"正文包含禁用标签：<{tag}>")
        elif tag not in ALLOWED_TAGS:
            errors.append(f"正文包含未列入安全白名单的标签：<{tag}>")
    if not tags or "section" not in tags:
        errors.append("正文缺少section根/分区结构")

    for tag, attrs in parsed.tags:
        if "class" in attrs:
            warnings.append(f"<{tag}> 使用class；微信正文不得依赖class样式")
        for event in [key for key in attrs if key.startswith("on")]:
            errors.append(f"<{tag}> 包含事件属性：{event}")
        style = attrs.get("style", "")
        for label, pattern in BANNED_STYLE_PATTERNS.items():
            if re.search(pattern, style, re.I):
                errors.append(f"<{tag}> 使用禁用样式（{label}）：{style}")
        declarations = style_map(style)
        fg = parse_hex(declarations.get("color", ""))
        bg = parse_hex(declarations.get("background-color", ""))
        if fg and bg and contrast(fg, bg) < 4.5:
            warnings.append(f"<{tag}> 前景/背景对比度仅 {contrast(fg, bg):.2f}:1")

    source_blocks = source_text_blocks(source)
    visible = normalize_visible("".join(parsed.text))
    cursor = 0
    for index, block in enumerate(source_blocks, 1):
        needle = normalize_visible(block)
        if not needle:
            continue
        found = visible.find(needle, cursor)
        if found < 0:
            errors.append(f"原文第{index}个文本块未按顺序完整出现：{block[:40]}")
        else:
            cursor = found + len(needle)
    if not changes:
        errors.append("changes.md 为空，无法审计结构改动")

    asset_entries = package.get("assets", [])
    by_path = {str(item.get("local_path", "")).replace("\\", "/"): item for item in asset_entries}
    for src in parsed.images:
        if not src:
            errors.append("存在空src图片")
            continue
        if src.startswith("data:") or src.startswith("file:"):
            errors.append(f"图片使用不可发布地址：{src[:60]}")
            continue
        if re.match(r"^https?://", src, re.I):
            if not re.match(r"^https://(?:mmbiz\.qpic\.cn|mmbiz\.qlogo\.cn)/", src, re.I):
                warnings.append(f"非微信CDN图片必须在发布前转存：{src[:100]}")
            continue
        relative = src.replace("\\", "/").lstrip("./")
        try:
            file_path = safe_resolve(package_dir / relative, package_dir)
        except (ValueError, FileNotFoundError):
            errors.append(f"本地图片路径不安全或不存在：{src}")
            continue
        if not file_path.exists():
            errors.append(f"本地图片不存在：{src}")
        if relative not in by_path:
            errors.append(f"正文图片未登记到article-package.json：{relative}")

    for asset in asset_entries:
        provider = str(asset.get("provider", "")).lower()
        local_path = str(asset.get("local_path", ""))
        try:
            resolved_asset = safe_resolve(package_dir / local_path, package_dir) if local_path else None
        except (ValueError, FileNotFoundError):
            errors.append(f"素材路径不安全或不存在：{asset.get('id', '<unknown>')}")
            resolved_asset = None
        if not local_path or resolved_asset is None or not resolved_asset.exists():
            errors.append(f"素材文件不存在或路径为空：{asset.get('id', '<unknown>')}")
        if provider not in {"generated", "original", "user-provided"}:
            for key in ("creator", "source_url", "license", "license_url", "accessed_at"):
                if not asset.get(key):
                    errors.append(f"第三方素材 {asset.get('id', '<unknown>')} 缺少 {key}")
        elif not asset.get("license"):
            warnings.append(f"原创/用户素材 {asset.get('id', '<unknown>')} 未写明权利说明")

    design = package.get("design", {})
    palette = design.get("palette", [])
    if len(palette) > 3:
        errors.append(f"主色板超过三种颜色：{palette}")
    if package.get("schema_version") != "1.0":
        errors.append("article-package.json schema_version 必须为 1.0")
    return {"ok": not errors, "errors": errors, "warnings": list(dict.fromkeys(warnings)), "stats": {"source_blocks": len(source_blocks), "tags": len(tags), "images": len(parsed.images), "assets": len(asset_entries)}}


def main() -> int:
    parser = argparse.ArgumentParser(description="校验公众号文章包的内容完整性、微信兼容性和素材许可")
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path, help="可选：保存兼容检查JSON")
    args = parser.parse_args()
    result = validate(args.package_dir.resolve())
    if args.output:
        payload = {"schema_version": "2.0", **result, "wechat_client_final_preview_required": True}
        write_json(args.output, payload)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("PASS" if result["ok"] else "FAIL")
        for issue in result["errors"]:
            print(f"ERROR: {issue}")
        for issue in result["warnings"]:
            print(f"WARN: {issue}")
        if result.get("stats"):
            print("STATS: " + json.dumps(result["stats"], ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
