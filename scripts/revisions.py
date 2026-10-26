from __future__ import annotations

import argparse
import copy
from pathlib import Path
from typing import Any

from article_schema import validate_article
from common import now_iso, read_json, write_json


class LockViolation(RuntimeError):
    pass


def _find_node(article: dict[str, Any], node_id: str) -> dict[str, Any]:
    for section in article["content"]["sections"]:
        for node in section.get("nodes", []):
            if node.get("id") == node_id:
                return node
    raise KeyError(f"未找到节点：{node_id}")


def apply_text_revision(article: dict[str, Any], node_id: str, text: str, *, actor: str, reason: str = "authorized revision") -> dict[str, Any]:
    revised = copy.deepcopy(article)
    node = _find_node(revised, node_id)
    locks = revised.get("locks", {})
    if locks.get("document") or node.get("locked") or node_id in locks.get("node_ids", []):
        raise LockViolation(f"节点已锁定，禁止修改：{node_id}")
    if node.get("type") != "text":
        raise ValueError("apply_text_revision只处理文本节点")
    before_content = copy.deepcopy(revised["content"])
    old = str(node.get("text", ""))
    node["text"] = text
    node["provenance"] = {"kind": "user-authorized-edit" if actor == "user" else "ai", "source_refs": [node_id]}
    versions = [int(item.get("version", 0)) for item in revised.get("history", []) if str(item.get("version", "")).isdigit()]
    revised.setdefault("history", []).append({"version": str(max(versions, default=0) + 1), "timestamp": now_iso(), "actor": actor, "changes": [f"{node_id}: {reason}"], "before_content": before_content, "diff": {"node_id": node_id, "before": old, "after": text}})
    validation = validate_article(revised)
    if not validation["ok"]:
        raise ValueError("修改后Article Schema无效：" + "; ".join(validation["errors"]))
    return revised


def rollback(article: dict[str, Any], *, version: str) -> dict[str, Any]:
    if not version.isdigit():
        raise ValueError("version必须为数字字符串")
    target = int(version)
    restored = copy.deepcopy(article)
    applied = False
    for entry in reversed(restored.get("history", [])):
        current = int(entry.get("version", 0)) if str(entry.get("version", "")).isdigit() else 0
        if current > target and entry.get("before_content"):
            restored["content"] = copy.deepcopy(entry["before_content"])
            applied = True
    if not applied and target != max([int(item.get("version", 0)) for item in restored.get("history", []) if str(item.get("version", "")).isdigit()] or [0]):
        raise ValueError(f"无法回退到版本{version}：缺少快照")
    versions = [int(item.get("version", 0)) for item in restored.get("history", []) if str(item.get("version", "")).isdigit()]
    restored.setdefault("history", []).append({"version": str(max(versions, default=0) + 1), "timestamp": now_iso(), "actor": "rollback", "changes": [f"restored content to version {version}"]})
    return restored


def main() -> int:
    parser = argparse.ArgumentParser(description="安全应用文章修改并保留版本/锁定状态")
    sub = parser.add_subparsers(dest="command", required=True)
    revise = sub.add_parser("revise-text")
    revise.add_argument("article", type=Path)
    revise.add_argument("node_id")
    revise.add_argument("text")
    revise.add_argument("--actor", default="ai")
    revise.add_argument("--output", required=True, type=Path)
    back = sub.add_parser("rollback")
    back.add_argument("article", type=Path)
    back.add_argument("version")
    back.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = read_json(args.article)
    if args.command == "revise-text":
        result = apply_text_revision(payload, args.node_id, args.text, actor=args.actor)
    else:
        result = rollback(payload, version=args.version)
    write_json(args.output, result)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LockViolation as exc:
        print(str(exc))
        raise SystemExit(2) from exc
