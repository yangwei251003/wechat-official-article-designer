from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from common import read_json, read_text, write_json

LEGACY_MARKERS = {
    "original-ornament",
    "playful-confetti",
    "paper-wave",
    "narrative-ripple",
}
REQUIRED_DESIGN_READ = {"article_type", "audience", "action", "emotion", "visual_family", "wechat_constraint"}
REQUIRED_CONTROLS = {"design_variance", "motion_intensity", "visual_density"}


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _all_assets(article: dict[str, Any], extra_assets: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    result = list(article.get("assets") or [])
    known = {str(item.get("id", "")) for item in result}
    for item in extra_assets or []:
        if str(item.get("id", "")) not in known:
            result.append(item)
    return result


def audit_high_design(article: dict[str, Any], fragment: str, assets: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    design = article.get("design") or {}
    read = design.get("design_read") or {}
    controls = design.get("controls") or {}
    rhythms = [str(item).strip() for item in design.get("rhythm_families") or [] if str(item).strip()]
    combined_assets = _all_assets(article, assets)
    original_ready = [
        item for item in combined_assets
        if item.get("provider") in {"original", "ai-generated"}
        and item.get("wechat_ready") is True
        and str(item.get("local_path", "")).lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
    ]
    hero_assets = [item for item in original_ready if item.get("role") in {"cover", "hero", "inline-hero", "key-visual"}]

    if design.get("mode") != "high-design":
        errors.append(_issue("mode", "高设计交付必须显式记录 design.mode=high-design。"))
    missing_read = sorted(REQUIRED_DESIGN_READ - set(read))
    if missing_read or any(not str(read.get(key, "")).strip() for key in REQUIRED_DESIGN_READ):
        errors.append(_issue("design-read", "Design Read 不完整：" + "、".join(missing_read or sorted(REQUIRED_DESIGN_READ))))
    if set(controls) < REQUIRED_CONTROLS or any(not isinstance(controls.get(key), int) or not 1 <= controls[key] <= 10 for key in REQUIRED_CONTROLS):
        errors.append(_issue("visual-controls", "三只视觉旋钮必须完整，并使用 1–10 的整数。"))
    if not str(design.get("visual_concept", "")).strip():
        errors.append(_issue("visual-concept", "必须记录一个与文章命题存在因果关系的核心视觉概念。"))
    if len(set(rhythms)) < 3:
        errors.append(_issue("rhythm", "高设计长文至少需要三种明确的节奏家族。"))
    if len(original_ready) < 2:
        errors.append(_issue("original-assets", "必须至少交付两项微信可用的原创或 AI 生成视觉资产。"))
    if not hero_assets:
        errors.append(_issue("hero", "必须有一项原创且微信可用的主视觉/封面资产。"))

    lowered = fragment.lower()
    legacy_hits = sorted(marker for marker in LEGACY_MARKERS if marker in lowered)
    legacy_hits.extend(
        marker for marker in LEGACY_MARKERS
        if any(marker in str(item.get("local_path", "")).lower() or marker in str(item.get("id", "")).lower() for item in combined_assets)
        and marker not in legacy_hits
    )
    if legacy_hits:
        errors.append(_issue("legacy-reference", "新设计引用了旧版视觉标记：" + "、".join(sorted(set(legacy_hits)))))

    images = len(re.findall(r"<img\b", lowered))
    repeated_left_titles = len(re.findall(r"border-left\s*:\s*3px\s+solid", lowered))
    semantic_markers = sum(lowered.count(marker) for marker in ("data-rhythm=", "data-visual-role=", "data-component="))
    baseline_signature = "letter-spacing:.03em" in lowered and "padding:22px 16px" in lowered
    if images == 0 and semantic_markers == 0 and (repeated_left_titles >= 1 or baseline_signature):
        errors.append(_issue("baseline-only", "当前 HTML 仍是保守基线排版，不能作为高设计最终成品。"))
    elif images == 0:
        warnings.append(_issue("no-inline-image", "正文没有内嵌主视觉，请确认图片是否将在微信草稿上传阶段注入。"))

    return {
        "ok": not errors,
        "mode": design.get("mode", ""),
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "rhythm_families": len(set(rhythms)),
            "original_wechat_assets": len(original_ready),
            "hero_assets": len(hero_assets),
            "inline_images": images,
            "semantic_design_markers": semantic_markers,
        },
    }


def audit_package(package: Path) -> dict[str, Any]:
    article_path = package / "article.json"
    fragment_path = package / "article-fragment.html"
    if not article_path.exists() or not fragment_path.exists():
        return {"ok": False, "errors": [_issue("missing-files", "缺少 article.json 或 article-fragment.html。")], "warnings": [], "metrics": {}}
    article = read_json(article_path)
    assets: list[dict[str, Any]] = []
    for candidate in (package / "assets" / "asset-set.json", package / "article-package.json"):
        if candidate.exists():
            assets.extend(read_json(candidate).get("assets") or [])
    report = audit_high_design(article, read_text(fragment_path), assets)
    report["package"] = package.name
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="检查高审美公众号交付是否越过保守基线并拥有原创资产")
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_package(args.package)
    if args.output:
        write_json(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
