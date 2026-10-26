# Preserved local sample workflow; private inputs excluded. See README.md.
from __future__ import annotations
import sys as _sample_sys
from pathlib import Path as _SamplePath
_sample_sys.path.insert(0,str(_SamplePath(__file__).resolve().parent))
from sample_runtime import sample
sample.configure()
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
ROOT = sample.workspace() / 'inputs/photos'
OUT = sample.workspace() / 'outputs/article'
ASSETS = OUT / 'assets'
ASSETS.mkdir(parents=True, exist_ok=True)
FONT_REGULAR = sample.input_path('input_0003')
FONT_BOLD = sample.input_path('input_0007')
INK = '#183B56'
GREEN = '#2EAD72'
RED = '#D94135'
PAPER = '#F7F2E8'

def font(size: int, bold: bool=False) -> ImageFont.FreeTypeFont:
    return sample.font(size)

def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip('#')
    return tuple((int(value[i:i + 2], 16) for i in (0, 2, 4)))

def crop_to_ratio(image: Image.Image, ratio: float, anchor: tuple[float, float]=(0.5, 0.5)) -> Image.Image:
    width, height = image.size
    current = width / height
    if current > ratio:
        crop_width = int(height * ratio)
        left = int((width - crop_width) * anchor[0])
        left = max(0, min(left, width - crop_width))
        box = (left, 0, left + crop_width, height)
    else:
        crop_height = int(width / ratio)
        top = int((height - crop_height) * anchor[1])
        top = max(0, min(top, height - crop_height))
        box = (0, top, width, top + crop_height)
    return image.crop(box)

def process_photo(source: Path, target: Path, size: tuple[int, int], anchor: tuple[float, float]=(0.5, 0.5), pre_crop: tuple[float, float, float, float] | None=None) -> None:
    with Image.open(source) as raw:
        image = ImageOps.exif_transpose(raw).convert('RGB')
        if pre_crop:
            width, height = image.size
            image = image.crop((int(width * pre_crop[0]), int(height * pre_crop[1]), int(width * pre_crop[2]), int(height * pre_crop[3])))
        image = crop_to_ratio(image, size[0] / size[1], anchor)
        image = image.resize(size, Image.Resampling.LANCZOS)
        image.save(target, 'JPEG', quality=84, optimize=True, progressive=True)
PHOTOS = sample.photo_records()

def make_cover() -> None:
    source = ROOT / 'group-1' / 'asset_0008.jpg'
    with Image.open(source) as raw:
        image = ImageOps.exif_transpose(raw).convert('RGB')
        image = crop_to_ratio(image, 900 / 383, (0.55, 0.48)).resize((900, 383), Image.Resampling.LANCZOS)
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for x in range(560):
        alpha = int(205 * (1 - x / 560) ** 1.4)
        od.line((x, 0, x, 383), fill=(*hex_rgb(INK), alpha))
    od.rectangle((0, 0, 12, 383), fill=(*hex_rgb(RED), 255))
    od.rounded_rectangle((44, 34, 260, 69), radius=16, fill=(255, 255, 255, 232))
    od.text((61, 40), '2026 field_0009', font=font(18, True), fill=hex_rgb(RED))
    od.text((45, 98), 'field_0010', font=font(54, True), fill=(255, 255, 255))
    od.text((45, 164), 'field_0011', font=font(54, True), fill=(255, 255, 255))
    od.line((47, 240, 302, 240), fill=(*hex_rgb(GREEN), 255), width=5)
    od.text((45, 260), '“field_0012”field_0013', font=font(22, True), fill=(255, 255, 255))
    od.text((45, 298), 'field_0014', font=font(22), fill=(245, 247, 244))
    output = Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')
    output.save(ASSETS / 'asset_0015.jpg', 'JPEG', quality=91, optimize=True, progressive=True)

def petal_points(cx: float, cy: float, angle: float, length: float, width: float) -> list[tuple[float, float]]:
    points = []
    for i in range(37):
        t = i / 36 * math.tau
        x = math.cos(t) * width * (0.52 + 0.48 * math.sin(t / 2) ** 2)
        y = -length * 0.48 + math.sin(t) * length * 0.5
        ca, sa = (math.cos(angle), math.sin(angle))
        points.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return points

def make_bloom_frame(active: int) -> Image.Image:
    canvas = Image.new('RGB', (900, 500), hex_rgb(PAPER))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((30, 26, 870, 474), radius=34, fill=(255, 255, 255), outline=(222, 230, 222), width=2)
    draw.text((58, 47), 'field_0016，field_0017', font=font(34, True), fill=hex_rgb(INK))
    draw.text((60, 97), 'field_0018 · field_0019 · field_0020 · field_0021 · field_0022', font=font(19), fill=(91, 113, 115))
    cx, cy = (450, 302)
    labels = ['01 field_0018', '02 field_0019', '03 field_0020', '04 field_0021', '05 field_0022']
    colors = [INK, GREEN, RED, GREEN, INK]
    label_positions: list[tuple[float, float, int, str]] = []
    for i in range(5):
        angle = math.radians(-90 + i * 72)
        points = petal_points(cx, cy, angle, 128, 72)
        color = colors[i] if i < active else '#D9E1DD'
        draw.polygon(points, fill=hex_rgb(color), outline=(255, 255, 255))
        label_angle = angle - math.pi / 2
        tx = cx + math.cos(label_angle) * 82
        ty = cy + math.sin(label_angle) * 82
        label_positions.append((tx, ty, i, color))
    for tx, ty, i, color in label_positions:
        bbox = draw.textbbox((0, 0), labels[i], font=font(15, True))
        draw.text((tx - (bbox[2] - bbox[0]) / 2, ty - (bbox[3] - bbox[1]) / 2), labels[i], font=font(15, True), fill=(255, 255, 255) if i < active else (112, 127, 123))
    draw.ellipse((386, 238, 514, 366), fill=(255, 250, 239), outline=hex_rgb(RED), width=5)
    center_text = 'field_0023\nfield_0024'
    draw.multiline_text((450, 302), center_text, font=font(23, True), fill=hex_rgb(RED), anchor='mm', align='center', spacing=2)
    draw.text((450, 438), 'field_0025，field_0026', font=font(18, True), fill=hex_rgb(INK), anchor='mm')
    return canvas

def make_bloom_assets() -> None:
    poster = make_bloom_frame(5)
    poster.save(ASSETS / 'asset_0027.png', optimize=True)
    frames: list[Image.Image] = []
    for active in range(0, 6):
        frame = make_bloom_frame(active)
        frames.extend([frame] * (4 if active in {0, 5} else 2))
    frames[0].save(ASSETS / 'asset_0028.gif', save_all=True, append_images=frames[1:], duration=180, loop=0, optimize=True, disposal=2)

def make_brand_strip() -> None:
    school_path = ROOT / 'asset_0029.png'
    team_path = ROOT / 'asset_0030.png'
    canvas = Image.new('RGB', (900, 180), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((20, 20, 880, 160), radius=28, fill=hex_rgb(PAPER), outline=(221, 227, 220), width=2)
    with Image.open(school_path) as raw:
        school = ImageOps.contain(ImageOps.exif_transpose(raw).convert('RGBA'), (110, 110), Image.Resampling.LANCZOS)
    with Image.open(team_path) as raw:
        team = ImageOps.contain(ImageOps.exif_transpose(raw).convert('RGBA'), (112, 112), Image.Resampling.LANCZOS)
    canvas.paste(school, (54, 35), school)
    canvas.paste(team, (731, 34), team)
    draw.text((182, 50), 'field_0031', font=font(27, True), fill=hex_rgb(INK))
    draw.text((182, 94), '“field_0012”field_0013', font=font(23, True), fill=hex_rgb(RED))
    draw.line((183, 132, 696, 132), fill=hex_rgb(GREEN), width=4)
    canvas.save(ASSETS / 'asset_0032.png', optimize=True)

def main() -> None:
    for item in PHOTOS:
        process_photo(item['source'], ASSETS / item['file'], item['size'], item['anchor'], item.get('pre_crop'))
    make_cover()
    make_bloom_assets()
    make_brand_strip()
    manifest = {'photos': [{'id': item['id'], 'source': str(item['source']), 'local_path': f'assets/{item['file']}', 'alt': item['alt'], 'section': item['section'], 'license': 'field_0033；field_0034', 'modifications': f'EXIFfield_0035、field_0036{item['size'][0]}×{item['size'][1]}field_0037'} for item in PHOTOS], 'original_assets': [{'id': 'cover-main', 'local_path': 'asset_0038.jpg', 'role': 'cover', 'license': 'Original layout derived from user-provided photo'}, {'id': 'five-petal-bloom', 'local_path': 'asset_0039.gif', 'role': 'illustration', 'license': 'Original programmatic asset', 'fallback': 'asset_0027.png'}, {'id': 'five-petal-bloom-poster', 'local_path': 'asset_0040.png', 'role': 'illustration', 'license': 'Original programmatic asset'}, {'id': 'brand-strip', 'local_path': 'asset_0041.png', 'role': 'ornament', 'license': 'Original layout derived from user-provided logos'}]}
    (OUT / 'asset-manifest-generated.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(ASSETS), 'photos': len(PHOTOS), 'originals': 4}, ensure_ascii=False))
if __name__ == '__main__':
    main()
