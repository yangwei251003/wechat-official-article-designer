from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def find_browser() -> str | None:
    candidates = [
        shutil.which("chrome"), shutil.which("msedge"), shutil.which("chromium"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="把SVG栅格化为微信公众号可用PNG")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=180)
    args = parser.parse_args()
    if args.width < 1 or args.height < 1:
        raise SystemExit("width/height 必须大于0")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(url=str(args.input.resolve()), write_to=str(args.output.resolve()), output_width=args.width, output_height=args.height)
        return 0
    except (ImportError, OSError):
        pass

    browser = find_browser()
    if not browser:
        raise SystemExit("未找到cairosvg或Chrome/Edge，无法栅格化SVG")
    svg_uri = args.input.resolve().as_uri()
    with tempfile.TemporaryDirectory(prefix="wechat-svg-") as temp:
        wrapper = Path(temp) / "render.html"
        wrapper.write_text(
            f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;width:{args.width}px;height:{args.height}px;overflow:hidden;background:transparent}}img{{display:block;width:{args.width}px;height:{args.height}px}}</style><img src="{svg_uri}">',
            encoding="utf-8",
        )
        command = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", f"--window-size={args.width},{args.height}", f"--screenshot={args.output.resolve()}", wrapper.resolve().as_uri()]
        result = subprocess.run(command, capture_output=True, text=True, timeout=45)
        if result.returncode != 0 or not args.output.exists():
            raise SystemExit(f"浏览器栅格化失败：{result.stderr.strip() or result.stdout.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
