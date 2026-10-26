from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import now_iso, read_json, write_json, write_text

LOW_RISK = {"MIT", "ISC", "APACHE-2.0", "BSD-2-CLAUSE", "BSD-3-CLAUSE", "CC0", "CC0-1.0", "PUBLIC DOMAIN", "AI-GENERATED ORIGINAL ARTWORK", "ORIGINAL ASSET", "USER-CONFIRMED RIGHTS"}


def _decision(asset: dict[str, Any]) -> tuple[str, str]:
    provider = str(asset.get("provider", "")).lower()
    license_name = str(asset.get("license", "")).strip()
    if provider == "user-provided" and not license_name:
        return "manual_review", "用户上传素材权属未确认"
    if not license_name or not asset.get("source_url") and provider not in {"original", "generated", "user-provided", "mock"}:
        return "manual_review", "缺少许可证或原始来源"
    upper = license_name.upper()
    if "WATERMARK" in upper or "UNKNOWN" in upper or "NO COMMERCIAL" in upper:
        return "blocked", "授权不明或禁止商用"
    if upper in LOW_RISK:
        return "allowed", "满足具体条款后可使用"
    if "CC BY" in upper or "OFL" in upper or "PEXELS" in upper:
        return "attribution_required", "需要署名并遵守平台/许可证条款"
    return "manual_review", "自定义或特殊许可证需人工判断"


def build_report(assets: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for asset in assets:
        decision, reason = _decision(asset)
        rows.append({**asset, "decision": decision, "reason": reason})
    blocked = [item.get("id", "") for item in rows if item["decision"] in {"blocked", "manual_review"}]
    return {"schema_version": "1.0", "generated_at": now_iso(), "auto_publish_allowed": not blocked, "blocked_or_review_asset_ids": blocked, "assets": rows}


def markdown_report(report: dict[str, Any]) -> str:
    lines = ["# 素材来源与版权报告", "", f"- 生成时间：{report['generated_at']}", f"- 自动发布许可：{'允许' if report['auto_publish_allowed'] else '不允许，需人工处理'}", "", "| 素材 | 来源 | 许可证 | 决策 | 原因 |", "|---|---|---|---|---|"]
    for item in report["assets"]:
        lines.append(f"| {item.get('id','')} | {item.get('provider','')} | {item.get('license','')} | {item['decision']} | {item['reason']} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="生成素材版权账本、署名与自动发布阻断报告")
    parser.add_argument("manifest", type=Path, help="article-package.json或包含assets的JSON")
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    report = build_report(read_json(args.manifest).get("assets", []))
    write_json(args.json_out, report)
    if args.markdown_out:
        write_text(args.markdown_out, markdown_report(report))
    return 0 if report["auto_publish_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
