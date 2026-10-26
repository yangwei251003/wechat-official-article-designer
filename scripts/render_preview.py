from __future__ import annotations

import argparse
import html
from pathlib import Path

from common import SKILL_DIR, parse_fragment, read_text, write_text


def render_preview(fragment: str, *, title: str, style_summary: str) -> str:
    parsed = parse_fragment(fragment)
    risky = [
        src for src in parsed.images
        if not src.lower().startswith(("https://mmbiz.qpic.cn/", "https://mmbiz.qlogo.cn/"))
    ]
    warning = (
        "图片均为微信CDN地址，可直接复制。"
        if not risky
        else f"检测到 {len(risky)} 张本地或非微信CDN图片；导入草稿时将先上传转存，手工复制后必须逐张确认。"
    )
    shell = read_text(SKILL_DIR / "assets" / "preview-shell.html")
    return (
        shell.replace("{{TITLE}}", html.escape(title))
        .replace("{{STYLE_SUMMARY}}", html.escape(style_summary))
        .replace("{{ASSET_WARNING}}", html.escape(warning))
        .replace("{{ARTICLE_HTML}}", fragment)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="把微信正文片段装入可切换视口和浅深色的本地预览壳")
    parser.add_argument("fragment", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--style-summary", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    write_text(args.output, render_preview(read_text(args.fragment), title=args.title, style_summary=args.style_summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
