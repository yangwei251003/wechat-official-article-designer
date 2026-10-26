from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import now_iso, write_json

DIRECTIONS = [
    {"id": "clarity", "name": "信息清晰型", "keywords": ["清楚", "可信", "低干扰"], "layout_strategy": "证据式单列：结论先行、解释图、行动清单", "component_strategy": ["evidence-heading", "annotated-diagram", "action-checklist"], "image_strategy": "原创解释图承担关系说明，不使用装饰图库", "spacing": "comfortable", "decoration": "low", "motion": "none", "controls": {"design_variance": 4, "motion_intensity": 1, "visual_density": 5}},
    {"id": "brand", "name": "品牌专业型", "keywords": ["一致", "权威", "系统"], "layout_strategy": "品牌声明首屏、证据带、人物/产品锚点、签名收束", "component_strategy": ["brand-statement", "evidence-band", "signature-close"], "image_strategy": "真实品牌资产或定向生成主视觉，强调统一裁切和光线", "spacing": "balanced", "decoration": "medium", "motion": "subtle", "controls": {"design_variance": 6, "motion_intensity": 2, "visual_density": 6}},
    {"id": "visual", "name": "视觉传播型", "keywords": ["记忆点", "张力", "分享"], "layout_strategy": "海报首屏、编辑分栏、全幅停顿、强对照、海报收束", "component_strategy": ["poster-hero", "editorial-spread", "contrast-strip"], "image_strategy": "以一个原创视觉母题贯穿主图、SVG、GIF与章节动作", "spacing": "dramatic", "decoration": "controlled-high", "motion": "one semantic GIF with static fallback", "controls": {"design_variance": 8, "motion_intensity": 4, "visual_density": 5}}
]


def build_design_brief(track: str, title: str, *, brand_constraints: list[str] | None = None, palette: list[str] | None = None) -> dict[str, Any]:
    base_palette = palette or ["#263A39", "#5E827D", "#EEF4F1"]
    directions = []
    for index, template in enumerate(DIRECTIONS):
        item = dict(template)
        shift = index % len(base_palette)
        item["palette"] = base_palette[shift:] + base_palette[:shift]
        item["title_structure"] = ["eyebrow", "main-title", "one-sentence-promise"] if index != 2 else ["visual-hook", "main-title", "short-subtitle"]
        item["visual_concept"] = f"从《{title}》的核心因果关系提炼单一母题；去掉文字后仍能辨认主题"
        directions.append(item)
    return {"schema_version": "2.1", "generated_at": now_iso(), "title": title, "track": track, "goal": "让内容目标、视觉表达与微信兼容约束保持一致", "design_read": {"article_type": track, "audience": "根据资料判断并记录", "action": "读完后的唯一主要动作", "emotion": "由内容冲突决定", "visual_family": "由核心母题决定，不继承旧示例", "wechat_constraint": "inline CSS / static fallback / system fonts / mobile width"}, "legacy_visual_policy": "greenfield-do-not-reference", "brand_constraints": brand_constraints or [], "wechat_constraints": ["inline CSS", "no script", "static fallback", "system fonts", "mobile width"], "directions": directions}


def main() -> int:
    parser = argparse.ArgumentParser(description="生成三套结构、组件和图片策略均不同的Design Brief")
    parser.add_argument("title")
    parser.add_argument("--track", default="通用内容")
    parser.add_argument("--palette", nargs=3)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    write_json(args.output, build_design_brief(args.track, args.title, palette=args.palette))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
