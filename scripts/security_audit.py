from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

RULES = {
    "hardcoded-secret": re.compile(r"(?:APP_SECRET|API_KEY|ACCESS_TOKEN|PASSWORD)\s*=\s*['\"][^'\"\s]{6,}['\"]", re.I),
    "path-traversal": re.compile(r"(?:open|Path)\s*\(\s*['\"][^'\"]*\.\.[/\\]", re.I),
    "shell-injection": re.compile(r"(?:shell\s*=\s*True|\beval\s*\(|\bexec\s*\()", re.I),
    "unsafe-remote-install": re.compile(r"(?:curl|wget)[^\n|]*\|\s*(?:bash|sh|powershell)", re.I),
}


def scan_text(text: str, *, file: str = "<memory>") -> list[dict[str, Any]]:
    issues = []
    for rule, pattern in RULES.items():
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            line_text = text.splitlines()[line - 1] if text.splitlines() else ""
            if "security-audit: allow-test-fixture" in line_text:
                continue
            issues.append({"rule": rule, "file": file, "line": line, "severity": "high" if rule in {"hardcoded-secret", "shell-injection", "unsafe-remote-install"} else "medium"})
    return issues


def scan_tree(root: Path) -> dict[str, Any]:
    root = root.resolve()
    issues = []
    checked = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in {".git", "__pycache__", "node_modules"} for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() not in {".py", ".md", ".json", ".yaml", ".yml", ".html", ".txt", ".toml", ".env", ".example"} and path.name != ".env.example":
            continue
        checked += 1
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        issues.extend(scan_text(text, file=path.relative_to(root).as_posix()))
    return {"ok": not any(item["severity"] == "high" for item in issues), "files_checked": checked, "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser(description="检查硬编码凭证、路径穿越和危险命令模式")
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = scan_tree(args.root)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
