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


def rasterize_svg(input_path: Path, output_path: Path, *, width: int = 1080, height: int = 180) -> None:
    if width < 1 or height < 1:
        raise ValueError("width/height 必须大于0")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import cairosvg  # type: ignore

        cairosvg.svg2png(url=str(input_path.resolve()), write_to=str(output_path.resolve()), output_width=width, output_height=height)
        return
    except (ImportError, OSError):
        pass
    browser = find_browser()
    if not browser:
        raise RuntimeError("未找到cairosvg或Chrome/Edge，无法栅格化SVG")
    svg_uri = input_path.resolve().as_uri()
    with tempfile.TemporaryDirectory(prefix="wechat-svg-") as temp:
        wrapper = Path(temp) / "render.html"
        wrapper.write_text(
            f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden;background:transparent}}img{{display:block;width:{width}px;height:{height}px}}</style><img src="{svg_uri}">',
            encoding="utf-8",
        )
        command = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1", f"--window-size={width},{height}", f"--screenshot={output_path.resolve()}", wrapper.resolve().as_uri()]
        result = subprocess.run(command, capture_output=True, text=True, timeout=45, check=False)
        if result.returncode != 0 or not output_path.exists():
            raise RuntimeError(f"浏览器栅格化失败：{result.stderr.strip() or result.stdout.strip()}")


def main() -> int:
    parser = argparse.ArgumentParser(description="把SVG栅格化为微信公众号可用PNG")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=180)
    args = parser.parse_args()
    try:
        rasterize_svg(args.input, args.output, width=args.width, height=args.height)
        return 0
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    raise SystemExit(main())
