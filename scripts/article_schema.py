from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from common import SKILL_DIR, markdown_blocks, now_iso, read_json, read_text, write_json

SCHEMA_PATH = SKILL_DIR / "assets" / "article-schema-v2.json"
FONT_STACK = "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',Arial,sans-serif"


def _document_id(title: str, source: str) -> str:
    return hashlib.sha256(f"{title}\0{source}".encode("utf-8")).hexdigest()[:16]


def scaffold_from_source(source: str, *, title: str = "未命名文章") -> dict[str, Any]:
    blocks = markdown_blocks(source)
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] = {"id": "section-1", "title": "", "locked": False, "source": {"kind": "user", "source_refs": ["source.md"]}, "nodes": []}
    sections.append(current)
    node_index = 0
    for block in blocks:
        if block["type"] == "heading":
            if block.get("level") == "1":
                continue
            if current["nodes"] or current["title"]:
                current = {"id": f"section-{len(sections)+1}", "title": block["text"], "locked": False, "source": {"kind": "user", "source_refs": ["source.md"]}, "nodes": []}
                sections.append(current)
            else:
                current["title"] = block["text"]
            continue
        if block["type"] == "image":
            node_index += 1
            current["nodes"].append({"id": f"node-{node_index}", "type": "image", "src": block.get("src", ""), "alt": block.get("alt", ""), "locked": False, "provenance": {"kind": "user", "source_refs": ["source.md"]}})
            continue
        if block.get("text"):
            node_index += 1
            current["nodes"].append({"id": f"node-{node_index}", "type": "text", "text": block["text"], "component": block["type"], "locked": False, "provenance": {"kind": "user", "source_refs": ["source.md"]}})
    if not sections:
        sections = [{"id": "section-1", "title": "", "locked": False, "source": {"kind": "user", "source_refs": ["source.md"]}, "nodes": []}]
    article = {
        "schema_version": "2.0", "document_id": _document_id(title, source),
        "metadata": {"title": title, "author": "", "language": "zh-CN", "created_at": now_iso(), "summary": ""},
        "goals": {"objective": "清晰、准确地完成微信公众号内容与视觉交付", "audience": "待确认", "call_to_action": "", "fact_risk": "low"},
        "content": {"title_candidates": [title], "sections": sections},
        "design": {"direction": "信息清晰型", "tokens": {"palette": ["#263A39", "#5E827D", "#EEF4F1"], "font_stack": FONT_STACK, "body_size": "15px", "line_height": 1.8, "spacing": "comfortable", "radius": "8px"}, "components": ["section-heading", "paragraph", "quote"]},
        "assets": [], "locks": {"document": False, "title": False, "node_ids": [], "data_paths": [], "asset_ids": []},
        "history": [{"version": "1", "timestamp": now_iso(), "actor": "script", "changes": ["scaffolded from source"]}],
        "wechat": {"compatibility_level": "strict", "cover_asset_id": "", "fallbacks": []},
        "copyright": {"status": "clear", "manual_review_asset_ids": []},
    }
    result = validate_article(article)
    if not result["ok"]:
        raise ValueError("生成的文章结构未通过Schema校验：" + "; ".join(result["errors"]))
    return article


def validate_article(article: dict[str, Any]) -> dict[str, Any]:
    try:
        import jsonschema
    except ImportError:
        required = {"schema_version", "document_id", "metadata", "goals", "content", "design", "assets", "locks", "history", "wechat", "copyright"}
        missing = sorted(required - set(article))
        return {"ok": not missing and article.get("schema_version") == "2.0", "errors": ([f"缺少字段：{x}" for x in missing] + ([] if article.get("schema_version") == "2.0" else ["schema_version必须为2.0"]))}
    schema = read_json(SCHEMA_PATH)
    validator = jsonschema.Draft202012Validator(schema)
    errors = [f"{'/'.join(str(x) for x in error.absolute_path) or '$'}: {error.message}" for error in sorted(validator.iter_errors(article), key=lambda e: list(e.absolute_path))]
    return {"ok": not errors, "errors": errors}


def migrate_v1_package(package: dict[str, Any]) -> dict[str, Any]:
    title = str(package.get("title") or "未命名文章")
    article = scaffold_from_source(f"# {title}\n", title=title)
    article["design"]["direction"] = str(package.get("design", {}).get("concept") or article["design"]["direction"])
    article["design"]["tokens"]["palette"] = list(package.get("design", {}).get("palette") or article["design"]["tokens"]["palette"])
    article["design"]["components"] = list(package.get("design", {}).get("components") or article["design"]["components"])
    article["assets"] = list(package.get("assets") or [])
    article["wechat"]["cover_asset_id"] = str(package.get("publishing", {}).get("cover_asset_id") or "")
    article["history"].append({"version": "2", "timestamp": now_iso(), "actor": "migration", "changes": ["migrated article-package 1.0 to article schema 2.0"]})
    return article


def main() -> int:
    parser = argparse.ArgumentParser(description="校验、生成或迁移Article Schema 2.0")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("article", type=Path)
    scaffold = sub.add_parser("scaffold")
    scaffold.add_argument("source", type=Path)
    scaffold.add_argument("--title", default="未命名文章")
    scaffold.add_argument("--output", required=True, type=Path)
    migrate = sub.add_parser("migrate-v1")
    migrate.add_argument("package", type=Path)
    migrate.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "validate":
        result = validate_article(read_json(args.article))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    if args.command == "scaffold":
        write_json(args.output, scaffold_from_source(read_text(args.source), title=args.title))
    else:
        write_json(args.output, migrate_v1_package(read_json(args.package)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
