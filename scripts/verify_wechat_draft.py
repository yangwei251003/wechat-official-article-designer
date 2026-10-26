from __future__ import annotations

import argparse
import json
import os
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from common import read_json, write_json
from publish_wechat import DEFAULT_API_BASE, api_json, get_token, is_wechat_media_url


class DraftImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        data = dict(attrs)
        for key in ("src", "data-src", "data-original-src"):
            if data.get(key):
                self.images.append({"key": key, "url": str(data[key])})
                return
        self.images.append({"key": "", "url": ""})


def inspect_draft_payload(payload: dict[str, Any], expected_title: str) -> dict[str, Any]:
    items = payload.get("news_item") or []
    article = items[0] if items else {}
    content = str(article.get("content", ""))
    parser = DraftImageParser()
    parser.feed(content)
    report = {
        "draft_found": bool(items),
        "title_matches": article.get("title") == expected_title,
        "inline_image_count": len(parser.images),
        "all_inline_images_wechat_hosted": bool(parser.images) and all(is_wechat_media_url(item["url"]) for item in parser.images),
        "image_attribute_keys": [item["key"] for item in parser.images],
        "image_hosts": [urlparse(item["url"]).hostname or "" for item in parser.images],
        "local_asset_reference_remaining": "assets/" in content,
        "cover_url_present": bool(article.get("thumb_url") or article.get("thumb_media_id")),
    }
    report["ok"] = all([report["draft_found"], report["title_matches"], report["all_inline_images_wechat_hosted"], not report["local_asset_reference_remaining"], report["cover_url_present"]])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="只读核验真实微信公众号草稿是否已完成图片转存和内容写入")
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("--media-id", help="默认读取 package/publish-result.json")
    parser.add_argument("--output", type=Path, help="默认写入 package/draft-verification.json")
    args = parser.parse_args()
    package_dir = args.package_dir.resolve()
    package = read_json(package_dir / "article-package.json")
    result = read_json(package_dir / "publish-result.json") if not args.media_id else {}
    media_id = args.media_id or str(result.get("media_id", ""))
    if not media_id:
        raise SystemExit("缺少草稿 media_id；请先创建草稿或传入 --media-id")
    app_id = os.environ.get("WECHAT_APP_ID")
    app_secret = os.environ.get("WECHAT_APP_SECRET")
    if not app_id or not app_secret:
        raise SystemExit("核验前必须通过环境变量设置 WECHAT_APP_ID 和 WECHAT_APP_SECRET")
    token = get_token(DEFAULT_API_BASE, app_id, app_secret)
    payload = api_json(f"{DEFAULT_API_BASE}/cgi-bin/draft/get?access_token={token}", method="POST", body={"media_id": media_id})
    report = inspect_draft_payload(payload, str(package.get("title", "")))
    output = args.output or package_dir / "draft-verification.json"
    write_json(output, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
