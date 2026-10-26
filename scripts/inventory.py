from __future__ import annotations

import argparse
import json
import mimetypes
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import now_iso, safe_resolve, sha256_file, write_json

DEFAULT_EXCLUDES = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", ".playwright-cli", ".playwright-mcp", "%USERPROFILE%"}


def build_inventory(root: Path, *, excludes: set[str] | None = None) -> dict[str, Any]:
    root = safe_resolve(root, root)
    ignored = DEFAULT_EXCLUDES | (excludes or set())
    files: list[dict[str, Any]] = []
    hashes: dict[str, list[str]] = defaultdict(list)
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in ignored for part in relative.parts):
            continue
        if not path.is_file():
            continue
        digest = sha256_file(path)
        rel = relative.as_posix()
        hashes[digest].append(rel)
        files.append({"path": rel, "size": path.stat().st_size, "sha256": digest, "media_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream", "status": "discovered"})
    duplicates = [{"sha256": digest, "paths": paths} for digest, paths in hashes.items() if len(paths) > 1]
    return {"schema_version": "1.0", "root": ".", "created_at": now_iso(), "summary": {"files": len(files), "bytes": sum(item["size"] for item in files), "duplicate_groups": len(duplicates)}, "files": files, "duplicates": duplicates}


def main() -> int:
    parser = argparse.ArgumentParser(description="盘点资料文件、类型、哈希和重复项")
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_inventory(args.root)
    if args.output:
        write_json(args.output, result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
