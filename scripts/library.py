from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from common import now_iso, sha256_file, write_json
from inventory import DEFAULT_EXCLUDES

ORIGIN_PRIORITY = {"user-specified": 0, "user-library": 1, "user-upload": 2, "external": 3, "generated": 4, "programmatic": 5}


def _tokens(value: str) -> set[str]:
    return {token for token in re.split(r"[^\w\u4e00-\u9fff]+", value.lower()) if token}


def rank_assets(items: list[dict[str, Any]], *, query: str, brand: str = "") -> list[dict[str, Any]]:
    query_tokens = _tokens(query)
    ranked = []
    for item in items:
        haystack = " ".join([str(item.get("title", "")), " ".join(item.get("tags", [])), str(item.get("ocr_text", ""))]).lower()
        item_tokens = _tokens(haystack)
        matched = {token for token in query_tokens if token in item_tokens or token in haystack}
        overlap = len(matched) / max(1, len(query_tokens))
        origin = int(item.get("origin_priority", 3))
        license_status = str(item.get("license_status", "unknown"))
        license_score = {"verified": 1.0, "review": 0.2, "unknown": -2.0, "blocked": -10.0}.get(license_status, -2.0)
        brand_score = 1.0 if brand and item.get("brand") == brand else 0.0
        repeat_penalty = min(float(item.get("use_count", 0)) * 0.08, 1.0)
        score = overlap * 5 + (5 - origin) * 0.7 + license_score + brand_score - repeat_penalty
        ranked.append({**item, "score": round(score, 4)})
    return sorted(ranked, key=lambda item: (-item["score"], str(item.get("id", ""))))


def build_index(root: Path) -> dict[str, Any]:
    root = root.resolve()
    items = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if not path.is_file() or any(part in DEFAULT_EXCLUDES for part in rel.parts) or path.name in {"library-index.json", "license-register.csv"}:
            continue
        origin = "user-library"
        items.append({"schema_version": "1.0", "id": sha256_file(path)[:16], "path": rel.as_posix(), "title": path.stem, "tags": [part for part in rel.parts[:-1]], "ocr_text": "", "people": [], "products": [], "places": [], "dominant_color": "", "ratio": "", "resolution": "", "style": "", "mood": "", "topics": [], "brand": "", "origin": origin, "origin_priority": ORIGIN_PRIORITY[origin], "source": "user-library", "creator": "", "license": "", "license_status": "unknown", "commercial_use": "unknown", "attribution_required": "unknown", "modification_allowed": "unknown", "redistribution_allowed": "unknown", "expires_at": "", "sha256": sha256_file(path), "use_count": 0, "last_used_at": ""})
    return {"schema_version": "1.0", "created_at": now_iso(), "root": ".", "items": items}


def main() -> int:
    parser = argparse.ArgumentParser(description="构建和检索个人素材仓库")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("root", type=Path)
    build.add_argument("--output", required=True, type=Path)
    search = sub.add_parser("search")
    search.add_argument("index", type=Path)
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    if args.command == "build":
        write_json(args.output, build_index(args.root))
    else:
        payload = json.loads(args.index.read_text(encoding="utf-8"))
        print(json.dumps(rank_assets(payload.get("items", []), query=args.query)[: args.limit], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
