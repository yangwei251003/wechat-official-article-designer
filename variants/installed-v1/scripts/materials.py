from __future__ import annotations

import argparse
import json
import mimetypes
import os
import urllib.parse
import urllib.request
from pathlib import Path

from common import now_iso, read_json, write_json


USER_AGENT = "wechat-official-article-designer/1.0"
ICON_LICENSE_ALLOWLIST = {"lucide": "ISC", "tabler": "MIT", "ph": "MIT"}


def get_json(url: str, headers: dict[str, str] | None = None) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def register_in_package(package_dir: Path, target: Path, entry: dict) -> None:
    package_dir = package_dir.resolve()
    target = target.resolve()
    try:
        relative = target.relative_to(package_dir)
    except ValueError as exc:
        raise SystemExit("登记到文章包的素材必须保存在文章包目录内") from exc
    manifest_path = package_dir / "article-package.json"
    if not manifest_path.exists():
        raise SystemExit("package-dir中缺少article-package.json")
    entry["local_path"] = str(relative).replace("\\", "/")
    manifest = read_json(manifest_path)
    assets = {item.get("id"): item for item in manifest.get("assets", [])}
    assets[entry["id"]] = entry
    manifest["assets"] = list(assets.values())
    write_json(manifest_path, manifest)


def search_openverse(query: str, limit: int) -> list[dict]:
    params = urllib.parse.urlencode({"q": query, "page_size": min(limit, 20), "license_type": "commercial", "mature": "false"})
    data = get_json(f"https://api.openverse.org/v1/images/?{params}")
    results = []
    for item in data.get("results", [])[:limit]:
        results.append({
            "id": item.get("id"), "title": item.get("title") or query, "preview_url": item.get("thumbnail"),
            "download_url": item.get("url"), "source_url": item.get("foreign_landing_url"), "creator": item.get("creator") or "Unknown",
            "creator_url": item.get("creator_url") or "", "license": item.get("license") or "", "license_url": item.get("license_url") or "",
            "credit": f"{item.get('creator') or 'Unknown'} / Openverse / {item.get('license') or 'license unknown'}",
        })
    return results


def search_pexels(query: str, limit: int) -> list[dict]:
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        raise SystemExit("使用Pexels前请设置环境变量 PEXELS_API_KEY")
    params = urllib.parse.urlencode({"query": query, "per_page": min(limit, 40), "orientation": "landscape"})
    data = get_json(f"https://api.pexels.com/v1/search?{params}", {"Authorization": key})
    results = []
    for item in data.get("photos", [])[:limit]:
        results.append({
            "id": str(item.get("id")), "title": item.get("alt") or query, "preview_url": item.get("src", {}).get("medium"),
            "download_url": item.get("src", {}).get("large2x") or item.get("src", {}).get("original"), "source_url": item.get("url"),
            "creator": item.get("photographer") or "Unknown", "creator_url": item.get("photographer_url") or "", "license": "Pexels License",
            "license_url": "https://www.pexels.com/license/", "credit": f"Photo by {item.get('photographer') or 'Unknown'} on Pexels",
        })
    return results


def command_search(args: argparse.Namespace) -> int:
    results = search_openverse(args.query, args.limit) if args.provider == "openverse" else search_pexels(args.query, args.limit)
    payload = {"schema_version": "1.0", "provider": args.provider, "query": args.query, "searched_at": now_iso(), "results": results}
    write_json(args.output, payload)
    print(f"{len(results)} results -> {args.output}")
    return 0


def download_bytes(url: str, max_mb: int) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45) as response:
        content_type = response.headers.get_content_type()
        data = response.read(max_mb * 1024 * 1024 + 1)
    if len(data) > max_mb * 1024 * 1024:
        raise SystemExit(f"素材超过 {max_mb}MB，已中止")
    if not content_type.startswith("image/"):
        raise SystemExit(f"下载内容不是图片：{content_type}")
    return data, content_type


def command_download(args: argparse.Namespace) -> int:
    payload = read_json(args.results)
    items = payload.get("results", [])
    if args.index < 0 or args.index >= len(items):
        raise SystemExit("index超出搜索结果范围")
    item = items[args.index]
    if not item.get("license") or not item.get("license_url") or not item.get("source_url"):
        raise SystemExit("素材缺少许可证或来源页，拒绝下载")
    data, content_type = download_bytes(item["download_url"], args.max_mb)
    suffix = Path(urllib.parse.urlparse(item["download_url"]).path).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        suffix = mimetypes.guess_extension(content_type) or ".jpg"
    target = args.output if args.output.suffix else args.output.with_suffix(suffix)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    entry = {
        "id": args.asset_id or target.stem, "role": args.role, "local_path": str(target).replace("\\", "/"), "provider": payload.get("provider"),
        "creator": item.get("creator"), "source_url": item.get("source_url"), "license": item.get("license"), "license_url": item.get("license_url"),
        "credit": item.get("credit"), "accessed_at": now_iso(), "modifications": "downloaded via official API; pending crop/compression", "wechat_url": "",
    }
    if args.manifest_out:
        write_json(args.manifest_out, entry)
    if args.package_dir:
        register_in_package(args.package_dir, target, entry)
    print(target)
    return 0


def command_icon(args: argparse.Namespace) -> int:
    if ":" not in args.name:
        raise SystemExit("图标名必须为 prefix:name，例如 lucide:quote")
    prefix, name = args.name.split(":", 1)
    if prefix not in ICON_LICENSE_ALLOWLIST:
        raise SystemExit(f"只允许自动使用这些图标集：{', '.join(ICON_LICENSE_ALLOWLIST)}")
    query = urllib.parse.urlencode({"color": args.color, "width": args.width, "height": args.height})
    url = f"https://api.iconify.design/{urllib.parse.quote(prefix)}/{urllib.parse.quote(name)}.svg?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=25) as response:
        data = response.read(2 * 1024 * 1024)
    if b"<svg" not in data[:500]:
        raise SystemExit("Iconify没有返回SVG")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    entry = {
        "id": args.asset_id or args.output.stem, "role": "ornament", "local_path": str(args.output).replace("\\", "/"), "provider": "iconify",
        "creator": prefix, "source_url": f"https://icon-sets.iconify.design/{prefix}/{name}/", "license": ICON_LICENSE_ALLOWLIST[prefix],
        "license_url": f"https://api.iconify.design/collection?prefix={prefix}", "credit": f"{prefix}:{name} via Iconify",
        "accessed_at": now_iso(), "modifications": f"SVG color {args.color}; must rasterize before WeChat use", "wechat_url": "",
    }
    if args.manifest_out:
        write_json(args.manifest_out, entry)
    if args.package_dir:
        register_in_package(args.package_dir, args.output, entry)
    print(args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="通过正规API检索、下载和登记公众号素材")
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search")
    search.add_argument("--provider", choices=["openverse", "pexels"], default="openverse")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=8)
    search.add_argument("--output", required=True, type=Path)
    search.set_defaults(func=command_search)
    download = sub.add_parser("download")
    download.add_argument("--results", required=True, type=Path)
    download.add_argument("--index", type=int, required=True)
    download.add_argument("--output", required=True, type=Path)
    download.add_argument("--max-mb", type=int, default=20)
    download.add_argument("--asset-id")
    download.add_argument("--role", choices=["cover", "inline", "illustration", "texture", "ornament", "qr"], default="inline")
    download.add_argument("--manifest-out", type=Path)
    download.add_argument("--package-dir", type=Path, help="可选：把素材登记进文章包")
    download.set_defaults(func=command_download)
    icon = sub.add_parser("icon")
    icon.add_argument("--name", required=True)
    icon.add_argument("--color", default="#315f58")
    icon.add_argument("--width", type=int, default=128)
    icon.add_argument("--height", type=int, default=128)
    icon.add_argument("--output", required=True, type=Path)
    icon.add_argument("--asset-id")
    icon.add_argument("--manifest-out", type=Path)
    icon.add_argument("--package-dir", type=Path, help="可选：把SVG源素材登记进文章包；发布前仍需转PNG")
    icon.set_defaults(func=command_icon)
    return parser


if __name__ == "__main__":
    parsed = build_parser().parse_args()
    raise SystemExit(parsed.func(parsed))
