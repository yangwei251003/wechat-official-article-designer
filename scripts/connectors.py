from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from common import SKILL_DIR, now_iso, read_json, write_json

USER_AGENT = "wechat-official-article-designer/2.0 (+local-skill)"
REGISTRY_PATH = SKILL_DIR / "assets" / "connector-registry.json"


class ConnectorPermissionError(RuntimeError):
    pass


class ConnectorConfigError(RuntimeError):
    pass


def registry() -> dict[str, Any]:
    return read_json(REGISTRY_PATH)


def _get_json(url: str, *, headers: dict[str, str] | None = None, timeout: int = 20) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read(5 * 1024 * 1024).decode("utf-8"))


def _mock(query: str, limit: int) -> list[dict[str, Any]]:
    seed = hashlib.sha256(query.encode("utf-8")).hexdigest()
    return [{"id": f"mock-{seed[:8]}-{index+1}", "title": f"{query} mock asset {index+1}", "preview_url": "", "download_url": "", "source_url": "local://mock", "creator": "test fixture", "license": "CC0-1.0", "license_url": "https://creativecommons.org/publicdomain/zero/1.0/", "credit": "No attribution required", "provider": "mock", "accessed_at": "1970-01-01T00:00:00+00:00"} for index in range(limit)]


def _openverse(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"q": query, "page_size": min(limit, 20), "license_type": "commercial", "mature": "false"})
    payload = _get_json(f"https://api.openverse.org/v1/images/?{params}")
    return [{"id": item.get("id"), "title": item.get("title") or query, "preview_url": item.get("thumbnail") or "", "download_url": item.get("url") or "", "source_url": item.get("foreign_landing_url") or "", "creator": item.get("creator") or "Unknown", "license": item.get("license") or "", "license_url": item.get("license_url") or "", "credit": f"{item.get('creator') or 'Unknown'} / {item.get('license') or 'license unknown'}", "provider": "openverse", "accessed_at": now_iso()} for item in payload.get("results", [])[:limit]]


def _pexels(query: str, limit: int) -> list[dict[str, Any]]:
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        raise ConnectorConfigError("PEXELS_API_KEY未配置；请使用Mock或其他无需密钥的来源")
    params = urllib.parse.urlencode({"query": query, "per_page": min(limit, 40), "orientation": "landscape"})
    payload = _get_json(f"https://api.pexels.com/v1/search?{params}", headers={"Authorization": key})
    return [{"id": str(item.get("id")), "title": item.get("alt") or query, "preview_url": item.get("src", {}).get("medium") or "", "download_url": item.get("src", {}).get("large2x") or item.get("src", {}).get("original") or "", "source_url": item.get("url") or "", "creator": item.get("photographer") or "Unknown", "license": "Pexels License", "license_url": "https://www.pexels.com/license/", "credit": f"Photo by {item.get('photographer') or 'Unknown'} on Pexels", "provider": "pexels", "accessed_at": now_iso()} for item in payload.get("photos", [])[:limit]]


def _iconify(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"query": query, "limit": min(limit, 32), "prefixes": "lucide,tabler,ph"})
    payload = _get_json(f"https://api.iconify.design/search?{params}")
    licenses = {"lucide": "ISC", "tabler": "MIT", "ph": "MIT"}
    output = []
    for name in payload.get("icons", [])[:limit]:
        prefix = name.split(":", 1)[0]
        output.append({"id": name, "title": name, "preview_url": f"https://api.iconify.design/{name.replace(':', '/')}.svg", "download_url": f"https://api.iconify.design/{name.replace(':', '/')}.svg", "source_url": f"https://icon-sets.iconify.design/{name.replace(':', '/')}/", "creator": prefix, "license": licenses.get(prefix, ""), "license_url": f"https://api.iconify.design/collection?prefix={prefix}", "credit": f"{name} via Iconify", "provider": "iconify", "accessed_at": now_iso()})
    return output


def _wikimedia(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"action": "query", "generator": "search", "gsrsearch": query, "gsrnamespace": 6, "gsrlimit": min(limit, 20), "prop": "imageinfo", "iiprop": "url|extmetadata", "format": "json", "origin": "*"})
    payload = _get_json(f"https://commons.wikimedia.org/w/api.php?{params}")
    output = []
    for page in payload.get("query", {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        def value(key: str, metadata: dict[str, Any] = meta) -> str:
            return str((metadata.get(key) or {}).get("value", ""))
        output.append({"id": str(page.get("pageid")), "title": page.get("title", ""), "preview_url": info.get("thumburl") or info.get("url") or "", "download_url": info.get("url") or "", "source_url": info.get("descriptionurl") or "", "creator": value("Artist") or "Unknown", "license": value("LicenseShortName"), "license_url": value("LicenseUrl"), "credit": value("Credit"), "provider": "wikimedia", "accessed_at": now_iso()})
    return output[:limit]


def search_assets(provider: str, query: str, *, limit: int = 8, allow_network: bool = False) -> list[dict[str, Any]]:
    if limit < 1 or limit > 40:
        raise ValueError("limit必须在1到40之间")
    if provider == "mock":
        return _mock(query, limit)
    if not allow_network:
        raise ConnectorPermissionError("真实连接器需要显式allow_network=True或CLI --allow-network")
    handlers = {"openverse": _openverse, "pexels": _pexels, "iconify": _iconify, "wikimedia": _wikimedia}
    if provider not in handlers:
        raise ValueError(f"未知连接器：{provider}")
    return handlers[provider](query, limit)


def main() -> int:
    parser = argparse.ArgumentParser(description="统一素材源连接器（默认离线，显式授权后联网）")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    search = sub.add_parser("search")
    search.add_argument("--provider", choices=["mock", "openverse", "pexels", "iconify", "wikimedia"], default="mock")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=8)
    search.add_argument("--allow-network", action="store_true")
    search.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "list":
        print(json.dumps(registry(), ensure_ascii=False, indent=2))
        return 0
    try:
        payload = {"schema_version": "1.0", "provider": args.provider, "query": args.query, "searched_at": now_iso(), "results": search_assets(args.provider, args.query, limit=args.limit, allow_network=args.allow_network)}
    except (ConnectorPermissionError, ConnectorConfigError) as exc:
        raise SystemExit(str(exc)) from exc
    if args.output:
        write_json(args.output, payload)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
