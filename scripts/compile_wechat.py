from __future__ import annotations

import argparse
import html
from pathlib import Path
from typing import Any

from article_schema import validate_article
from common import read_json, write_json, write_text
from sanitize_html import sanitize_and_inline


def _styles(article: dict[str, Any]) -> dict[str, str]:
    tokens = article["design"]["tokens"]
    palette = list(tokens.get("palette") or ["#263A39", "#5E827D", "#EEF4F1"])
    while len(palette) < 3:
        palette.append("#EEF4F1")
    return {"ink": palette[0], "accent": palette[1], "paper": palette[2], "font": tokens.get("font_stack", "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',Arial,sans-serif"), "body": tokens.get("body_size", "15px"), "line": str(tokens.get("line_height", 1.8)), "radius": tokens.get("radius", "8px")}


def _node_html(node: dict[str, Any], style: dict[str, str], degraded: list[str]) -> str:
    kind = node.get("type")
    if kind == "text":
        text = html.escape(str(node.get("text", "")))
        component = node.get("component")
        if component == "quote":
            return f'<blockquote style="margin:22px 0;padding:4px 0 4px 16px;border-left:2px solid {style["accent"]};color:{style["ink"]};"><p style="margin:0;font-size:14px;line-height:{style["line"]};">{text}</p></blockquote>'
        if component == "list":
            return f'<p style="margin:0 0 14px;color:{style["ink"]};font-size:{style["body"]};line-height:{style["line"]};"><span style="display:inline-block;margin-right:8px;color:{style["accent"]};font-weight:700;">•</span>{text}</p>'
        return f'<p style="margin:0 0 18px;color:{style["ink"]};font-size:{style["body"]};line-height:{style["line"]};">{text}</p>'
    if kind == "image":
        return f'<section style="margin:26px 0;"><img src="{html.escape(str(node.get("src", "")), quote=True)}" alt="{html.escape(str(node.get("alt", "")), quote=True)}" style="display:block;width:100%;height:auto;margin:0;" /></section>'
    if kind in {"chart", "video", "component"}:
        fallback = node.get("fallback") or {}
        if fallback.get("type") == "image" and fallback.get("src"):
            degraded.append(str(node.get("id", "")))
            return f'<section style="margin:26px 0;"><img src="{html.escape(str(fallback["src"]), quote=True)}" alt="{html.escape(str(fallback.get("alt", kind)), quote=True)}" style="display:block;width:100%;height:auto;margin:0;" /></section>'
        degraded.append(str(node.get("id", "")))
        return f'<p style="margin:18px 0;padding:12px;border:1px solid {style["accent"]};color:{style["ink"]};font-size:13px;line-height:1.7;">{html.escape(str(fallback.get("text") or f"{kind}内容需在发布前提供静态降级版本"))}</p>'
    if kind == "table":
        rows = node.get("rows") or []
        body = []
        for row in rows:
            cells = "".join(f'<td style="padding:8px;border:1px solid {style["accent"]};color:{style["ink"]};font-size:13px;vertical-align:top;">{html.escape(str(cell))}</td>' for cell in row)
            body.append(f"<tr>{cells}</tr>")
        return f'<table style="width:100%;border-collapse:collapse;margin:22px 0;" role="presentation"><tbody>{"".join(body)}</tbody></table>'
    return ""


def _markdown(article: dict[str, Any]) -> str:
    lines = [f"# {article['metadata']['title']}", ""]
    for section in article["content"]["sections"]:
        if section.get("title"):
            lines.extend([f"## {section['title']}", ""])
        for node in section.get("nodes", []):
            if node.get("type") == "text":
                prefix = "> " if node.get("component") == "quote" else ""
                lines.extend([prefix + str(node.get("text", "")), ""])
            elif node.get("type") == "image":
                lines.extend([f"![{node.get('alt','')}]({node.get('src','')})", ""])
    return "\n".join(lines).rstrip() + "\n"


def compile_article(article: dict[str, Any]) -> dict[str, Any]:
    validation = validate_article(article)
    if not validation["ok"]:
        raise ValueError("Article Schema校验失败：" + "; ".join(validation["errors"]))
    style = _styles(article)
    degraded: list[str] = []
    parts = [f'<section style="font-family:{style["font"]};color:{style["ink"]};font-size:{style["body"]};line-height:{style["line"]};background-color:{style["paper"]};padding:20px 16px;">', f'<p style="margin:0 0 28px;color:{style["ink"]};font-size:23px;font-weight:700;line-height:1.45;">{html.escape(article["metadata"]["title"])}</p>']
    for section in article["content"]["sections"]:
        if section.get("title"):
            parts.append(f'<section style="margin:32px 0 18px;border-left:3px solid {style["accent"]};padding:2px 0 2px 12px;"><p style="margin:0;color:{style["ink"]};font-size:18px;font-weight:700;line-height:1.5;">{html.escape(section["title"])}</p></section>')
        parts.extend(_node_html(node, style, degraded) for node in section.get("nodes", []))
    parts.append("</section>")
    sanitized = sanitize_and_inline("\n".join(parts))
    compatibility = {"ok": True, "level": article["wechat"]["compatibility_level"], "degraded_nodes": degraded, "removed_items": sanitized["removed"], "warnings": (["复杂节点已使用静态降级；保留源规范便于后续修改"] if degraded else [])}
    return {"html": sanitized["html"] + "\n", "markdown": _markdown(article), "compatibility": compatibility}


def main() -> int:
    parser = argparse.ArgumentParser(description="把Article Schema 2.0编译为微信安全HTML、Markdown与兼容报告")
    parser.add_argument("article", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    result = compile_article(read_json(args.article))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_text(args.output_dir / "article-fragment.html", result["html"])
    write_text(args.output_dir / "article.md", result["markdown"])
    write_json(args.output_dir / "compatibility-report.json", result["compatibility"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
