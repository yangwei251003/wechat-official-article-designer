from __future__ import annotations

import argparse
import html
from datetime import date
from pathlib import Path
from typing import Any

from article_schema import scaffold_from_source
from common import (
    SKILL_DIR,
    extract_title,
    markdown_blocks,
    now_iso,
    parse_fragment,
    read_text,
    slugify,
    write_json,
    write_text,
)
from design_brief import build_design_brief
from license_report import build_report, markdown_report

THEMES = {
    "knowledge": {"track": "知识科普", "concept": "清晰的知识标本", "palette": ["#263A39", "#5E827D", "#EEF4F1"]},
    "business": {"track": "商业科技", "concept": "克制的数据发布现场", "palette": ["#26364A", "#55779A", "#EEF2F6"]},
    "lifestyle": {"track": "生活美学", "concept": "有纸张温度的慢读杂志", "palette": ["#4E493F", "#9A7658", "#F5F1E8"]},
    "profile": {"track": "人物叙事", "concept": "安静而有张力的人物特写", "palette": ["#343332", "#846B55", "#F3F0EB"]},
    "tutorial": {"track": "教程清单", "concept": "轻量清楚的行动手册", "palette": ["#304B5B", "#D17A52", "#EEF3F4"]},
}


def detect_theme(text: str) -> dict[str, Any]:
    tests = [
        ("tutorial", ["步骤", "方法", "教程", "清单", "如何", "第一步"]),
        ("business", ["商业", "公司", "市场", "增长", "科技", "产品", "数据", "人工智能", "ai"]),
        ("lifestyle", ["生活", "旅行", "咖啡", "美食", "家", "季节", "花", "日常"]),
        ("profile", ["人物", "采访", "他说", "她说", "回忆", "故事"]),
    ]
    lowered = text.lower()
    for key, words in tests:
        if any(word in lowered for word in words):
            return THEMES[key]
    return THEMES["knowledge"]


def baseline_fragment(blocks: list[dict[str, str]], theme: dict) -> str:
    ink, accent, paper = theme["palette"]
    out = [
        f'<section style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',\'PingFang SC\',\'Microsoft YaHei\',Arial,sans-serif;color:{ink};font-size:15px;line-height:1.8;letter-spacing:.03em;background-color:{paper};padding:22px 16px;">'
    ]
    list_index = 0
    for block in blocks:
        kind = block["type"]
        if kind == "heading":
            size = "22px" if block.get("level") == "1" else "18px"
            margin = "8px 0 28px" if block.get("level") == "1" else "34px 0 16px"
            border = "" if block.get("level") == "1" else f"border-left:3px solid {accent};padding-left:12px;"
            out.append(f'<p style="margin:{margin};{border}color:{ink};font-size:{size};font-weight:700;line-height:1.45;">{html.escape(block["text"])}</p>')
        elif kind == "paragraph":
            out.append(f'<p style="margin:0 0 18px;color:{ink};font-size:15px;line-height:1.8;">{html.escape(block["text"])}</p>')
        elif kind == "quote":
            out.append(f'<blockquote style="margin:24px 0;padding:4px 0 4px 16px;border-left:2px solid {accent};color:{ink};"><p style="margin:0;font-size:14px;line-height:1.8;">{html.escape(block["text"])}</p></blockquote>')
        elif kind == "list":
            list_index += 1
            out.append(f'<p style="margin:0 0 14px;color:{ink};font-size:15px;line-height:1.75;"><span style="display:inline-block;margin-right:9px;color:{accent};font-weight:700;">{list_index:02d}</span>{html.escape(block["text"])}</p>')
        elif kind == "image":
            out.append(f'<section style="margin:28px 0;"><img src="{html.escape(block["src"], quote=True)}" alt="{html.escape(block.get("alt", ""), quote=True)}" style="display:block;width:100%;height:auto;margin:0;" /></section>')
    out.append("</section>")
    return "\n".join(out) + "\n"


def make_output_dir(root: Path, slug: str, explicit: Path | None) -> Path:
    if explicit:
        explicit.mkdir(parents=True, exist_ok=True)
        return explicit.resolve()
    base = root.resolve() / "wechat-output" / f"{date.today().isoformat()}-{slug}"
    candidate = base
    index = 2
    while candidate.exists():
        candidate = Path(f"{base}-{index}")
        index += 1
    candidate.mkdir(parents=True)
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="构建微信公众号文章包和可复制预览页")
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 Markdown/TXT源稿")
    parser.add_argument("--fragment", type=Path, help="已设计的微信正文HTML片段")
    parser.add_argument("--changes", type=Path, help="自定义fragment对应的结构改动清单Markdown")
    parser.add_argument("--output-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--title")
    parser.add_argument("--author", default="")
    parser.add_argument("--digest", default="")
    args = parser.parse_args()
    if args.fragment and not args.changes:
        parser.error("使用 --fragment 时必须同时提供 --changes，避免结构改动失去审计记录")

    source = read_text(args.input)
    blocks = markdown_blocks(source)
    title = args.title or extract_title(source, blocks)
    slug = slugify(title)
    theme = detect_theme(source)
    output = make_output_dir(args.output_root, slug, args.output_dir)
    (output / "assets").mkdir(exist_ok=True)

    write_text(output / "source.md", source)
    fragment = read_text(args.fragment) if args.fragment else baseline_fragment(blocks, theme)
    write_text(output / "article-fragment.html", fragment)

    parsed = parse_fragment(fragment)
    risky = [src for src in parsed.images if not src.lower().startswith("https://mmbiz.qpic.cn/") and not src.lower().startswith("https://mmbiz.qlogo.cn/")]
    warning = "图片均为微信CDN地址，可直接复制。" if not risky else f"检测到 {len(risky)} 张本地或非微信CDN图片；复制后必须确认微信已完成转存，正式发布建议使用草稿API。"

    common_prompt = f"为《{title}》创作{theme['concept']}视觉，{theme['track']}编辑设计，使用{'、'.join(theme['palette'])}，画面不要生成文字，保留标题安全区，原创且不模仿具体艺术家"
    brief_assets = [
        {"id": "cover-main", "role": "cover", "canvas": {"width": 900, "height": 383}, "format": "PNG/JPG", "composition": "宽幅主视觉，主体偏一侧，另一侧保留标题区", "text_content": title, "text_safe_area": "中央70%，距离四边至少8%", "subject_safe_area": "缩略裁切后主体仍完整", "prompt": common_prompt + "，2.35:1宽幅封面", "palette": theme["palette"], "filename": "cover-main.jpg"},
        {"id": "guide-wide", "role": "inline", "canvas": {"width": 900, "height": 500}, "format": "PNG/JPG", "composition": "横向叙事或概念解释画面，视觉焦点单一", "text_content": "", "text_safe_area": "四周保留8%呼吸区", "subject_safe_area": "中心60%", "prompt": common_prompt + "，正文横图，无文字", "palette": theme["palette"], "filename": "guide-wide.jpg"},
        {"id": "cover-square", "role": "cover-crop", "canvas": {"width": 900, "height": 900}, "format": "PNG/JPG", "composition": "方形主体居中，缩小到200px仍清楚", "text_content": "", "text_safe_area": "中心70%", "subject_safe_area": "中心60%", "prompt": common_prompt + "，方形裁切版本，无文字", "palette": theme["palette"], "filename": "cover-square.jpg"},
    ]
    brief = build_design_brief(theme["track"], title, palette=theme["palette"])
    brief.update({"concept": theme["concept"], "palette": theme["palette"], "template_keywords": [theme["track"], theme["concept"], "公众号封面"], "asset_direction": "AI原创优先；实景需求使用合规图库；画面不要生成文字，标题在可画或Figma中后置。", "assets": brief_assets})
    write_json(output / "design-brief.json", brief)
    brief_md = f"# 外部设计任务包\n\n- 文章：{title}\n- 赛道：{theme['track']}\n- 概念：{theme['concept']}\n- 配色：{' / '.join(theme['palette'])}\n- 可画检索词：{'、'.join(brief['template_keywords'])}\n- 原则：画面主体置于安全区；AI图不要生成文字；导出后按JSON文件名保存到 assets。\n"
    write_text(output / "design-brief.md", brief_md)
    if args.changes:
        write_text(output / "changes.md", read_text(args.changes))
    else:
        write_text(output / "changes.md", "# 结构改动清单\n\n无结构性改动。基线脚本只映射原有标题、段落、引用、列表和图片。\n")

    package_assets: list[dict[str, Any]] = []
    package: dict[str, Any] = {
        "schema_version": "1.0",
        "title": title,
        "slug": slug,
        "created_at": now_iso(),
        "source_file": "source.md",
        "fragment_file": "article-fragment.html",
        "preview_file": "preview.html",
        "design": {"mode": ("custom-unverified" if args.fragment else "baseline-draft"), "track": theme["track"], "concept": theme["concept"], "palette": theme["palette"], "components": ["章节标题", "正文", "引用", "编号清单"]},
        "editing_policy": {"structural_edits_allowed": True, "immutable": ["事实", "观点", "数字", "人名", "引用", "因果", "叙述含义与顺序"]},
        "assets": package_assets,
        "publishing": {"status": "not_started", "cover_asset_id": "cover-main", "author": args.author, "digest": args.digest, "need_open_comment": 1, "only_fans_can_comment": 0},
        "article_schema_version": "2.0",
        "article_file": "article.json",
    }
    write_json(output / "article-package.json", package)

    article = scaffold_from_source(source, title=title)
    article["metadata"]["author"] = args.author
    article["metadata"]["summary"] = args.digest
    article["design"]["mode"] = "baseline"
    article["design"]["direction"] = theme["concept"]
    article["design"]["tokens"]["palette"] = theme["palette"]
    article["design"]["components"] = package["design"]["components"]
    write_json(output / "article.json", article)

    shell = read_text(SKILL_DIR / "assets" / "preview-shell.html")
    preview = shell.replace("{{TITLE}}", html.escape(title)).replace("{{STYLE_SUMMARY}}", html.escape(f"{theme['concept']} · {theme['track']} · {' / '.join(theme['palette'])}")).replace("{{ASSET_WARNING}}", html.escape(warning)).replace("{{ARTICLE_HTML}}", fragment)
    write_text(output / "preview.html", preview)
    rights = build_report(package_assets)
    write_json(output / "license-report.json", rights)
    write_text(output / "license-report.md", markdown_report(rights))
    from validate_package import validate

    validation = validate(output)
    compatibility = {"schema_version": "1.0", "ok": validation["ok"], "errors": validation["errors"], "warnings": validation["warnings"], "stats": validation.get("stats", {}), "wechat_client_final_preview_required": True}
    write_json(output / "compatibility-report.json", compatibility)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
