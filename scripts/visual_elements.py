from __future__ import annotations

import argparse
import html
from pathlib import Path
from typing import Any

from common import now_iso, write_json, write_text

EMOJI_FAMILIES = [
    ("research", ["🔎", "🧪", "🧭"], ["研究", "观察", "实验", "假设", "证据", "学习"]),
    ("business", ["✳️", "📈", "⚡"], ["商业", "产品", "增长", "数据", "发布", "科技"]),
    ("story", ["✦", "🫧", "✉️"], ["人物", "故事", "生活", "旅行", "季节", "文化"]),
    ("care", ["🌱", "🤝", "☀️"], ["亲子", "儿童", "公益", "健康", "陪伴", "教育"]),
]


def choose_emojis(topic: str, *, limit: int = 3) -> list[str]:
    lowered = topic.lower()
    for _, emojis, keywords in EMOJI_FAMILIES:
        if any(keyword in lowered for keyword in keywords):
            return emojis[:limit]
    return ["✦", "●", "→"][:limit]


def imagegen_tasks(topic: str, palette: list[str]) -> list[dict[str, str]]:
    background, primary, accent = palette
    shared = (
        f"主题：{topic}。色彩关系：深色/中性色基底 {background}，主色 {primary}，强调色 {accent}。"
        "不生成文字、Logo、水印、虚构数据或模仿具体艺术家；保留安全留白；画面只服务文章语义。"
    )
    return [
        {
            "id": "illustration-main",
            "use_case": "illustration-story",
            "target": "公众号正文横图，900×500，导出PNG/JPG后自动上传",
            "prompt": shared + "创作一张具有单一叙事焦点的编辑插画，主体动作明确，材质和光线真实克制。",
        },
        {
            "id": "background-texture",
            "use_case": "stylized-concept",
            "target": "微信公众号背景纹理，1080×420，低对比度PNG",
            "prompt": shared + "创作稀疏、低对比、可裁切的背景纹理，不含人物、文字或醒目主体。",
        },
        {
            "id": "emoji-sticker-sheet",
            "use_case": "stylized-concept",
            "target": "如原生Emoji不适合品牌时，生成一张小型装饰贴纸PNG，不承担关键信息",
            "prompt": shared + "创作一组统一笔触的小型符号贴纸，单色或双色，留足透明背景移除空间。",
        },
    ]


def component_html(topic: str, palette: list[str], emojis: list[str]) -> str:
    background, primary, accent = palette
    topic_text = html.escape(topic[:48])
    emoji_text = "&nbsp;".join(html.escape(item) for item in emojis)
    return (
        f'<section data-component="emoji-line-frame" style="margin:28px 0;padding:18px 16px;border-top:3px solid {primary};border-bottom:1px solid {primary};background-color:{background};">'
        f'<p style="margin:0 0 10px;color:{accent};font-size:20px;line-height:1.35;">{emoji_text}</p>'
        f'<p style="margin:0;color:{primary};font-size:17px;font-weight:700;line-height:1.58;">{topic_text}</p>'
        f'<p style="margin:8px 0 0;color:{primary};font-size:13px;line-height:1.72;">原生 Emoji 用作节奏标记；线框承担分组，不以装饰替代内容。</p>'
        "</section>\n"
    )


def build_visual_plan(topic: str, *, palette: list[str] | None = None) -> dict[str, Any]:
    colors = list(palette or ["#101522", "#FF5B45", "#C8FF4A"])
    while len(colors) < 3:
        colors.append("#C8FF4A")
    colors = colors[:3]
    emojis = choose_emojis(topic)
    return {
        "schema_version": "1.0",
        "created_at": now_iso(),
        "topic": topic,
        "palette": colors,
        "selection_order": ["user-specified", "user-library", "licensed-external", "imagegen", "programmatic"],
        "elements": [
            {
                "type": "emoji",
                "values": emojis,
                "delivery": "native-unicode-in-html",
                "upload_required": False,
                "rules": ["全文默认不超过3种", "不承载唯一信息", "正式/法律/医疗主题默认不用"],
            },
            {
                "type": "icon",
                "source": "Iconify lucide/tabler/ph",
                "external_query": ["search", "arrow-right", "sparkles"],
                "delivery": "sanitize SVG then rasterize to PNG",
                "upload_required": True,
                "rules": ["一个文章只用一个图标家族", "SVG源不直接放公众号正文", "记录许可证和署名"],
            },
            {
                "type": "line-frame",
                "source": "inline HTML/CSS",
                "delivery": "wechat-safe HTML component",
                "upload_required": False,
                "rules": ["只在语义分组或转折出现", "不连续重复同一种边线组件"],
            },
            {
                "type": "illustration",
                "source": "licensed external or imagegen",
                "delivery": "PNG/JPG, optionally GIF with static fallback",
                "upload_required": True,
                "rules": ["每张图必须承担证据、解释、情绪或路径之一", "无合适外部素材时调用image_gen"],
            },
            {
                "type": "background",
                "source": "asset_factory or imagegen",
                "delivery": "low-contrast PNG texture",
                "upload_required": True,
                "rules": ["不能降低正文对比度", "不能把背景图作为唯一信息"],
            },
        ],
        "imagegen_tasks": imagegen_tasks(topic, colors),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="为公众号文章规划Emoji、图标、线框组件、插画和背景，并生成微信安全组件与imagegen任务")
    parser.add_argument("topic")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--palette", nargs=3)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plan = build_visual_plan(args.topic, palette=args.palette)
    write_json(args.output_dir / "visual-elements.json", plan)
    write_json(args.output_dir / "imagegen-prompts.json", {"topic": args.topic, "tasks": plan["imagegen_tasks"]})
    write_text(args.output_dir / "emoji-line-frame.html", component_html(args.topic, plan["palette"], plan["elements"][0]["values"]))
    print(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
