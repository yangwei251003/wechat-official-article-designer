from __future__ import annotations

import argparse
import functools
import http.server
import threading
import webbrowser
from pathlib import Path


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return


def main() -> int:
    parser = argparse.ArgumentParser(description="通过仅本机可访问的HTTP服务打开公众号预览，保证剪贴板权限稳定")
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("--port", type=int, default=0, help="默认自动选择空闲端口")
    parser.add_argument("--no-open", action="store_true", help="只输出URL，不自动打开浏览器")
    parser.add_argument("--duration", type=float, help=argparse.SUPPRESS)
    args = parser.parse_args()
    package_dir = args.package_dir.resolve()
    preview = package_dir / "preview.html"
    if not preview.exists():
        raise SystemExit("文章包中缺少preview.html")
    handler = functools.partial(QuietHandler, directory=str(package_dir))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    url = f"http://127.0.0.1:{server.server_port}/preview.html"
    print(url, flush=True)
    if not args.no_open:
        webbrowser.open(url)
    if args.duration:
        threading.Timer(args.duration, server.shutdown).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

