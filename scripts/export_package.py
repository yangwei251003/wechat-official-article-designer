from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from common import safe_resolve


def export_zip(package_dir: Path, target: Path) -> Path:
    package_dir = package_dir.resolve()
    if not package_dir.is_dir():
        raise ValueError("文章包目录不存在")
    target = target.resolve()
    if target == package_dir or package_dir in target.parents:
        raise ValueError("ZIP输出不得位于文章包内部")
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(package_dir.rglob("*")):
            if not path.is_file():
                continue
            safe = safe_resolve(path, package_dir)
            relative = safe.relative_to(package_dir).as_posix()
            if relative.startswith("/") or ".." in Path(relative).parts:
                raise ValueError(f"不安全的归档路径：{relative}")
            archive.write(safe, relative)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="安全打包文章交付物为ZIP")
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(export_zip(args.package_dir, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
