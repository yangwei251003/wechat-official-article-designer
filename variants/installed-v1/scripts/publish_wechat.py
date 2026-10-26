from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from common import now_iso, parse_fragment, read_json, read_text, write_json, write_text
from validate_package import validate


DEFAULT_API_BASE = "https://api.weixin.qq.com"


class WeChatAPIError(RuntimeError):
    def __init__(self, message: str, payload: dict | None = None) -> None:
        super().__init__(message)
        self.payload = payload or {}


def api_json(url: str, *, method: str = "GET", body: dict | None = None, timeout: int = 35) -> dict:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "wechat-official-article-designer/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("errcode") not in (None, 0):
        raise WeChatAPIError(f"微信API错误 {payload.get('errcode')}: {payload.get('errmsg', '')}", payload)
    return payload


def multipart_file(url: str, field: str, path: Path, timeout: int = 60) -> dict:
    boundary = f"----wechat-{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    head = f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{path.name}\"\r\nContent-Type: {content_type}\r\n\r\n".encode()
    body = head + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": "wechat-official-article-designer/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("errcode") not in (None, 0):
        raise WeChatAPIError(f"微信API错误 {payload.get('errcode')}: {payload.get('errmsg', '')}", payload)
    return payload


def token_cache_path(app_id: str) -> Path:
    key = hashlib.sha256(app_id.encode()).hexdigest()[:12]
    root = Path(tempfile.gettempdir()) / "wechat-official-article-designer"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"token-{key}.json"


def get_token(api_base: str, app_id: str, app_secret: str) -> str:
    cache = token_cache_path(app_id)
    if cache.exists():
        payload = read_json(cache)
        if payload.get("expires_at", 0) > time.time() + 180 and payload.get("access_token"):
            return payload["access_token"]
    query = urllib.parse.urlencode({"grant_type": "client_credential", "appid": app_id, "secret": app_secret})
    payload = api_json(f"{api_base}/cgi-bin/token?{query}")
    token = payload.get("access_token")
    if not token:
        raise WeChatAPIError("微信未返回access_token", payload)
    write_json(cache, {"access_token": token, "expires_at": time.time() + int(payload.get("expires_in", 7200))})
    return token


def local_image_sources(fragment: str) -> list[str]:
    return [src for src in parse_fragment(fragment).images if src and not re.match(r"^https?://", src, re.I)]


def replace_image_src(fragment: str, mapping: dict[str, str]) -> str:
    pattern = re.compile(r"(<img\b[^>]*?\bsrc\s*=\s*)([\"'])(.*?)(\2)", re.I | re.S)
    return pattern.sub(lambda match: f"{match.group(1)}{match.group(2)}{mapping.get(match.group(3), match.group(3))}{match.group(4)}", fragment)


def preflight(package_dir: Path) -> tuple[dict, str, dict[str, dict]]:
    result = validate(package_dir)
    if not result["ok"]:
        raise SystemExit("文章包校验失败，拒绝发布：\n" + "\n".join(result["errors"]))
    package = read_json(package_dir / "article-package.json")
    fragment = read_text(package_dir / package.get("fragment_file", "article-fragment.html"))
    assets = {item.get("id"): item for item in package.get("assets", [])}
    cover_id = package.get("publishing", {}).get("cover_asset_id")
    if not cover_id or cover_id not in assets:
        raise SystemExit("未登记封面素材，无法创建微信草稿")
    cover_path = package_dir / assets[cover_id]["local_path"]
    if not cover_path.exists() or cover_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        raise SystemExit("封面必须是存在的JPG/PNG文件")
    for src in local_image_sources(fragment):
        path = package_dir / src.replace("/", os.sep)
        if not path.exists() or path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            raise SystemExit(f"正文图片必须是存在的JPG/PNG文件：{src}")
        if path.stat().st_size >= 1024 * 1024:
            raise SystemExit(f"正文图片必须小于1MB：{src}")
    return package, fragment, assets


def main() -> int:
    parser = argparse.ArgumentParser(description="安全上传图片并创建微信公众号草稿；默认只干跑")
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("--commit", action="store_true", help="实际创建草稿；只在用户明确同意后使用")
    parser.add_argument("--clear-pending", action="store_true", help="人工核对后台后清除未知状态锁")
    parser.add_argument("--api-base", default=os.environ.get("WECHAT_API_BASE", DEFAULT_API_BASE), help=argparse.SUPPRESS)
    args = parser.parse_args()
    package_dir = args.package_dir.resolve()
    pending_path = package_dir / "publish-pending.json"
    if args.clear_pending:
        if pending_path.exists():
            pending_path.unlink()
            print("pending状态已清除；请确认后台没有重复草稿后再提交。")
        else:
            print("没有pending状态。")
        return 0
    if pending_path.exists():
        raise SystemExit("存在publish-pending.json：上次草稿请求状态未知。请先到微信后台核对，禁止自动重试。")

    package, fragment, assets = preflight(package_dir)
    local_sources = local_image_sources(fragment)
    print(json.dumps({"mode": "commit" if args.commit else "dry-run", "title": package.get("title"), "inline_images": len(local_sources), "cover_asset_id": package["publishing"]["cover_asset_id"]}, ensure_ascii=False))
    if not args.commit:
        print("DRY RUN PASS：未连接微信、未上传图片、未创建草稿。")
        return 0

    app_id = os.environ.get("WECHAT_APP_ID")
    app_secret = os.environ.get("WECHAT_APP_SECRET")
    if not app_id or not app_secret:
        raise SystemExit("提交前必须设置 WECHAT_APP_ID 和 WECHAT_APP_SECRET")
    if not args.api_base.startswith("https://") and not re.match(r"^http://(?:127\.0\.0\.1|localhost)(?::\d+)?$", args.api_base):
        raise SystemExit("api-base必须使用HTTPS；仅本地测试服务器允许HTTP")

    token = get_token(args.api_base, app_id, app_secret)
    image_mapping: dict[str, str] = {}
    for src in local_sources:
        path = package_dir / src.replace("/", os.sep)
        query = urllib.parse.urlencode({"access_token": token})
        response = multipart_file(f"{args.api_base}/cgi-bin/media/uploadimg?{query}", "media", path)
        if not response.get("url"):
            raise WeChatAPIError(f"正文图片上传没有返回URL：{src}", response)
        image_mapping[src] = response["url"]
    wechat_fragment = replace_image_src(fragment, image_mapping)
    remaining = [src for src in parse_fragment(wechat_fragment).images if not re.match(r"^https://(?:mmbiz\.qpic\.cn|mmbiz\.qlogo\.cn)/", src, re.I)]
    if remaining:
        raise SystemExit("上传后正文仍含非微信图片，拒绝创建草稿：" + ", ".join(remaining))

    cover_asset = assets[package["publishing"]["cover_asset_id"]]
    cover_path = package_dir / cover_asset["local_path"]
    query = urllib.parse.urlencode({"access_token": token, "type": "image"})
    cover_response = multipart_file(f"{args.api_base}/cgi-bin/material/add_material?{query}", "media", cover_path)
    thumb_media_id = cover_response.get("media_id")
    if not thumb_media_id:
        raise WeChatAPIError("封面上传没有返回media_id", cover_response)

    publishing = package.get("publishing", {})
    article = {
        "title": package.get("title", ""), "author": publishing.get("author", ""), "digest": publishing.get("digest", ""),
        "content": wechat_fragment, "content_source_url": publishing.get("content_source_url", ""), "thumb_media_id": thumb_media_id,
        "show_cover_pic": 0, "need_open_comment": int(publishing.get("need_open_comment", 1)), "only_fans_can_comment": int(publishing.get("only_fans_can_comment", 0)),
    }
    payload = {"articles": [article]}
    fingerprint = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    write_json(pending_path, {"created_at": now_iso(), "fingerprint": fingerprint, "title": package.get("title"), "status": "request_not_confirmed"})
    query = urllib.parse.urlencode({"access_token": token})
    try:
        response = api_json(f"{args.api_base}/cgi-bin/draft/add?{query}", method="POST", body=payload, timeout=45)
    except WeChatAPIError:
        pending_path.unlink(missing_ok=True)
        raise
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        package.setdefault("publishing", {})["status"] = "pending_unknown"
        write_json(package_dir / "article-package.json", package)
        raise SystemExit(f"草稿请求状态未知，已保留pending锁且不会自动重试：{type(exc).__name__}") from exc
    pending_path.unlink(missing_ok=True)
    media_id = response.get("media_id")
    if not media_id:
        raise WeChatAPIError("创建草稿成功响应中没有media_id", response)
    package.setdefault("publishing", {})["status"] = "draft_created"
    write_json(package_dir / "article-package.json", package)
    write_json(package_dir / "publish-result.json", {"created_at": now_iso(), "status": "draft_created", "media_id": media_id, "thumb_media_id": thumb_media_id, "image_mapping": image_mapping, "fingerprint": fingerprint})
    print(json.dumps({"status": "draft_created", "media_id": media_id, "images": len(image_mapping)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WeChatAPIError as exc:
        print(str(exc))
        raise SystemExit(2)

