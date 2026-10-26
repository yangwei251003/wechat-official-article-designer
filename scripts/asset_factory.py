from __future__ import annotations

import argparse
import hashlib
import html
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from common import now_iso, read_json, write_json, write_text

try:
    from PIL import Image, ImageDraw
except ImportError as exc:
    raise SystemExit("asset_factory需要Pillow") from exc


def derive_motif(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["用户研究", "访谈", "观察", "实验", "假设", "证据", "洞察"]):
        return "signal-lens"
    if any(word in lowered for word in ["儿童", "亲子", "节日", "手作", "校园"]):
        return "kinetic-cutouts"
    if any(word in lowered for word in ["商业", "科技", "ai", "数据", "增长", "产品"]):
        return "system-pulse"
    if any(word in lowered for word in ["人物", "访谈", "口述", "人生", "故事"]):
        return "human-trace"
    if any(word in lowered for word in ["生活", "旅行", "美食", "咖啡", "花", "季节", "自然"]):
        return "field-notes"
    return "concept-prism"


def _hex(value: str, fallback: str) -> str:
    value = value.strip()
    return value if len(value) == 7 and value.startswith("#") else fallback


def _rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _source_svg(motif: str, palette: list[str]) -> str:
    background, primary, accent = palette
    if motif == "signal-lens":
        shapes = f'''<g opacity=".22" stroke="{accent}" stroke-width="1"><path d="M58 78H842M58 172H842M58 266H842M58 360H842M58 454H842"/><path d="M130 36V464M290 36V464M450 36V464M610 36V464M770 36V464"/></g><circle cx="650" cy="245" r="172" fill="none" stroke="{primary}" stroke-width="42" opacity=".92"/><circle cx="650" cy="245" r="112" fill="{accent}" opacity=".10"/><path d="M54 388 C205 375 234 116 386 188 S555 412 846 104" fill="none" stroke="{accent}" stroke-width="8" stroke-linecap="round"/><circle r="14" fill="{primary}"><animateMotion dur="5.5s" repeatCount="indefinite" path="M54 388 C205 375 234 116 386 188 S555 412 846 104"/></circle><path d="M520 402L760 88" stroke="{primary}" stroke-width="2" opacity=".55"><animate attributeName="opacity" values=".18;.8;.18" dur="2.7s" repeatCount="indefinite"/></path>'''
    elif motif == "system-pulse":
        shapes = f'''<path d="M70 348H250L320 132H486L548 308H830" fill="none" stroke="{accent}" stroke-width="10" stroke-linejoin="bevel"/><g fill="none" stroke="{primary}" stroke-width="3"><rect x="70" y="82" width="220" height="110" rx="18"/><rect x="590" y="294" width="240" height="112" rx="18"/></g><circle cx="320" cy="132" r="20" fill="{primary}"><animate attributeName="r" values="12;24;12" dur="2.2s" repeatCount="indefinite"/></circle><circle cx="548" cy="308" r="15" fill="{primary}"/>'''
    elif motif == "kinetic-cutouts":
        shapes = f'''<path d="M70 90L360 48L300 318L42 384Z" fill="{primary}"/><circle cx="632" cy="182" r="138" fill="{accent}"/><path d="M450 462L842 234L842 462Z" fill="{primary}" opacity=".78"/><rect x="387" y="86" width="92" height="92" fill="{background}" stroke="{accent}" stroke-width="12"><animateTransform attributeName="transform" type="rotate" values="0 433 132;12 433 132;0 433 132" dur="4s" repeatCount="indefinite"/></rect>'''
    elif motif == "human-trace":
        shapes = f'''<path d="M170 426 C208 232 176 110 334 74 C470 44 530 156 506 260 C486 354 562 412 720 420" fill="none" stroke="{primary}" stroke-width="48" stroke-linecap="round"/><path d="M128 384 C322 336 572 350 808 118" fill="none" stroke="{accent}" stroke-width="7"/><circle cx="580" cy="208" r="25" fill="{accent}"><animate attributeName="opacity" values=".25;1;.25" dur="3s" repeatCount="indefinite"/></circle>'''
    elif motif == "field-notes":
        contours = "".join(f'<path d="M40 {90+i*54} C210 {25+i*60} 335 {180+i*25} 500 {105+i*48} S720 {40+i*62} 870 {110+i*48}" fill="none" stroke="{primary}" stroke-width="{2+i%2}" opacity="{.25+i*.07:.2f}"/>' for i in range(6))
        shapes = contours + f'<path d="M604 424C592 306 650 194 772 72M660 312C712 292 752 254 782 202M646 246C608 218 588 184 580 144" fill="none" stroke="{accent}" stroke-width="9" stroke-linecap="round"/>'
    else:
        shapes = f'''<path d="M38 420L318 42L512 420Z" fill="{primary}"/><path d="M262 420L538 82L862 420Z" fill="none" stroke="{accent}" stroke-width="24"/><path d="M390 62L470 438" stroke="{background}" stroke-width="6" opacity=".75"><animateTransform attributeName="transform" type="translate" values="-40 0;120 0;-40 0" dur="6s" repeatCount="indefinite"/></path>'''
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="500" viewBox="0 0 900 500"><rect width="900" height="500" fill="{background}"/>{shapes}</svg>'


def _scaled_canvas(size: tuple[int, int]) -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    scale = 2
    image = Image.new("RGB", (size[0] * scale, size[1] * scale))
    return image, ImageDraw.Draw(image), scale


def _finish(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return image.resize(size, Image.Resampling.LANCZOS)


def _line(draw: ImageDraw.ImageDraw, points: Sequence[tuple[float, float]], *, fill: tuple[int, int, int], width: int, scale: int) -> None:
    draw.line([(int(x * scale), int(y * scale)) for x, y in points], fill=fill, width=width * scale, joint="curve")


def _draw_frame(size: tuple[int, int], motif: str, palette: list[str], frame: int, frames: int) -> Image.Image:
    image, draw, scale = _scaled_canvas(size)
    draw.rectangle((0, 0, size[0] * scale, size[1] * scale), fill=_rgb(palette[0]))
    width, height = size
    seed = hashlib.sha256(motif.encode("utf-8")).digest()
    progress = frame / frames
    if motif == "signal-lens":
        for grid_x in range(60, width, 145):
            _line(draw, [(grid_x, 36), (grid_x, height - 36)], fill=_rgb(palette[2]), width=1, scale=scale)
        for grid_y in range(58, height, 92):
            _line(draw, [(46, grid_y), (width - 46, grid_y)], fill=_rgb(palette[2]), width=1, scale=scale)
        cx, cy, radius = int(width * .72), int(height * .49), int(height * .34)
        draw.ellipse(tuple(v * scale for v in (cx-radius, cy-radius, cx+radius, cy+radius)), outline=_rgb(palette[1]), width=38 * scale)
        draw.ellipse(tuple(v * scale for v in (cx-radius+55, cy-radius+55, cx+radius-55, cy+radius-55)), outline=_rgb(palette[2]), width=3 * scale)
        signal_points: list[tuple[float, float]] = []
        for sample_x in range(45, width - 35, 7):
            signal_y = height * .68 - math.sin(sample_x / width * math.pi * 3.1) * height * .18 - (sample_x / width) * height * .22
            signal_points.append((sample_x, signal_y))
        _line(draw, signal_points, fill=_rgb(palette[2]), width=7, scale=scale)
        dot_index = min(len(signal_points)-1, int(progress * len(signal_points)))
        dx, dy = signal_points[dot_index]
        r = 14
        draw.ellipse(tuple(int(v * scale) for v in (dx-r, dy-r, dx+r, dy+r)), fill=_rgb(palette[1]))
    elif motif == "system-pulse":
        pulse_points = [(52, height*.7), (230, height*.7), (300, height*.25), (470, height*.25), (545, height*.64), (width-50, height*.64)]
        _line(draw, pulse_points, fill=_rgb(palette[2]), width=10, scale=scale)
        for index, (pulse_x, pulse_y) in enumerate(pulse_points[1:-1], 1):
            r = 10 + (10 if index == int(progress * 4) + 1 else 0)
            draw.ellipse(tuple(int(v*scale) for v in (pulse_x-r,pulse_y-r,pulse_x+r,pulse_y+r)), fill=_rgb(palette[1]))
        draw.rounded_rectangle(tuple(v*scale for v in (70,70,280,185)), radius=18*scale, outline=_rgb(palette[1]), width=3*scale)
        draw.rounded_rectangle(tuple(v*scale for v in (600,300,842,414)), radius=18*scale, outline=_rgb(palette[1]), width=3*scale)
    elif motif == "kinetic-cutouts":
        wobble = int(math.sin(progress * math.pi * 2) * 18)
        draw.polygon([(50*scale,95*scale),((355+wobble)*scale,42*scale),(295*scale,330*scale),(42*scale,392*scale)], fill=_rgb(palette[1]))
        draw.ellipse(tuple(v*scale for v in (505,58,790,343)), fill=_rgb(palette[2]))
        draw.polygon([(420*scale,470*scale),(850*scale,225*scale),(850*scale,470*scale)], fill=_rgb(palette[1]))
    elif motif == "human-trace":
        trace_points = [(175,430),(205,295),(188,160),(335,72),(485,88),(525,228),(500,338),(720,424)]
        _line(draw, trace_points, fill=_rgb(palette[1]), width=42, scale=scale)
        _line(draw, [(110,386),(330,334),(555,350),(815,112)], fill=_rgb(palette[2]), width=7, scale=scale)
        r=13+int(8*(1+math.sin(progress*math.pi*2)))
        draw.ellipse(tuple(v*scale for v in (580-r,205-r,580+r,205+r)),fill=_rgb(palette[2]))
    elif motif == "field-notes":
        for i in range(7):
            contour_points: list[tuple[float, float]]=[]
            for contour_x in range(35,width-20,15):
                contour_y=80+i*54+math.sin(contour_x/95+i*.8+progress*.7)*30
                contour_points.append((contour_x,contour_y))
            _line(draw,contour_points,fill=_rgb(palette[1]),width=2+(i%2),scale=scale)
        _line(draw,[(610,440),(620,320),(675,210),(790,64)],fill=_rgb(palette[2]),width=9,scale=scale)
    else:
        shift=int(math.sin(progress*math.pi*2)*35)
        draw.polygon([(38*scale,430*scale),((320+shift)*scale,42*scale),(520*scale,430*scale)],fill=_rgb(palette[1]))
        _line(draw,[(250,430),(540,70),(865,430)],fill=_rgb(palette[2]),width=24,scale=scale)
    for index in range(34):
        speck_x=(seed[index%len(seed)]*19+index*79)%width
        speck_y=(seed[-(index%len(seed))-1]*13+index*41)%height
        draw.point((speck_x*scale,speck_y*scale),fill=_rgb(palette[2]))
    return _finish(image, size)


def _texture(output: Path, palette: list[str], motif: str) -> None:
    image = Image.new("RGB", (1080, 420), _rgb(palette[0]))
    draw = ImageDraw.Draw(image)
    seed = hashlib.sha256(motif.encode("utf-8")).digest()
    for index in range(140):
        x = (seed[index % len(seed)] * 17 + index * 83) % 1080
        y = (seed[-(index % len(seed)) - 1] * 11 + index * 47) % 420
        radius = 1 + index % 3
        draw.ellipse((x, y, x + radius, y + radius), fill=_rgb(palette[1] if index % 5 else palette[2]))
    image.save(output, "PNG", optimize=True)


def _component(topic: str, motif: str, palette: list[str]) -> str:
    safe_topic = html.escape(topic[:42])
    labels = {"signal-lens": "观察信号", "system-pulse": "系统脉冲", "kinetic-cutouts": "动势拼片", "human-trace": "人物轨迹", "field-notes": "现场切片", "concept-prism": "概念折射"}
    label = labels.get(motif, "原创视觉")
    return f'<section data-component="semantic-callout" style="margin:30px 0;padding:0;background-color:{palette[0]};border:1px solid {palette[2]};"><table style="width:100%;border-collapse:collapse;" role="presentation"><tbody><tr><td style="width:22%;padding:18px 10px;text-align:center;background-color:{palette[1]};color:{palette[0]};font-size:12px;font-weight:700;line-height:1.4;">{html.escape(label)}</td><td style="padding:18px 16px;color:{palette[2]};font-size:16px;font-weight:700;line-height:1.55;">{safe_topic}</td></tr></tbody></table></section>\n'


def create_asset_set(topic: str, output: Path, *, palette: list[str] | None = None) -> dict[str, Any]:
    colors = list(palette or ["#EEF4F1", "#315F58", "#D17A52"])
    while len(colors) < 3:
        colors.append("#D17A52")
    colors = [_hex(colors[0], "#EEF4F1"), _hex(colors[1], "#315F58"), _hex(colors[2], "#D17A52")]
    motif = derive_motif(topic)
    output.mkdir(parents=True, exist_ok=True)
    svg_path = output / "motion-source.svg"
    gif_path = output / "motion-wechat.gif"
    poster_path = output / "motion-poster.png"
    hero_path = output / "hero-wechat.png"
    cover_path = output / "cover-wechat.png"
    texture_path = output / "texture-wechat.png"
    component_path = output / "component.html"
    write_text(svg_path, _source_svg(motif, colors) + "\n")
    frames = [_draw_frame((900, 500), motif, colors, index, 16) for index in range(16)]
    gif_frames = [frame.quantize(colors=64, method=Image.Quantize.MEDIANCUT) for frame in frames]
    gif_frames[0].save(gif_path, "GIF", save_all=True, append_images=gif_frames[1:], duration=120, loop=0, optimize=True, disposal=2)
    frames[0].save(poster_path, "PNG", optimize=True)
    frames[0].save(hero_path, "PNG", optimize=True)
    frames[0].crop((0, 58, 900, 441)).save(cover_path, "PNG", optimize=True)
    _texture(texture_path, colors, motif)
    write_text(component_path, _component(topic, motif, colors))
    assets = [
        {"id": "motion-source", "role": "source", "local_path": svg_path.name, "provider": "original", "license": "Original asset", "wechat_ready": False, "fallback": gif_path.name},
        {"id": "hero-wechat", "role": "hero", "local_path": hero_path.name, "provider": "original", "license": "Original asset", "wechat_ready": True},
        {"id": "cover-wechat", "role": "cover", "local_path": cover_path.name, "provider": "original", "license": "Original asset", "wechat_ready": True},
        {"id": "motion-wechat", "role": "ornament", "local_path": gif_path.name, "provider": "original", "license": "Original asset", "wechat_ready": True, "fallback": poster_path.name},
        {"id": "texture-wechat", "role": "texture", "local_path": texture_path.name, "provider": "original", "license": "Original asset", "wechat_ready": True},
        {"id": "component", "role": "component", "local_path": component_path.name, "provider": "original", "license": "Original asset", "wechat_ready": True},
    ]
    return {"schema_version": "2.0", "created_at": now_iso(), "topic": topic, "motif": motif, "palette": colors, "art_direction": {"concept": motif, "original": True, "text_in_image": False, "wechat_fallbacks": True}, "editable_svg": svg_path.name, "wechat_gif": gif_path.name, "static_poster": poster_path.name, "hero": hero_path.name, "cover": cover_path.name, "texture": texture_path.name, "component": component_path.name, "assets": assets}


def main() -> int:
    parser = argparse.ArgumentParser(description="根据文章语义原创SVG、GIF、背景纹理和微信安全组件")
    parser.add_argument("topic")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--palette", nargs=3)
    parser.add_argument("--manifest", type=Path, help="可选：把微信可用资产登记到article-package.json")
    args = parser.parse_args()
    result = create_asset_set(args.topic, args.output_dir, palette=args.palette)
    write_json(args.output_dir / "asset-set.json", result)
    if args.manifest:
        manifest = read_json(args.manifest)
        existing = {item.get("id"): item for item in manifest.get("assets", [])}
        for item in result["assets"]:
            if item.get("wechat_ready") and item["local_path"].lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                entry = {**item, "local_path": str(Path("assets") / item["local_path"]).replace("\\", "/"), "creator": "asset_factory.py", "source_url": "", "license_url": "", "credit": "original programmatic asset", "accessed_at": now_iso(), "modifications": f"generated motif {result['motif']}", "wechat_url": ""}
                existing[entry["id"]] = entry
        manifest["assets"] = list(existing.values())
        write_json(args.manifest, manifest)
    print(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
