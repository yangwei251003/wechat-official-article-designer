from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from common import now_iso, write_json, write_text


def render_mock_chart(spec: dict[str, Any], output: Path, *, width: int = 900, height: int = 520) -> dict[str, Any]:
    labels = [str(item) for item in spec.get("labels", [])]
    values = [float(item) for item in spec.get("values", [])]
    if not labels or len(labels) != len(values) or len(values) > 20:
        raise ValueError("Mock图表需要1-20个等长labels/values")
    if width < 320 or height < 240 or width > 2400 or height > 1600:
        raise ValueError("图表尺寸超出安全范围")
    maximum = max(max(values), 1)
    chart_left, chart_top, chart_width, chart_height = 90, 90, width - 140, height - 170
    band = chart_width / len(values)
    bars = []
    for index, (label, value) in enumerate(zip(labels, values, strict=False)):
        bar_height = max(0, value) / maximum * chart_height
        x = chart_left + index * band + band * 0.2
        y = chart_top + chart_height - bar_height
        bar_width = band * 0.6
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" rx="8" fill="#5E827D"/><text x="{x+bar_width/2:.1f}" y="{y-10:.1f}" text-anchor="middle" font-size="24" fill="#263A39">{html.escape(f"{value:g}")}</text><text x="{x+bar_width/2:.1f}" y="{chart_top+chart_height+36:.1f}" text-anchor="middle" font-size="22" fill="#263A39">{html.escape(label)}</text>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="#EEF4F1"/><text x="{chart_left}" y="52" font-size="30" font-weight="700" fill="#263A39">{html.escape(str(spec.get("title", "数据图表")))}</text><line x1="{chart_left}" y1="{chart_top+chart_height}" x2="{chart_left+chart_width}" y2="{chart_top+chart_height}" stroke="#9EB7B2" stroke-width="2"/>{"".join(bars)}</svg>'
    output.parent.mkdir(parents=True, exist_ok=True)
    write_text(output, svg + "\n")
    return {"engine": "mock", "output": str(output), "generated_at": now_iso(), "static": True, "warning": "Mock渲染用于可重复测试，不等同于ECharts/Mermaid/Vega-Lite真实渲染"}


def render_mermaid(source: Path, output: Path) -> dict[str, Any]:
    command = shutil.which("mmdc")
    if not command:
        raise RuntimeError("未找到Mermaid CLI；保留.mmd源并使用Mock/手工静态降级")
    completed = subprocess.run([command, "-i", str(source), "-o", str(output), "--securityLevel", "strict"], capture_output=True, text=True, timeout=60)
    if completed.returncode:
        raise RuntimeError("Mermaid渲染失败")
    return {"engine": "mermaid", "output": str(output), "generated_at": now_iso(), "static": True}


def main() -> int:
    parser = argparse.ArgumentParser(description="把图表规范渲染为微信可用静态图；真实引擎缺失时清晰降级")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--engine", choices=["mock", "mermaid"], default="mock")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.engine == "mock":
        result = render_mock_chart(json.loads(args.input.read_text(encoding="utf-8")), args.output)
    else:
        result = render_mermaid(args.input, args.output)
    if args.report:
        write_json(args.report, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
