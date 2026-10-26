from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from common import read_json, read_text, write_json, write_text  # noqa: E402
from publish_wechat import WeChatAPIError, api_json, multipart_file  # noqa: E402
from validate_package import validate  # noqa: E402

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit("self_test需要Pillow") from exc


SAMPLES = {
    "business": """# AI产品进入精细化运营阶段

过去一年，团队把增长目标从注册量调整为有效使用率。

数据显示，核心用户的七日留存率从21%提高到34%。这并不意味着所有功能都应该继续增加。

> 真正的增长来自用户反复完成关键任务。

- 先识别关键任务
- 再减少首次使用阻力
- 最后验证留存变化
""",
    "tutorial": """# 三步整理一篇长文章

第一步：确认文章只表达一个核心问题。

第二步：把证据、案例和结论放回正确顺序。

第三步：删除不能支撑核心问题的重复材料。
""",
    "lifestyle": """# 雨后的厨房

窗外的雨停了，木桌上还留着一圈杯底的水痕。

我把刚烤好的面包切开，热气让清晨慢了下来。

这样的日常没有答案，却让人重新看见生活的纹理。
""",
}


def run_script(name: str, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT_DIR / name), *args]
    return subprocess.run(command, text=True, capture_output=True, env=env, timeout=90)


def build_sample(root: Path, key: str) -> Path:
    source = root / f"{key}.md"
    write_text(source, SAMPLES[key])
    output = root / f"package-{key}"
    result = run_script("build_package.py", "--input", str(source), "--output-dir", str(output))
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return output


class MockWeChatHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args) -> None:
        return

    def _json(self, payload: dict, code: int = 200) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.startswith("/cgi-bin/token"):
            self._json({"access_token": "mock-token", "expires_in": 7200})
        elif self.path.startswith("/error-token"):
            self._json({"errcode": 40014, "errmsg": "invalid access_token"})
        elif self.path.startswith("/error-ip"):
            self._json({"errcode": 40164, "errmsg": "invalid ip"})
        else:
            self._json({"errcode": 404, "errmsg": "not found"}, 404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        if self.path.startswith("/cgi-bin/media/uploadimg"):
            if "fail=1" in self.path:
                self._json({"errcode": 40007, "errmsg": "invalid media"})
            else:
                self._json({"url": "https://mmbiz.qpic.cn/mock/inline/0"})
        elif self.path.startswith("/cgi-bin/material/add_material"):
            self._json({"media_id": "mock-cover-media", "url": "https://mmbiz.qpic.cn/mock/cover/0"})
        elif self.path.startswith("/cgi-bin/draft/add"):
            payload = json.loads(body.decode("utf-8"))
            content = payload["articles"][0]["content"]
            if "mmbiz.qpic.cn" not in content:
                self._json({"errcode": 40007, "errmsg": "invalid media"})
            else:
                self._json({"media_id": "mock-draft-media"})
        else:
            self._json({"errcode": 404, "errmsg": "not found"}, 404)


class SkillTests(unittest.TestCase):
    def test_three_tracks_generate_different_designs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            concepts = []
            for key in SAMPLES:
                package = build_sample(root, key)
                result = validate(package)
                self.assertTrue(result["ok"], result)
                concepts.append(read_json(package / "article-package.json")["design"]["concept"])
            self.assertEqual(3, len(set(concepts)))

    def test_missing_or_reordered_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            package = build_sample(Path(temp), "tutorial")
            write_text(package / "article-fragment.html", '<section style="color:#262626;background-color:#ffffff;"><p style="margin:0;">第三步：删除不能支撑核心问题的重复材料。</p></section>')
            result = validate(package)
            self.assertFalse(result["ok"])
            self.assertTrue(any("未按顺序完整出现" in item for item in result["errors"]))

    def test_html_source_is_read_as_article_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "article.html"
            write_text(source, "<h1>HTML原稿</h1><p>第一段包含<strong>重点</strong>。</p><blockquote>一条引用。</blockquote><ul><li>清单项目</li></ul>")
            output = root / "html-package"
            result = run_script("build_package.py", "--input", str(source), "--output-dir", str(output))
            self.assertEqual(0, result.returncode, result.stderr)
            fragment = read_text(output / "article-fragment.html")
            self.assertIn("HTML原稿", fragment)
            self.assertIn("第一段包含重点。", fragment)
            self.assertNotIn("&lt;h1&gt;", fragment)
            self.assertTrue(validate(output)["ok"])

    def test_custom_fragment_requires_change_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.md"
            fragment = root / "fragment.html"
            write_text(source, "# 标题\n\n正文。\n")
            write_text(fragment, '<section style="color:#262626;"><p style="margin:0;">标题</p><p style="margin:0;">正文。</p></section>')
            result = run_script("build_package.py", "--input", str(source), "--fragment", str(fragment), "--output-dir", str(root / "package"))
            self.assertNotEqual(0, result.returncode)
            self.assertIn("--changes", result.stderr)

    def test_banned_css_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            package = build_sample(Path(temp), "lifestyle")
            fragment = read_text(package / "article-fragment.html").replace("padding:22px 16px", "display:flex;padding:22px 16px")
            write_text(package / "article-fragment.html", fragment)
            result = validate(package)
            self.assertFalse(result["ok"])
            self.assertTrue(any("Flex" in item for item in result["errors"]))

    def test_preview_has_rich_clipboard_and_modes(self) -> None:
        shell = read_text(SKILL_DIR / "assets" / "preview-shell.html")
        self.assertIn("ClipboardItem", shell)
        self.assertIn("text/html", shell)
        self.assertIn('data-width="375"', shell)
        self.assertIn('data-width="430"', shell)
        self.assertIn('data-mode="dark"', shell)

    def test_local_preview_server_uses_loopback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            package = build_sample(Path(temp), "lifestyle")
            result = run_script("serve_preview.py", str(package), "--no-open", "--duration", "0.2")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertRegex(result.stdout, r"http://127\.0\.0\.1:\d+/preview\.html")

    def test_svg_rasterization(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            svg = root / "source.svg"
            png = root / "result.png"
            write_text(svg, '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="80"><rect width="320" height="80" fill="#eef4f1"/><circle cx="160" cy="40" r="24" fill="#315f58"/></svg>')
            result = run_script("rasterize_svg.py", str(svg), str(png), "--width", "320", "--height", "80")
            self.assertEqual(0, result.returncode, result.stderr + result.stdout)
            with Image.open(png) as image:
                self.assertEqual((320, 80), image.size)

    def test_asset_variants_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            package = build_sample(root, "business")
            source = root / "source.png"
            Image.new("RGB", (1600, 1000), (80, 110, 103)).save(source)
            result = run_script("prepare_assets.py", "--input", str(source), "--output-dir", str(package / "assets"), "--manifest", str(package / "article-package.json"), "--provider", "original", "--license", "Original asset")
            self.assertEqual(0, result.returncode, result.stderr)
            expected = {"cover-main.jpg": (900, 383), "guide-wide.jpg": (900, 500), "cover-square.jpg": (900, 900)}
            for name, size in expected.items():
                path = package / "assets" / name
                self.assertTrue(path.exists())
                with Image.open(path) as image:
                    self.assertEqual(size, image.size)
                self.assertLess(path.stat().st_size, 950 * 1024)

    def test_mock_wechat_reports_token_and_ip_errors(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), MockWeChatHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            with self.assertRaises(WeChatAPIError) as token_error:
                api_json(base + "/error-token")
            self.assertEqual(40014, token_error.exception.payload["errcode"])
            with self.assertRaises(WeChatAPIError) as ip_error:
                api_json(base + "/error-ip")
            self.assertEqual(40164, ip_error.exception.payload["errcode"])
            with tempfile.TemporaryDirectory() as temp:
                image_path = Path(temp) / "fail.png"
                Image.new("RGB", (40, 40), (100, 120, 110)).save(image_path)
                with self.assertRaises(WeChatAPIError) as upload_error:
                    multipart_file(base + "/cgi-bin/media/uploadimg?fail=1", "media", image_path)
                self.assertEqual(40007, upload_error.exception.payload["errcode"])
        finally:
            server.shutdown()
            server.server_close()

    def test_mock_wechat_draft_flow_and_pending_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.md"
            write_text(source, "# 测试草稿\n\n这是一段不会被改写的正文。\n")
            inline = root / "inline.png"
            Image.new("RGB", (600, 360), (100, 130, 120)).save(inline, optimize=True)
            fragment = root / "fragment.html"
            write_text(fragment, '<section style="color:#263a39;background-color:#eef4f1;padding:16px;"><p style="margin:0 0 18px;font-size:22px;">测试草稿</p><p style="margin:0 0 18px;font-size:15px;">这是一段不会被改写的正文。</p><img src="assets/inline.png" alt="测试图" style="display:block;width:100%;height:auto;margin:0;" /></section>')
            changes = root / "changes.md"
            write_text(changes, "# 结构改动清单\n\n- 图片插入：在正文后加入测试图。\n")
            package = root / "package"
            built = run_script("build_package.py", "--input", str(source), "--fragment", str(fragment), "--changes", str(changes), "--output-dir", str(package))
            self.assertEqual(0, built.returncode, built.stderr)
            shutil_inline = package / "assets" / "inline.png"
            shutil_inline.write_bytes(inline.read_bytes())
            Image.new("RGB", (900, 383), (50, 75, 70)).save(package / "assets" / "cover-main.jpg", quality=85)
            manifest = read_json(package / "article-package.json")
            manifest["assets"] = [
                {"id": "inline-01", "role": "inline", "local_path": "assets/inline.png", "provider": "original", "creator": "", "source_url": "", "license": "Original asset", "license_url": "", "credit": "original", "accessed_at": "2026-07-24", "modifications": "none", "wechat_url": ""},
                {"id": "cover-main", "role": "cover", "local_path": "assets/cover-main.jpg", "provider": "original", "creator": "", "source_url": "", "license": "Original asset", "license_url": "", "credit": "original", "accessed_at": "2026-07-24", "modifications": "none", "wechat_url": ""},
            ]
            write_json(package / "article-package.json", manifest)

            server = ThreadingHTTPServer(("127.0.0.1", 0), MockWeChatHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                env = os.environ.copy()
                env.update({"WECHAT_APP_ID": f"test-{uuid.uuid4().hex}", "WECHAT_APP_SECRET": "not-a-real-secret", "WECHAT_API_BASE": f"http://127.0.0.1:{server.server_port}"})
                result = run_script("publish_wechat.py", str(package), "--commit", env=env)
                self.assertEqual(0, result.returncode, result.stderr + result.stdout)
                published = read_json(package / "publish-result.json")
                self.assertEqual("mock-draft-media", published["media_id"])
                self.assertNotIn("not-a-real-secret", read_text(package / "publish-result.json"))
                write_json(package / "publish-pending.json", {"status": "unknown"})
                blocked = run_script("publish_wechat.py", str(package), "--commit", env=env)
                self.assertNotEqual(0, blocked.returncode)
                self.assertIn("禁止自动重试", blocked.stderr + blocked.stdout)
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
