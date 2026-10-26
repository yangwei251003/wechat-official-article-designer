from __future__ import annotations

import argparse
import io
from pathlib import Path

from common import now_iso, read_json, write_json

try:
    from PIL import Image, ImageOps
except ImportError as exc:
    raise SystemExit("需要Pillow：请使用Codex工作区Python运行，或安装 pillow") from exc


VARIANTS = [
    ("cover-main", "cover", (900, 383)),
    ("guide-wide", "inline", (900, 500)),
    ("cover-square", "cover-crop", (900, 900)),
]


def save_under_limit(image: Image.Image, path: Path, max_kb: int, prefer_png: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if prefer_png:
        buffer = io.BytesIO()
        image.save(buffer, "PNG", optimize=True)
        if len(buffer.getvalue()) <= max_kb * 1024:
            path.with_suffix(".png").write_bytes(buffer.getvalue())
            return
    rgb = image.convert("RGB")
    for quality in range(92, 49, -6):
        buffer = io.BytesIO()
        rgb.save(buffer, "JPEG", quality=quality, optimize=True, progressive=True)
        if len(buffer.getvalue()) <= max_kb * 1024:
            path.with_suffix(".jpg").write_bytes(buffer.getvalue())
            return
    raise ValueError(f"无法把图片压缩到 {max_kb}KB 以下：{path.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成微信封面、正文横图和方形裁切")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--focal-x", type=float, default=0.5)
    parser.add_argument("--focal-y", type=float, default=0.5)
    parser.add_argument("--max-kb", type=int, default=950)
    parser.add_argument("--manifest", type=Path, help="可选：更新article-package.json")
    parser.add_argument("--provider", default="user-provided", choices=["user-provided", "generated", "original", "openverse", "pexels", "canva", "figma"])
    parser.add_argument("--creator", default="")
    parser.add_argument("--source-url", default="")
    parser.add_argument("--license", default="User-confirmed rights")
    parser.add_argument("--license-url", default="")
    args = parser.parse_args()

    if not 0 <= args.focal_x <= 1 or not 0 <= args.focal_y <= 1:
        raise SystemExit("focal-x/focal-y 必须在0到1之间")
    if args.provider not in {"user-provided", "generated", "original"} and not all([args.creator, args.source_url, args.license, args.license_url]):
        raise SystemExit("第三方素材必须提供 creator、source-url、license 和 license-url")

    source = Image.open(args.input)
    source = ImageOps.exif_transpose(source)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for asset_id, role, size in VARIANTS:
        rendered = ImageOps.fit(source, size, method=Image.Resampling.LANCZOS, centering=(args.focal_x, args.focal_y))
        target = output_dir / asset_id
        save_under_limit(rendered, target, args.max_kb, prefer_png=(source.mode in {"RGBA", "LA"}))
        actual = target.with_suffix(".png") if target.with_suffix(".png").exists() else target.with_suffix(".jpg")
        entries.append({
            "id": asset_id,
            "role": role,
            "local_path": actual.name if not args.manifest else str(Path("assets") / actual.name).replace("\\", "/"),
            "provider": args.provider,
            "creator": args.creator,
            "source_url": args.source_url,
            "license": args.license,
            "license_url": args.license_url,
            "credit": f"{args.creator} / {args.provider}" if args.creator else args.provider,
            "accessed_at": now_iso(),
            "modifications": f"center-crop {size[0]}x{size[1]}, optimized under {args.max_kb}KB",
            "wechat_url": "",
        })
    if args.manifest:
        manifest = read_json(args.manifest)
        existing = {item.get("id"): item for item in manifest.get("assets", [])}
        existing.update({item["id"]: item for item in entries})
        manifest["assets"] = list(existing.values())
        manifest.setdefault("publishing", {})["cover_asset_id"] = "cover-main"
        write_json(args.manifest, manifest)
    print(str(output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

